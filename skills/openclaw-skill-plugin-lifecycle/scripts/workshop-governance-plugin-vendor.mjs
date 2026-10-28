#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const pluginId = "workshop-governance-context";
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const skillDir = path.resolve(scriptDir, "..");
const workspaceDir = path.resolve(skillDir, "../..");
const registryPath = path.join(
  skillDir,
  "references",
  "workspace-skill-registry.json",
);

function fail(message) {
  console.error(`vendor error: ${message}`);
  process.exit(1);
}

function expandHome(value) {
  if (value === "~") return os.homedir();
  if (value.startsWith("~/")) return path.join(os.homedir(), value.slice(2));
  return value;
}

function workspacePath(value, label) {
  const absolute = path.resolve(workspaceDir, value);
  const relative = path.relative(workspaceDir, absolute);
  if (
    !value ||
    path.isAbsolute(value) ||
    relative === ".." ||
    relative.startsWith(`..${path.sep}`)
  ) {
    fail(`${label} must stay inside the workspace`);
  }
  return absolute;
}

function git(sourceDir, ...args) {
  return execFileSync("git", ["-C", sourceDir, ...args], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
}

function ignored(relativePath) {
  const parts = relativePath.split(path.sep);
  const name = parts.at(-1);
  return (
    parts.includes(".git") ||
    parts.includes("node_modules") ||
    name === ".DS_Store" ||
    name.endsWith(".tgz")
  );
}

async function snapshot(rootDir, allowMissing = false) {
  const files = new Map();

  async function visit(relativeDir) {
    const absoluteDir = path.join(rootDir, relativeDir);
    let entries;
    try {
      entries = await fs.readdir(absoluteDir, { withFileTypes: true });
    } catch (error) {
      if (allowMissing && error?.code === "ENOENT" && !relativeDir) return;
      throw error;
    }
    for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
      const relativePath = path.join(relativeDir, entry.name);
      if (ignored(relativePath)) continue;
      const absolutePath = path.join(rootDir, relativePath);
      if (entry.isSymbolicLink()) {
        fail(`symlinks are not allowed in the vendored plugin: ${relativePath}`);
      }
      if (entry.isDirectory()) {
        await visit(relativePath);
        continue;
      }
      if (!entry.isFile()) continue;
      const content = await fs.readFile(absolutePath);
      const stat = await fs.stat(absolutePath);
      files.set(relativePath, {
        hash: crypto.createHash("sha256").update(content).digest("hex"),
        mode: stat.mode & 0o777,
      });
    }
  }

  await visit("");
  return files;
}

function treeHash(files) {
  const hash = crypto.createHash("sha256");
  for (const [relativePath, entry] of [...files.entries()].sort(([a], [b]) =>
    a.localeCompare(b),
  )) {
    hash.update(relativePath.replaceAll(path.sep, "/"));
    hash.update("\0");
    hash.update(entry.hash);
    hash.update("\0");
  }
  return hash.digest("hex");
}

function compare(source, vendor) {
  const drift = [];
  for (const [relativePath, sourceEntry] of source) {
    const vendorEntry = vendor.get(relativePath);
    if (!vendorEntry) drift.push(`missing: ${relativePath}`);
    else if (vendorEntry.hash !== sourceEntry.hash) {
      drift.push(`changed: ${relativePath}`);
    } else if (vendorEntry.mode !== sourceEntry.mode) {
      drift.push(`mode: ${relativePath}`);
    }
  }
  for (const relativePath of vendor.keys()) {
    if (!source.has(relativePath)) drift.push(`extra: ${relativePath}`);
  }
  return drift.sort();
}

async function readJson(filePath, label) {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch (error) {
    fail(`cannot read ${label} at ${filePath}: ${error.message}`);
  }
}

async function loadLayout(sourceOverride) {
  const registry = await readJson(registryPath, "workspace skill registry");
  const entry = registry.publication?.plugins?.[pluginId];
  if (!entry) fail(`registry has no publication.plugins.${pluginId} entry`);
  const sourceDir = path.resolve(
    expandHome(sourceOverride ?? entry.checkout ?? ""),
  );
  const vendorDir = workspacePath(entry.vendor, "plugin vendor path");
  const lockPath = workspacePath(entry.lock, "plugin lock path");
  const assetsDir = path.join(skillDir, "assets");
  const relativeVendor = path.relative(assetsDir, vendorDir);
  if (
    !relativeVendor ||
    relativeVendor === ".." ||
    relativeVendor.startsWith(`..${path.sep}`)
  ) {
    fail("plugin vendor path must be below this skill's assets directory");
  }
  if (sourceDir === vendorDir) fail("upstream and vendor paths must differ");
  return { entry, sourceDir, vendorDir, lockPath };
}

