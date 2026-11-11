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

test("rejects private chats because Telegram cannot close their topics", () => {
  assert.throws(
    () => parseArgs(["close", "--chat", "123456789", "--thread", "42"]),
    /Telegram supergroup ID/,
  );
});

test("rejects destructive and unknown actions", () => {
  assert.throws(
    () => parseArgs(["delete", "--chat", "-1001234567890", "--thread", "42"]),
    /Unsupported action/,
  );
});

test("rejects malformed topic IDs", () => {
  assert.throws(
    () => parseArgs(["reopen", "--chat", "-1001234567890", "--thread", "nope"]),
    /positive integer/,
  );
});
