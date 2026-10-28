#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const defaultRegistry = path.resolve(
  scriptDir,
  "../references/workspace-skill-registry.json",
);

function fail(message) {
  console.error(`registry error: ${message}`);
  process.exit(1);
}

function expandHome(value) {
  if (value === "~") return os.homedir();
  if (value.startsWith("~/")) return path.join(os.homedir(), value.slice(2));
  return value;
}

function object(value, label, errors) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    errors.push(`${label} must be an object`);
    return {};
  }
  return value;
}

function validate(registry, registryPath, workspaceArg) {
  const errors = [];
  if (registry.schemaVersion !== 1) errors.push("schemaVersion must be 1");

  const authorization = object(registry.authorization, "authorization", errors);
  const owner = object(
    authorization.workspaceOwner,
    "authorization.workspaceOwner",
    errors,
  );
  const ownerPrincipal = owner.principal;
  if (ownerPrincipal !== "workspace-owner") {
    errors.push("workspace owner principal must be workspace-owner");
  }
  if (owner.resolve?.kind !== "openclaw-owner-authority") {
    errors.push("workspace owner must resolve through OpenClaw owner authority");
  }

  const defaults = object(
    authorization.defaults,
    "authorization.defaults",
    errors,
  );
  if (
    !Array.isArray(defaults.workspaceSkillEditors) ||
    !defaults.workspaceSkillEditors.includes(ownerPrincipal)
  ) {
    errors.push("default workspace editors must include only the workspace owner");
  } else if (defaults.workspaceSkillEditors.length !== 1) {
    errors.push("default workspace editors must remain singular");
  }
  for (const field of ["newSkillDestination", "autonomousSkillDestination"]) {
    if (defaults[field] !== "workshop") {
      errors.push(`authorization.defaults.${field} must be workshop`);
    }
  }

  const principals = object(
    authorization.principals,
    "authorization.principals",
    errors,
  );
  for (const [principal, entryValue] of Object.entries(principals)) {
    const entry = object(entryValue, `principal ${principal}`, errors);
    const kind = entry.resolve?.kind;
    if (!new Set(["host-injected-principal-id", "openclaw-profile-id"]).has(kind)) {
      errors.push(`principal ${principal} has an unsupported resolver`);
    }
    if (
      kind === "host-injected-principal-id" &&
      entry.resolve?.principalId !== principal
    ) {
      errors.push(`principal ${principal} must match its injected principalId`);
    }
    if (
      kind === "openclaw-profile-id" &&
      (typeof entry.resolve?.profileId !== "string" || !entry.resolve.profileId)
    ) {
      errors.push(`principal ${principal} requires a durable OpenClaw profileId`);
    }
  }
  const exceptions = object(
    authorization.skillEditorExceptions,
    "authorization.skillEditorExceptions",
    errors,
  );

  const authorizationText = JSON.stringify(authorization).toLowerCase();
  for (const prefix of [
    "telegram:",
    "discord:",
    "slack:",
    "imessage:",
    "sms:",
    "signal:",
    "whatsapp:",
  ]) {
    if (authorizationText.includes(prefix)) {
      errors.push(`authorization must not contain native channel identity ${prefix}`);
    }
  }

  const workspaceDir = workspaceArg
    ? path.resolve(workspaceArg)
    : path.resolve(path.dirname(registryPath), "../../..");
  const enforceCanonicalPaths = fs.existsSync(
    path.join(workspaceDir, "scripts", "publish-skillreef.sh"),
  );
  const validSkill = /^[a-z0-9][a-z0-9-]*$/u;
  for (const [skill, editors] of Object.entries(exceptions)) {
    if (!validSkill.test(skill) || skill === "*") {
      errors.push(`invalid exact skill grant: ${skill}`);
    }
    if (!Array.isArray(editors) || editors.length === 0) {
      errors.push(`editor exception ${skill} must be a nonempty array`);
      continue;
    }
    for (const principal of editors) {
      if (principal !== ownerPrincipal && !principals[principal]) {
        errors.push(`unknown principal ${principal} in ${skill}`);
      }
    }
    if (
      enforceCanonicalPaths &&
      !fs.existsSync(path.join(workspaceDir, "skills", skill, "SKILL.md"))
    ) {
      errors.push(`granted workspace skill does not exist: ${skill}`);
    }
  }

  const publication = object(registry.publication, "publication", errors);
  const skillreef = object(publication.skillreef, "publication.skillreef", errors);
  if (typeof skillreef.repository !== "string" || !skillreef.repository.includes("/")) {
    errors.push("publication.skillreef.repository must be an owner/repo slug");
  }
  if (typeof skillreef.checkout !== "string" || !skillreef.checkout.trim()) {
    errors.push("publication.skillreef.checkout is required");
  }
  const reefSkills = object(
    skillreef.skills,
    "publication.skillreef.skills",
    errors,
  );
  const mirrorNames = new Set();
  for (const [skill, entryValue] of Object.entries(reefSkills)) {
    const entry = object(entryValue, `publication skill ${skill}`, errors);
    if (!validSkill.test(skill)) errors.push(`invalid publication skill: ${skill}`);
    if (!validSkill.test(entry.mirror ?? "")) {
      errors.push(`invalid SkillReef mirror for ${skill}`);
    } else if (mirrorNames.has(entry.mirror)) {
      errors.push(`duplicate SkillReef mirror: ${entry.mirror}`);
    } else {
      mirrorNames.add(entry.mirror);
    }
    if (!new Set(["workspace", "workshop"]).has(entry.source)) {
      errors.push(`publication source for ${skill} must be workspace or workshop`);
    }
    if (
      enforceCanonicalPaths &&
      entry.source === "workspace" &&
      !fs.existsSync(path.join(workspaceDir, "skills", skill, "SKILL.md"))
    ) {
      errors.push(`published workspace skill does not exist: ${skill}`);
    }
  }

  const standalone = object(
    publication.standalone,
    "publication.standalone",
    errors,
  );
  if (typeof standalone.checkoutRoot !== "string" || !standalone.checkoutRoot.trim()) {
    errors.push("publication.standalone.checkoutRoot is required");
  }
  const standaloneSkills = object(
    standalone.skills,
    "publication.standalone.skills",
    errors,
  );
  for (const [skill, entryValue] of Object.entries(standaloneSkills)) {
    const entry = object(entryValue, `standalone skill ${skill}`, errors);
    if (!reefSkills[skill]) {
      errors.push(`standalone skill is missing its SkillReef source: ${skill}`);
    }
    if (!validSkill.test(entry.directory ?? "")) {
      errors.push(`invalid standalone checkout directory for ${skill}`);
    }
    if (typeof entry.repository !== "string" || !entry.repository.includes("/")) {
      errors.push(`standalone repository for ${skill} must be an owner/repo slug`);
    }
  }

  if (errors.length) fail(errors.join("\n"));
  return { authorization, publication, workspaceDir };
}