async function validatePluginTree(rootDir) {
  const manifest = await readJson(
    path.join(rootDir, "openclaw.plugin.json"),
    "plugin manifest",
  );
  const packageJson = await readJson(
    path.join(rootDir, "package.json"),
    "plugin package",
  );
  if (manifest.id !== pluginId) {
    fail(`expected plugin id ${pluginId}, found ${String(manifest.id)}`);
  }
  if (!manifest.version || manifest.version !== packageJson.version) {
    fail("plugin manifest and package versions must match");
  }
  return { manifest, packageJson };
}

async function verifyVendor(layout) {
  const { manifest } = await validatePluginTree(layout.vendorDir);
  const files = await snapshot(layout.vendorDir);
  const lock = await readJson(layout.lockPath, "plugin vendor lock");
  const hash = treeHash(files);
  const expected = {
    schemaVersion: 1,
    pluginId,
    repository: layout.entry.repository,
    version: manifest.version,
    vendoredPath: layout.entry.vendor,
    treeSha256: hash,
    fileCount: files.size,
  };
  for (const [field, value] of Object.entries(expected)) {
    if (lock[field] !== value) {
      fail(`vendor lock ${field} mismatch: expected ${value}, found ${lock[field]}`);
    }
  }
  if (typeof lock.upstreamCommit !== "string" || !/^[0-9a-f]{40}$/u.test(lock.upstreamCommit)) {
    fail("vendor lock requires a full upstreamCommit");
  }
  return { files, hash, lock, manifest };
}

async function checkUpstream(layout) {
  const topLevel = path.resolve(git(layout.sourceDir, "rev-parse", "--show-toplevel"));
  if (topLevel !== layout.sourceDir) {
    fail(`plugin checkout must be its Git root: ${layout.sourceDir}`);
  }
  const status = git(layout.sourceDir, "status", "--porcelain", "--untracked-files=all");
  if (status) fail("plugin checkout must be clean before vendoring");
  const origin = git(layout.sourceDir, "config", "--get", "remote.origin.url");
  if (!origin.includes(layout.entry.repository)) {
    fail(`plugin checkout origin does not match ${layout.entry.repository}`);
  }
  const commit = git(layout.sourceDir, "rev-parse", "HEAD");
  const sourcePlugin = await validatePluginTree(layout.sourceDir);
  const sourceFiles = await snapshot(layout.sourceDir);
  return { commit, sourceFiles, sourcePlugin };
}

async function check(layout) {
  const upstream = await checkUpstream(layout);
  const vendor = await verifyVendor(layout);
  const drift = compare(upstream.sourceFiles, vendor.files);
  if (drift.length) fail(`vendored plugin drift:\n${drift.join("\n")}`);
  if (vendor.lock.upstreamCommit !== upstream.commit) {
    fail(
      `vendor lock commit mismatch: expected ${upstream.commit}, found ${vendor.lock.upstreamCommit}`,
    );
  }
  if (upstream.sourcePlugin.manifest.version !== vendor.manifest.version) {
    fail("upstream and vendored plugin versions differ");
  }
  console.log(
    `vendor matches ${layout.entry.repository}@${upstream.commit} (${vendor.hash})`,
  );
}

async function sync(layout) {
  const upstream = await checkUpstream(layout);
  await fs.rm(layout.vendorDir, { recursive: true, force: true });
  await fs.mkdir(layout.vendorDir, { recursive: true });
  for (const [relativePath, entry] of upstream.sourceFiles) {
    const sourcePath = path.join(layout.sourceDir, relativePath);
    const vendorPath = path.join(layout.vendorDir, relativePath);
    await fs.mkdir(path.dirname(vendorPath), { recursive: true });
    await fs.copyFile(sourcePath, vendorPath);
    await fs.chmod(vendorPath, entry.mode);
  }
  const vendorFiles = await snapshot(layout.vendorDir);
  const lock = {
    schemaVersion: 1,
    pluginId,
    repository: layout.entry.repository,
    upstreamCommit: upstream.commit,
    version: upstream.sourcePlugin.manifest.version,
    vendoredPath: layout.entry.vendor,
    treeSha256: treeHash(vendorFiles),
    fileCount: vendorFiles.size,
  };
  await fs.mkdir(path.dirname(layout.lockPath), { recursive: true });
  await fs.writeFile(layout.lockPath, `${JSON.stringify(lock, null, 2)}\n`);
  await check(layout);
}

const [action = "verify", sourceOverride] = process.argv.slice(2);
const layout = await loadLayout(sourceOverride);

switch (action) {
  case "verify": {
    const result = await verifyVendor(layout);
    console.log(`valid vendored plugin: ${result.hash}`);
    break;
  }
  case "check":
    await check(layout);
    break;
  case "sync":
    await sync(layout);
    break;
  default:
    fail("usage: workshop-governance-plugin-vendor.mjs [verify|check|sync] [upstream-checkout]");
}
