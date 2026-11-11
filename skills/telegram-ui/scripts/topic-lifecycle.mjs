#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const USAGE = `Usage:
  topic-lifecycle.mjs inspect --chat <supergroup-id> [--account <id>]
  topic-lifecycle.mjs close --chat <supergroup-id> --thread <topic-id> [--account <id>]
  topic-lifecycle.mjs reopen --chat <supergroup-id> --thread <topic-id> [--account <id>]
  topic-lifecycle.mjs delete --chat <chat-id> --thread <topic-id> [--account <id>]

Close/reopen supports forum supergroups. Delete supports forum supergroups and
private chats with topics; it removes the topic and its Telegram messages.`;

export function parseArgs(argv) {
  const [action, ...rest] = argv;
  if (action === "--help" || action === "-h" || !action) return { help: true };
  if (!new Set(["inspect", "close", "reopen", "delete"]).has(action)) {
    throw new Error(`Unsupported action: ${action}`);
  }
  const values = { action, account: "default" };
  for (let index = 0; index < rest.length; index += 2) {
    const flag = rest[index];
    const value = rest[index + 1];
    if (!value || !new Set(["--chat", "--thread", "--account"]).has(flag)) {
      throw new Error(`Invalid argument near: ${flag ?? "<end>"}`);
    }
    values[flag.slice(2)] = value;
  }
  if (!/^(?:-100\d+|\d+)$/.test(values.chat ?? "")) {
    throw new Error("--chat must be a Telegram private-chat or supergroup ID");
  }
  if (new Set(["close", "reopen"]).has(action) && !/^-100\d+$/.test(values.chat)) {
    throw new Error(`${action} requires a Telegram forum supergroup ID beginning with -100`);
  }
  if (action !== "inspect" && !/^\d+$/.test(values.thread ?? "")) {
    throw new Error("--thread must be a positive integer topic ID");
  }
  if (!/^[a-zA-Z0-9_-]+$/.test(values.account)) {
    throw new Error("--account contains unsupported characters");
  }
  return values;
}

function findOpenClawRoot() {
  const override = process.env.OPENCLAW_PACKAGE_ROOT?.trim();
  if (override) return override;
  const npmRoot = execFileSync("npm", ["root", "-g"], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"],
  }).trim();
  return path.join(npmRoot, "openclaw");
}

async function loadOpenClaw() {
  const root = findOpenClawRoot();
  const configModule = path.join(root, "dist/plugin-sdk/runtime-config-snapshot.js");
  const telegramModule = path.join(root, "dist/extensions/telegram/runtime-api.js");
  if (!existsSync(configModule) || !existsSync(telegramModule)) {
    throw new Error(`Compatible OpenClaw runtime modules were not found under ${root}`);
  }
  const [{ captureRuntimeConfigAsyncReader }, { resolveTelegramToken }] = await Promise.all([
    import(pathToFileURL(configModule)),
    import(pathToFileURL(telegramModule)),
  ]);
  return { captureRuntimeConfigAsyncReader, resolveTelegramToken };
}

function createApi(token) {
  return async (method, body = {}) => {
    const response = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    const result = await response.json();
    if (!result.ok) {
      const description = String(result.description ?? "Telegram request failed").replaceAll(
        token,
        "[redacted]",
      );
      throw new Error(`${method}: ${description}`);
    }
    return result.result;
  };
}

async function preflight(api, chatId, action) {
  const [bot, chat] = await Promise.all([api("getMe"), api("getChat", { chat_id: chatId })]);
  if (chat.type === "private") {
    if (!new Set(["inspect", "delete"]).has(action)) {
      throw new Error(`${action} is unavailable for Telegram private-chat topics`);
    }
    return { chatId: String(chat.id), chatType: "private" };
  }
  if (chat.type !== "supergroup" || chat.is_forum !== true) {
    throw new Error("Target must be a private chat or forum-enabled Telegram supergroup");
  }
  const member = await api("getChatMember", { chat_id: chatId, user_id: bot.id });
  const creator = member.status === "creator";
  if (action === "delete") {
    if (!creator && (member.status !== "administrator" || member.can_delete_messages !== true)) {
      throw new Error("Bot needs the Telegram Delete Messages administrator permission");
    }
  } else if (!creator && member.can_manage_topics !== true) {
    throw new Error("Bot needs the Telegram Manage Topics administrator permission");
  }
  return {
    chatId: String(chat.id),
    chatType: "supergroup",
    botStatus: member.status,
    canManageTopics: creator || member.can_manage_topics === true,
    canDeleteMessages: creator || member.can_delete_messages === true,
  };
}

export async function run(options) {
  const { captureRuntimeConfigAsyncReader, resolveTelegramToken } = await loadOpenClaw();
  const readConfig = await captureRuntimeConfigAsyncReader();
  const config = await readConfig();
  const resolution = resolveTelegramToken(config, { accountId: options.account });
  if (!resolution.token) throw new Error(`Telegram token unavailable for account ${options.account}`);
  const api = createApi(resolution.token);
  const proof = await preflight(api, options.chat, options.action);
  if (options.action === "inspect") return { ok: true, action: "inspect", ...proof };

  if (options.action === "delete") {
    if (options.thread === "1" && proof.chatType === "supergroup") {
      throw new Error("Telegram's General forum topic cannot be deleted");
    }
    await api("deleteForumTopic", {
      chat_id: options.chat,
      message_thread_id: Number(options.thread),
    });
    return {
      ok: true,
      action: "delete",
      chatId: options.chat,
      chatType: proof.chatType,
      threadId: options.thread,
      telegramMessagesDeleted: true,
    };
  }

  const general = options.thread === "1";
  const method = general
    ? `${options.action}GeneralForumTopic`
    : `${options.action}ForumTopic`;
  const payload = general
    ? { chat_id: options.chat }
    : { chat_id: options.chat, message_thread_id: Number(options.thread) };
  await api(method, payload);
  return {
    ok: true,
    action: options.action,
    chatId: options.chat,
    threadId: options.thread,
    general,
  };
}

async function main() {
  try {
    const options = parseArgs(process.argv.slice(2));
    if (options.help) {
      console.log(USAGE);
      return;
    }
    console.log(JSON.stringify(await run(options), null, 2));
  } catch (error) {
    console.error(`topic-lifecycle: ${error instanceof Error ? error.message : String(error)}`);
    process.exitCode = 1;
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) await main();
