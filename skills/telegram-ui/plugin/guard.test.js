import test from "node:test";
import assert from "node:assert/strict";
import plugin from "./index.js";
import { inspectTelegramText } from "./guard.js";

test("repairs only the exact heading boundary", () => {
  assert.deepEqual(inspectTelegramText("Before<br><br>### After"), {
    text: "Before\n\n### After", repairs: 1,
  });
  assert.equal(inspectTelegramText("A<br><br>## B<br><br>### C").repairs, 2);
});

test("preserves ambiguous and unrelated markup", () => {
  for (const text of ["A<br>B", "A<br><br>B", "`A<br><br>### B`", "```\nA<br><br>### B\n```", "<ul><li>A</li></ul><br><br>### B"]) {
    assert.equal(inspectTelegramText(text).text, text);
  }
});

test("does not rewrite blank-line paragraphs", () => {
  assert.deepEqual(inspectTelegramText("First\n\nSecond"), {
    text: "First\n\nSecond", repairs: 0,
  });
});

test("hook is Telegram-only, defaults to warn, repairs only in repair mode, never cancels", () => {
  let hook;
  const logs = [];
  const api = { pluginConfig: { mode: "warn" }, logger: { warn: (s) => logs.push(s) }, on: (_name, fn) => { hook = fn; } };
  plugin.register(api);
  const event = { content: "A<br><br>### B" };
  assert.equal(hook(event, { channelId: "telegram" }), undefined);
  assert.equal(hook(event, { channelId: "sms" }), undefined);
  api.pluginConfig.mode = "repair";
  assert.deepEqual(hook(event, { channelId: "telegram" }), { content: "A\n\n### B" });
  assert.equal(logs.some((s) => s.includes("A<br>")), false);
  api.logger.warn = () => { throw new Error("logger down"); };
  assert.equal(hook(event, { channelId: "telegram" }), undefined);
});
