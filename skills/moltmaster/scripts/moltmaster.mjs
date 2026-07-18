#!/usr/bin/env node
// Auth Molt v0.1 — Codex OAuth refresh utility (OpenClaw-adjacent CLI)
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

const __dirname = path.dirname(new URL(import.meta.url).pathname);

function resolveSdkPath() {
  const sdkSuffix = 'openclaw/dist/plugin-sdk/agent-runtime.js';
  const candidates = [
    process.env.AUTH_MOLT_SDK_PATH,
    process.env.MOLTMASTER_SDK_PATH,
    process.env.HOMEBREW_PREFIX ? path.join(process.env.HOMEBREW_PREFIX, 'lib', 'node_modules', sdkSuffix) : null,
    '/opt/homebrew/lib/node_modules/openclaw/dist/plugin-sdk/agent-runtime.js',
    '/usr/local/lib/node_modules/openclaw/dist/plugin-sdk/agent-runtime.js',
    '/usr/lib/node_modules/openclaw/dist/plugin-sdk/agent-runtime.js',
  ].filter(Boolean);

  return candidates.find((candidate) => fs.existsSync(candidate)) ?? candidates[0];
}

const SDK_PATH = resolveSdkPath();
const DEFAULT_STORE_PATH = path.join(os.homedir(), '.openclaw', 'agents', 'main', 'agent', 'auth-profiles.json');
const STORE_PATH = process.env.AUTH_MOLT_STORE_PATH ?? DEFAULT_STORE_PATH;
const SKILL_DIR = path.resolve(__dirname, '..');
const BACKUP_DIR = process.env.AUTH_MOLT_BACKUP_DIR ?? path.join(SKILL_DIR, 'backups');
const STATE_FILE = process.env.AUTH_MOLT_STATE_FILE ?? path.join(SKILL_DIR, '.refresh-state.json');
const CODEX_PROFILE_ALLOWLIST = [
  /^openai-codex:[^/\s]+@edge\.app$/,
  /^openai-codex:pearson\.jaredb@gmail\.com$/,
  /^openai-codex:you@example\.com$/,
];
const CODEX_EMAIL_ALLOWLIST = [
  /@edge\.app$/,
  /^pearson\.jaredb@gmail\.com$/,
  /^you@example\.com$/,
];
const WARN_WITHIN_MS = 14 * 24 * 60 * 60 * 1000;
const COOLDOWN_MS = 60_000;

// ─── Utilities ───────────────────────────────────────────────────────────────

function usage() {
  console.log(`
Auth Molt v0.1 — Codex OAuth refresh utility (OpenClaw-adjacent CLI)

Usage:
  node scripts/moltmaster.mjs --dry-run [--profile <id>]
  node scripts/moltmaster.mjs --execute --profile <id>
  node scripts/moltmaster.mjs --execute --all
  node scripts/moltmaster.mjs --execute --force-expired-for-refresh --profile <id>
  node scripts/moltmaster.mjs --prune-backups --older-than <days>
  node scripts/moltmaster.mjs --prune-backups --older-than <days> --execute

Flags:
  --dry-run                      List targets without mutating anything (default)
  --execute                      Required for any mutation
  --profile <id>                 Target a single profile (repeatable)
  --all                          Target all Codex OAuth profiles
  --force-expired-for-refresh    Temporarily fake expiry to force refresh for a usable-but-expiring profile
  --prune-backups                List or delete old backup files
  --older-than <days>            Threshold in days (required with --prune-backups)

Safety:
  - Dry-run unless --execute is present
  - --force-expired-for-refresh requires --execute + exactly one --profile; refuses --all
  - Codex-only, explicit-profile, OAuth-only allowlist
  - Timestamped backup before any mutation; backup dir 700, files 0600
  - Rollback from pre-force backup if force-refresh fails or verification fails
  - Cooldown: refuses force-refresh if profile was refreshed < 60s ago (skipped if no state)
  - No token printing; fingerprints are SHA-256 prefix only
  - No doctor/gateway/service commands

Environment:
  AUTH_MOLT_STORE_PATH           Override auth store path (testing only)
  AUTH_MOLT_BACKUP_DIR           Override backup dir (testing only)
  AUTH_MOLT_STATE_FILE           Override cooldown state file (testing only)
`.trim());
}

function readStore(storePath = STORE_PATH) {
  const raw = fs.readFileSync(storePath, 'utf8');
  return JSON.parse(raw);
}

function writeStore(storePath, data) {
  fs.writeFileSync(storePath, JSON.stringify(data, null, 2), { mode: 0o600 });
}