const args = process.argv.slice(2);
const action = args.shift() ?? "validate";
const registryArg = args.shift() ?? defaultRegistry;
let workspaceArg;
let principalArg;
let skillArg;
if (action === "authorize") {
  principalArg = args.shift();
  skillArg = args.shift();
  workspaceArg = args.shift();
} else {
  workspaceArg = args.shift();
}
const registryPath = path.resolve(registryArg);
let registry;
try {
  registry = JSON.parse(fs.readFileSync(registryPath, "utf8"));
} catch (error) {
  fail(`cannot read ${registryPath}: ${error.message}`);
}
const validated = validate(registry, registryPath, workspaceArg);

switch (action) {
  case "validate":
    console.log(`valid workspace skill registry: ${registryPath}`);
    break;
  case "skillreef-pairs":
    for (const [skill, entry] of Object.entries(
      validated.publication.skillreef.skills,
    ).sort(([a], [b]) => a.localeCompare(b))) {
      console.log(`${skill}:${entry.mirror}:${entry.source}`);
    }
    break;
  case "standalone-pairs":
    for (const [skill, entry] of Object.entries(
      validated.publication.standalone.skills,
    ).sort(([a], [b]) => a.localeCompare(b))) {
      console.log(`${skill}:${entry.directory}`);
    }
    break;
  case "skillreef-checkout":
    console.log(expandHome(validated.publication.skillreef.checkout));
    break;
  case "standalone-root":
    console.log(expandHome(validated.publication.standalone.checkoutRoot));
    break;
  case "authorize": {
    if (!principalArg || !skillArg) {
      fail("authorize requires <principal> <skill> after the registry path");
    }
    const owner = validated.authorization.workspaceOwner.principal;
    const editors =
      validated.authorization.skillEditorExceptions[skillArg] ?? [];
    const allowed = principalArg === owner || editors.includes(principalArg);
    console.log(
      JSON.stringify({
        allowed,
        principal: principalArg,
        skill: skillArg,
        reason:
          principalArg === owner
            ? "workspace-owner"
            : allowed
              ? "exact-editor-exception"
              : "no-exact-grant",
      }),
    );
    if (!allowed) process.exitCode = 3;
    break;
  }
  default:
    fail(`unknown action: ${action}`);
}
