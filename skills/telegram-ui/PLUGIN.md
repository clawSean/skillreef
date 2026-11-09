# Optional Telegram UI output guard

The `telegram-ui` skill works without this plugin. The optional OpenClaw plugin
adds a narrow, fail-open outbound hook; it does not replace the skill or make
arbitrary message formatting safe.

## Current rules

- `warn` (default): logs a rule name/count for the known
  `<br><br>### Heading` boundary and warns when an ordinary final contains plain
  blank-line paragraphs. It never changes or cancels a send.
- `repair`: changes only the exact heading boundary to two source newlines,
  outside obvious code/structural markup. It does **not** auto-double newlines.
- `off`: does nothing.

The hook skips non-Telegram channels, non-text, media, and structured controls.
It catches its own errors and never returns a cancellation. Logs never include
message bodies. The ordinary-final paragraph warning is detection-only because
that route has leaked break tags literally on iOS; automatic insertion there
would make delivery less readable. The skill instead routes multi-block text
through the calibrated explicit-send path.

## Use

Skill-only: place this directory in your OpenClaw workspace's `skills/` folder.
Nothing else is required.

Plugin-enhanced: keep the same skill directory and install it as a local
OpenClaw plugin with `openclaw plugins install --link --no-enable <skill-path>`.
Enable the plugin only after inspecting it and the current OpenClaw hook
contract. Start in `warn` mode; promote `plugins.entries.telegram-ui.config.mode`
to `repair` only after route-specific client proof. Follow your installation's
normal reload procedure to activate a config change.

Run `npm test` in this directory for pure guard fixtures. The package has no
runtime dependencies. The current local package has been tested offline; it is
not installed or active on the contributor's Gateway.