function iso(ms) {
  return Number.isFinite(ms) ? new Date(ms).toISOString() : 'invalid/missing';
}

function statusFor(expires) {
  if (!Number.isFinite(expires)) return 'missing-expiry';
  const remaining = expires - Date.now();
  if (remaining <= 0) return 'expired';
  if (remaining <= WARN_WITHIN_MS) return 'expiring';
  return 'valid';
}

function fingerprint(value) {
  if (!value || typeof value !== 'string') return null;
  return crypto.createHash('sha256').update(value).digest('hex').slice(0, 12);
}

function profileFingerprints(profile) {
  return {
    access: fingerprint(profile?.access ?? profile?.accessToken ?? profile?.token ?? profile?.apiKey),
    refresh: fingerprint(profile?.refresh ?? profile?.refreshToken),
  };
}

function allowlistedProfileId(profileId) {
  return CODEX_PROFILE_ALLOWLIST.some((re) => re.test(String(profileId).toLowerCase()));
}

function allowlistedEmail(email) {
  return CODEX_EMAIL_ALLOWLIST.some((re) => re.test(String(email).toLowerCase()));
}

function summarize(profileId, profile) {
  return {
    profileId,
    provider: profile?.provider,
    type: profile?.type,
    email: profile?.email ?? '(none)',
    expires: profile?.expires,
    expiresIso: iso(profile?.expires),
    status: statusFor(profile?.expires),
  };
}

function validateTarget(profileId, profile) {
  if (!allowlistedProfileId(profileId)) throw new Error(`Refusing non-allowlisted profile id: ${profileId}`);
  if (!profile || profile.provider !== 'openai-codex') throw new Error(`Refusing non-Codex provider for ${profileId}`);
  if (profile.type !== 'oauth') throw new Error(`Refusing non-OAuth profile for ${profileId}: ${profile.type}`);
  if (profile.email && !allowlistedEmail(profile.email)) throw new Error(`Refusing unexpected email domain for ${profileId}`);
}

function ensureBackupDir() {
  fs.mkdirSync(BACKUP_DIR, { recursive: true });
  fs.chmodSync(BACKUP_DIR, 0o700);
}

function backupStore(tag = '') {
  ensureBackupDir();
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const suffix = tag ? `.${tag}` : '';
  const dest = path.join(BACKUP_DIR, `auth-profiles${suffix}.${stamp}.json`);
  fs.copyFileSync(STORE_PATH, dest, fs.constants.COPYFILE_EXCL);
  fs.chmodSync(dest, 0o600);
  return dest;
}

function readState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
  } catch {
    return { profiles: {} };
  }
}

function writeState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), { mode: 0o600 });
}

function checkCooldown(profileId) {
  const state = readState();
  const profileState = state.profiles?.[profileId];
  if (!profileState?.refreshedAt) return;
  const elapsed = Date.now() - profileState.refreshedAt;
  if (elapsed < COOLDOWN_MS) {
    throw new Error(
      `Cooldown: ${profileId} was refreshed ${Math.round(elapsed / 1000)}s ago (< 60s). Wait before retrying.`
    );
  }
}

function recordRefresh(profileId) {
  const state = readState();
  if (!state.profiles) state.profiles = {};
  state.profiles[profileId] = { refreshedAt: Date.now() };
  writeState(state);
}

// ─── Prune ───────────────────────────────────────────────────────────────────

async function runPrune({ execute, olderThanDays }) {
  const thresholdMs = olderThanDays * 24 * 60 * 60 * 1000;
  const now = Date.now();

  let files;
  try {
    files = fs.readdirSync(BACKUP_DIR);
  } catch {
    console.log(`Backup dir does not exist or is unreadable: ${BACKUP_DIR}`);
    return;
  }

  const backupPattern = /^auth-profiles.*\.json$/;
  const candidates = [];
  for (const f of files) {
    if (!backupPattern.test(f)) continue;
    const full = path.join(BACKUP_DIR, f);
    const stat = fs.statSync(full);
    const ageMs = now - stat.mtimeMs;
    if (ageMs >= thresholdMs) candidates.push({ file: f, full, ageMs });
  }

  if (candidates.length === 0) {
    console.log(`No backup files older than ${olderThanDays} day(s) found in ${BACKUP_DIR}`);
    return;
  }

  const verb = execute ? 'Deleting' : 'Would delete';
  console.log(`${verb} ${candidates.length} backup file(s) older than ${olderThanDays} day(s):`);
  for (const { file, ageMs } of candidates) {
    const ageDays = (ageMs / (24 * 60 * 60 * 1000)).toFixed(1);
    console.log(`  ${execute ? 'DELETE' : 'DRY'} ${file}  (${ageDays}d old)`);
  }

  if (!execute) {
    console.log('Dry-run: no files deleted. Add --execute to delete.');
    return;
  }

  for (const { full } of candidates) {
    fs.unlinkSync(full);
  }
  console.log(`Deleted ${candidates.length} backup file(s).`);
}

