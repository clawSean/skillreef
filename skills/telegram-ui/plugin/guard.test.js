import test from "node:test";
import assert from "node:assert/strict";
import plugin from "./index.js";
import { inspectTelegramText } from "./guard.js";

test("repairs adjacent and whitespace-separated heading boundaries", () => {
  assert.deepEqual(inspectTelegramText("Before<br><br>### After"), {
    text: "Before\n\n### After", repairs: 1,
  });
  for (const [input, heading] of [
    ["Before<br><br>\n\n### After", "###"],
    ["Before<BR><BR>  \r\n### After", "###"],
    ["Before\n<br><br>\n## After", "##"],
  ]) {
    assert.deepEqual(inspectTelegramText(input), {
      text: `Before\n\n${heading} After`, repairs: 1,
    });
  }
  assert.equal(inspectTelegramText("A<br><br>## B<br><br>### C").repairs, 2);
});

test("preserves malformed boundaries inside code and structural markup", () => {
  for (const text of [
    "`A<br><br>### B`",
    "```\nA<br><br>### B\n```",
    "<ul><li>A<br><br>### B</li></ul>",
    "<details>A<br><br>\n### B</details>",
  ]) {
    assert.equal(inspectTelegramText(text).text, text);
  }
});

test("repairs safe boundaries elsewhere in messages that contain protected markup", () => {
  assert.deepEqual(inspectTelegramText("Use `x` here.\nNext<br><br>\n### After"), {
    text: "Use `x` here.\nNext\n\n### After", repairs: 1,
  });
  assert.deepEqual(inspectTelegramText("<ul><li>A</li></ul>\nNext<br><br>### After"), {
    text: "<ul><li>A</li></ul>\nNext\n\n### After", repairs: 1,
  });
});

test("preserves unrelated content and non-text payloads", () => {
  for (const text of ["A<br>B", "A<br><br>B", "First\n\nSecond", "A<br><br>###No space", "A<br><br>####### B"]) {
    assert.deepEqual(inspectTelegramText(text), { text, repairs: 0 });
  }
  assert.deepEqual(inspectTelegramText(undefined), { text: undefined, repairs: 0 });
});

test("hook is Telegram-only, honors every mode, and never cancels", () => {
  let hook;
  const logs = [];
  const api = { pluginConfig: { mode: "warn" }, logger: { warn: (s) => logs.push(s) }, on: (_name, fn) => { hook = fn; } };
  plugin.register(api);
  const event = { content: "A<br><br>\n\n### B" };
  assert.equal(hook(event, { channelId: "telegram" }), undefined);
  assert.equal(hook(event, { channelId: "sms" }), undefined);
  api.pluginConfig.mode = "off";
  assert.equal(hook(event, { channelId: "telegram" }), undefined);
  api.pluginConfig.mode = "repair";
  assert.deepEqual(hook(event, { channelId: "telegram" }), { content: "A\n\n### B" });
  assert.deepEqual(logs, ["telegram-ui guard: heading-boundary count=1 mode=warn", "telegram-ui guard: heading-boundary count=1 mode=repair"]);
  assert.equal(hook({ content: { blocks: [] } }, { channelId: "telegram" }), undefined);
  api.logger.warn = () => { throw new Error("logger down"); };
  assert.equal(hook(event, { channelId: "telegram" }), undefined);
});
