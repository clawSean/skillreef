import { inspectTelegramText } from "./guard.js";

export default {
  id: "telegram-ui",
  name: "Telegram UI Guard",
  register(api) {
    api.on("message_sending", (event, context) => {
      try {
        if (context.channelId !== "telegram") return;
        const mode = api.pluginConfig?.mode ?? "warn";
        if (mode === "off") return;
        const result = inspectTelegramText(event.content);
        if (!result.repairs) return;
        api.logger.warn(`telegram-ui guard: heading-boundary count=${result.repairs} mode=${mode}`);
        if (mode === "repair") return { content: result.text };
      } catch {
        // Formatting must never suppress delivery.
      }
    });
  },
};
