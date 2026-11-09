import { inspectTelegramText } from "./guard.js";

export default {
  id: "telegram-ui",
  name: "Telegram UI Guard",
  register(api) {
    api.on("reply_payload_sending", (event, context) => {
      try {
        if ((event.channel ?? context.channelId) !== "telegram") return;
        const mode = api.pluginConfig?.mode ?? "warn";
        if (mode === "off") return;
        const payload = event.payload;
        if (typeof payload?.text !== "string" || payload.mediaUrl || payload.mediaUrls?.length || payload.attachments?.length || payload.presentation || payload.interactive || payload.audioAsVoice) return;
        const result = inspectTelegramText(payload.text, event.kind);
        if (result.warning) api.logger.warn(`telegram-ui guard: ${result.warning}`);
        if (!result.repairs) return;
        api.logger.warn(`telegram-ui guard: heading-boundary count=${result.repairs} mode=${mode}`);
        if (mode === "repair") return { payload: { ...payload, text: result.text } };
      } catch {
        // Formatting must never suppress delivery.
      }
    });
  },
};