// ─── Force-expire refresh ─────────────────────────────────────────────────────

async function runForceExpiredRefresh(profileId, profile) {
  checkCooldown(profileId);

  const before = summarize(profileId, profile);
  const fpBefore = profileFingerprints(profile);

  console.log(`\nForce-expire refresh: ${profileId}`);
  console.log(`  original expiry: ${before.expiresIso}`);

  const preForceBackup = backupStore('pre-force');
  console.log(`  pre-force backup: ${preForceBackup}`);
  console.log('  WARNING: backup file contains credentials; keep private.');

  // Temporarily write faked expiry to store so OpenClaw sees the profile as expired
  const fakeExpiry = Date.now() - 60_000;
  const storeData = readStore();
  storeData.profiles[profileId] = { ...storeData.profiles[profileId], expires: fakeExpiry };
  writeStore(STORE_PATH, storeData);
  console.log(`  faked expiry to: ${iso(fakeExpiry)}`);

  let refreshed = false;
  try {
    const runtime = await import(SDK_PATH);
    const { ensureAuthProfileStore, resolveApiKeyForProfile } = runtime;
    if (typeof ensureAuthProfileStore !== 'function' || typeof resolveApiKeyForProfile !== 'function') {
      throw new Error('OpenClaw runtime auth helpers not available; refusing to continue.');
    }

    const runtimeStore = ensureAuthProfileStore(undefined, { allowKeychainPrompt: false });
    const resolved = await resolveApiKeyForProfile({ store: runtimeStore, profileId });
    if (!resolved || resolved.provider !== 'openai-codex') {
      throw new Error('Refresh returned no Codex credential result');
    }

    const afterStore = readStore();
    const afterProfile = afterStore.profiles?.[profileId];
    const after = summarize(profileId, afterProfile);
    const fpAfter = profileFingerprints(afterProfile);

    const expiryIncreased = Number.isFinite(after.expires) && after.expires > before.expires;
    const accessChanged = fpBefore.access !== fpAfter.access;
    const refreshChanged = fpBefore.refresh !== fpAfter.refresh;

    if (!expiryIncreased) {
      throw new Error(
        `Verification failed: post-refresh expiry (${after.expiresIso}) did not increase beyond original (${before.expiresIso})`
      );
    }
    if (!accessChanged && !refreshChanged) {
      throw new Error('Verification failed: neither access nor refresh token fingerprint changed after refresh');
    }

    refreshed = true;
    recordRefresh(profileId);

    console.log(`\nOK ${profileId} refreshed successfully`);
    console.log(`  expiry:                ${before.expiresIso} -> ${after.expiresIso}`);
    console.log(`  access-token changed:  ${accessChanged}`);
    console.log(`  refresh-token changed: ${refreshChanged}`);
  } catch (error) {
    if (!refreshed) {
      console.error(`\nFAIL: ${error?.message ?? error}`);
      console.error(`Rolling back from pre-force backup: ${preForceBackup}`);
      fs.copyFileSync(preForceBackup, STORE_PATH);
      fs.chmodSync(STORE_PATH, 0o600);
      console.error('Rollback complete. Auth store restored to pre-force state.');
      process.exit(2);
    }
    throw error;
  }
}

// ─── Arg parsing ─────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) { usage(); process.exit(0); }

const execute = args.includes('--execute');
const dryRun = args.includes('--dry-run') || !execute;
const all = args.includes('--all');
const forceExpiredForRefresh = args.includes('--force-expired-for-refresh');
const pruneBackups = args.includes('--prune-backups');

const profileArgs = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--profile') {
    if (!args[i + 1]) throw new Error('--profile requires a value');
    profileArgs.push(args[++i]);
  }
}

let olderThanDays = null;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--older-than') {
    if (!args[i + 1]) throw new Error('--older-than requires a value');
    olderThanDays = Number(args[++i]);
    if (!Number.isFinite(olderThanDays) || olderThanDays <= 0) throw new Error('--older-than must be a positive number');
  }
}

// ─── Refusal guards ───────────────────────────────────────────────────────────

