import assert from "node:assert/strict";
import test from "node:test";

import { parseArgs } from "./topic-lifecycle.mjs";

test("parses a close request", () => {
  assert.deepEqual(
    parseArgs(["close", "--chat", "-1001234567890", "--thread", "42", "--account", "bot"]),
    { action: "close", chat: "-1001234567890", thread: "42", account: "bot" },
  );
});

test("inspect does not require a thread", () => {
  assert.deepEqual(parseArgs(["inspect", "--chat", "-1001234567890"]), {
    action: "inspect",
    chat: "-1001234567890",
    account: "default",
  });
});

test("parses private-chat topic deletion", () => {
  assert.deepEqual(parseArgs(["delete", "--chat", "123456789", "--thread", "42"]), {
    action: "delete",
    chat: "123456789",
    thread: "42",
    account: "default",
  });
});

test("rejects close for private-chat topics", () => {
  assert.throws(
    () => parseArgs(["close", "--chat", "123456789", "--thread", "42"]),
    /forum supergroup ID/,
  );
});

test("rejects unknown actions", () => {
  assert.throws(
    () => parseArgs(["archive", "--chat", "-1001234567890", "--thread", "42"]),
    /Unsupported action/,
  );
});

test("rejects malformed topic IDs", () => {
  assert.throws(
    () => parseArgs(["reopen", "--chat", "-1001234567890", "--thread", "nope"]),
    /positive integer/,
  );
});
