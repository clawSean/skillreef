# Skill Reef Vision

Skill Reef exists to give agents durable, practical skills they can apply without
guesswork.

The Telegram UI skill has one job: provide the strongest possible foundation for
agentic Telegram responses. An agent reading it should know which UI actions are
available, which send paths actually work, which fields to use, and which current
limitations to avoid.

## Principles

- Keep skills self-contained enough to be useful when copied alone.
- Prefer verified command shapes over abstract design advice.
- Document working paths, broken paths, and fallbacks plainly.
- Make agent behavior better at the moment of response, not just better in a
  documentation graph.
- Avoid pointing agents through a maze of other skills, procedures, or private
  workspace notes for core behavior.

## Telegram UI Target

The Telegram UI skill should answer these questions directly:

- Should this response be plain text, buttons, a poll, a reply, a reaction, an
  edit, media, a sticker, or a pin?
- Which OpenClaw `message` action and fields should be used?
- Which Telegram formatting survives outbound rendering?
- Which features are unavailable through the current OpenClaw Telegram path?
- What fallback should an agent use when a richer control fails?

If a future update adds a new Telegram UI capability, add the command shape and
the practical decision rule in the Telegram UI skill itself.
