#!/usr/bin/env node
// Auth Molt v0.1 lightweight tests — no external deps
// Tests arg validation, profile validation, and dry-run using AUTH_MOLT_STORE_PATH env override.
// Force-refresh success (claw3-style) and failure with rollback (claw4-style) are manual-only
// because they require the live OpenClaw runtime and credential store.
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

const SCRIPT = new URL('./moltmaster.mjs', import.meta.url).pathname;

const VALID_STORE = {
  profiles: {
    'openai-codex:valid@edge.app': {
      provider: 'openai-codex', type: 'oauth', email: 'valid@edge.app', expires: 9999999999999,
    },
    'openai-codex:you@example.com': {
      provider: 'openai-codex', type: 'oauth', email: 'you@example.com', expires: 9999999999999,
    },
  },
};

const MIXED_STORE = {
  profiles: {
    'openai-codex:valid@edge.app': {
      provider: 'openai-codex', type: 'oauth', email: 'valid@edge.app', expires: 9999999999999,
    },
    'openai-codex:badprovider@edge.app': {
      provider: 'anthropic', type: 'oauth', email: 'badprovider@edge.app', expires: 9999999999999,
    },
    'openai-codex:badtype@edge.app': {
      provider: 'openai-codex', type: 'apikey', email: 'badtype@edge.app', expires: 9999999999999,
    },
    'openai-codex:bademail@edge.app': {
      provider: 'openai-codex', type: 'oauth', email: 'bademail@notedge.com', expires: 9999999999999,
    },
  },
};

// ─── Test runner ─────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function run(label, args, { storePath, backupDir, stateFile, expectExit = 0, expectStdout = [], expectStderr = [] } = {}) {
  const env = { ...process.env };
  if (storePath) env.AUTH_MOLT_STORE_PATH = storePath;
  if (backupDir) env.AUTH_MOLT_BACKUP_DIR = backupDir;
  if (stateFile) env.AUTH_MOLT_STATE_FILE = stateFile;

  const result = spawnSync(process.execPath, [SCRIPT, ...args], {
    env,
    encoding: 'utf8',
    timeout: 10_000,
  });

  const stdout = result.stdout ?? '';
  const stderr = result.stderr ?? '';
  const exitCode = result.status ?? 1;

  const checks = [];
  if (exitCode !== expectExit) checks.push(`exit ${exitCode} != expected ${expectExit}`);
  for (const s of expectStdout) {
    if (!stdout.includes(s)) checks.push(`stdout missing: ${JSON.stringify(s)}`);
  }
  for (const s of expectStderr) {
    if (!stderr.includes(s) && !stdout.includes(s)) checks.push(`stderr missing: ${JSON.stringify(s)}`);
  }

  if (checks.length === 0) {
    console.log(`  PASS  ${label}`);
    passed++;
  } else {
    console.log(`  FAIL  ${label}`);
    for (const c of checks) console.log(`        ${c}`);
    if (stdout) console.log(`        stdout: ${stdout.slice(0, 300)}`);
    if (stderr) console.log(`        stderr: ${stderr.slice(0, 300)}`);
    failed++;
  }
}

// ─── Temp store setup ─────────────────────────────────────────────────────────

const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'auth-molt-test-'));
const validStorePath = path.join(tmpDir, 'valid-store.json');
const mixedStorePath = path.join(tmpDir, 'mixed-store.json');
const backupDir = path.join(tmpDir, 'backups');
const stateFile = path.join(tmpDir, 'refresh-state.json');
fs.writeFileSync(validStorePath, JSON.stringify(VALID_STORE, null, 2));
fs.writeFileSync(mixedStorePath, JSON.stringify(MIXED_STORE, null, 2));

function testEnv(opts = {}) {
  return { backupDir, stateFile, ...opts };
}

// ─── Tests ────────────────────────────────────────────────────────────────────

console.log('\nAuth Molt v0.1 — unit tests\n');

// --- Dry-run ---
console.log('Dry-run:');
run('dry-run lists profile and exits 0', ['--dry-run'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 0,
  expectStdout: ['dry-run', 'valid@edge.app', 'Dry-run: no files changed'],
});
run('no-flag defaults to dry-run', [], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 0,
  expectStdout: ['dry-run', 'Dry-run: no files changed'],
});
run('dry-run with --profile filters to target', ['--dry-run', '--profile', 'openai-codex:valid@edge.app'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 0,
  expectStdout: ['valid@edge.app'],
});
run('dry-run allows approved Pearson Codex profile', ['--dry-run', '--profile', 'openai-codex:you@example.com'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 0,
  expectStdout: ['you@example.com'],
});

// --- Flag refusals ---
console.log('\nFlag refusals:');
run('--execute + --dry-run refused', ['--execute', '--dry-run'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['ambiguous mode'],
});
run('--execute + --all + --profile refused', ['--execute', '--all', '--profile', 'openai-codex:valid@edge.app'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['ambiguous target'],
});
run('--force-expired-for-refresh without --execute refused', ['--force-expired-for-refresh', '--profile', 'openai-codex:valid@edge.app'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['requires --execute'],
});
run('--force-expired-for-refresh + --all refused', ['--execute', '--force-expired-for-refresh', '--all'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['refuses --all'],
});
run('--force-expired-for-refresh without --profile refused', ['--execute', '--force-expired-for-refresh'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['exactly one --profile'],
});
run('--force-expired-for-refresh with two --profile refused', [
  '--execute', '--force-expired-for-refresh',
  '--profile', 'openai-codex:valid@edge.app',
  '--profile', 'openai-codex:valid@edge.app',
], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['exactly one --profile'],
});
run('--prune-backups without --older-than refused', ['--prune-backups'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['requires --older-than'],
});
run('bare --execute without --profile or --all refused', ['--execute'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['exactly one --profile'],
});

// --- Profile validation ---
console.log('\nProfile validation:');
run('non-Codex provider rejected', ['--dry-run', '--profile', 'openai-codex:badprovider@edge.app'], {
  storePath: mixedStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['non-Codex provider'],
});
run('non-OAuth type rejected', ['--dry-run', '--profile', 'openai-codex:badtype@edge.app'], {
  storePath: mixedStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['non-OAuth profile'],
});
run('non-edge.app email rejected', ['--dry-run', '--profile', 'openai-codex:bademail@edge.app'], {
  storePath: mixedStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['unexpected email'],
});
run('non-allowlisted profile ID rejected', ['--dry-run', '--profile', 'anthropic:badid'], {
  storePath: mixedStorePath,
  ...testEnv(),
  expectExit: 1,
  expectStderr: ['non-allowlisted profile id'],
});

// --- Prune dry-run ---
console.log('\nPrune:');
run('prune dry-run with no backups exits 0', ['--prune-backups', '--older-than', '1'], {
  storePath: validStorePath,
  ...testEnv(),
  expectExit: 0,
});

// ─── Cleanup ──────────────────────────────────────────────────────────────────

fs.rmSync(tmpDir, { recursive: true, force: true });

// ─── Summary ──────────────────────────────────────────────────────────────────

console.log(`\n${passed + failed} tests: ${passed} passed, ${failed} failed`);
if (failed > 0) {
  console.error('\nSome tests failed.');
  process.exit(1);
}
console.log('All tests passed.');