if (!pruneBackups && execute && args.includes('--dry-run')) {
  throw new Error('Refusing ambiguous mode: use either --dry-run or --execute, not both.');
}

if (pruneBackups) {
  if (olderThanDays === null) throw new Error('--prune-backups requires --older-than <days>');
  await runPrune({ execute, olderThanDays });
  process.exit(0);
}

if (forceExpiredForRefresh) {
  if (!execute) throw new Error('--force-expired-for-refresh requires --execute.');
  if (all) throw new Error('--force-expired-for-refresh refuses --all; provide exactly one --profile.');
  if (profileArgs.length !== 1) throw new Error('--force-expired-for-refresh requires exactly one --profile.');
}

if (execute && all && profileArgs.length > 0) {
  throw new Error('Refusing ambiguous target set: use --profile for one profile or --all, not both.');
}

// ─── Main flow ────────────────────────────────────────────────────────────────

const store = readStore();
const profiles = store.profiles ?? {};
const targetIds = profileArgs.length > 0
  ? profileArgs
  : Object.entries(profiles)
      .filter(([, p]) => p?.provider === 'openai-codex' && p?.type === 'oauth')
      .map(([id]) => id)
      .sort();

if (targetIds.length === 0) throw new Error('No Codex OAuth profiles found.');
if (targetIds.length > 10) throw new Error(`Refusing unusually large target set: ${targetIds.length}`);
if (execute && !all && !forceExpiredForRefresh && profileArgs.length !== 1) {
  throw new Error('Execute mode requires exactly one --profile unless --all is explicitly passed. Try: --execute --profile openai-codex:claw4@edge.app');
}

for (const id of targetIds) validateTarget(id, profiles[id]);

console.log(`Auth Molt v0.1 — mode: ${dryRun ? 'dry-run' : 'execute'}${forceExpiredForRefresh ? ' (force-expired-for-refresh)' : ''}`);
console.log(`Auth store: ${STORE_PATH}`);
console.log('Targets:');
for (const id of targetIds) {
  const s = summarize(id, profiles[id]);
  console.log(`  ${s.profileId}  status=${s.status}  exp=${s.expiresIso}  email=${s.email}`);
}

if (dryRun) {
  console.log('Dry-run: no files changed. Re-run with --execute to refresh through OpenClaw OAuth manager.');
  process.exit(0);
}

if (forceExpiredForRefresh) {
  await runForceExpiredRefresh(targetIds[0], profiles[targetIds[0]]);
  process.exit(0);
}

// ─── Standard execute ─────────────────────────────────────────────────────────

const backup = backupStore();
console.log(`Backup: ${backup}`);
console.log('WARNING: backup file contains credentials; keep private.');

const runtime = await import(SDK_PATH);
const { ensureAuthProfileStore, resolveApiKeyForProfile } = runtime;
if (typeof ensureAuthProfileStore !== 'function' || typeof resolveApiKeyForProfile !== 'function') {
  throw new Error('OpenClaw runtime auth helpers not available; refusing to continue.');
}

const runtimeStore = ensureAuthProfileStore(undefined, { allowKeychainPrompt: false });
for (const id of targetIds) validateTarget(id, runtimeStore.profiles?.[id]);

const results = [];
for (const id of targetIds) {
  try {
    const before = summarize(id, runtimeStore.profiles[id]);
    const fpBefore = profileFingerprints(runtimeStore.profiles[id]);
    const resolved = await resolveApiKeyForProfile({ store: runtimeStore, profileId: id });
    if (!resolved || resolved.provider !== 'openai-codex') {
      throw new Error('Refresh returned no Codex credential result');
    }
    const afterStore = readStore();
    const after = summarize(id, afterStore.profiles?.[id]);
    const fpAfter = profileFingerprints(afterStore.profiles?.[id]);
    results.push({ id, ok: true, before, after });
    console.log(`OK ${id}`);
    console.log(`  expiry:                ${before.expiresIso} -> ${after.expiresIso}`);
    console.log(`  access-token changed:  ${fpBefore.access !== fpAfter.access}`);
    console.log(`  refresh-token changed: ${fpBefore.refresh !== fpAfter.refresh}`);
  } catch (error) {
    results.push({ id, ok: false, error: error?.message ?? String(error) });
    console.error(`FAIL ${id}: ${error?.message ?? error}`);
  }
}

const failed = results.filter(r => !r.ok);
if (failed.length > 0) {
  console.error(`Completed with ${failed.length} failure(s). Backup remains at ${backup}`);
  process.exit(2);
}

console.log('All selected Codex OAuth profiles refreshed/resolved successfully.');
