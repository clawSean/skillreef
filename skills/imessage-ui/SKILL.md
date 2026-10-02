---
name: "imessage-ui"
description: "Mandatory iMessage readability plus a current, phased native-feature test matrix."
---

# iMessage UI

Use for every iMessage conversation. The readability rules apply to every ordinary message; the native-action rules apply when sending interactive, expressive, formatted, threaded, mutable, or media-rich content.

For direct Mac bridge commands, target discovery, or history inspection, also load the bundled `imsg` skill and `clawnode-mac-node` when the Messages host is remote.

## Every-send readability checklist

1. Lead with the outcome or answer; do not bury it under setup.
2. Separate thought blocks with one blank line and keep paragraphs short.
3. Use bullets for three or more parallel items; keep each bullet to one idea.
4. Use native **bold** only for brief scan anchors, not whole paragraphs.
5. Use a threaded reply instead of quoting the message being answered.
6. Prefer a tapback when the entire response is acknowledgment.
7. Keep emoji moderate and effects exceptional; do not copy Telegram's decorative density.
8. Do not use Markdown headings, tables, raw HTML, or subjects for essential structure. The message must remain clear as plain text.

## Native-action preflight

1. Confirm the surface is iMessage, not SMS fallback.
2. Resolve the conversation. Prefer stable `chat_id`; keep the full chat GUID and message GUID for bridge actions.
3. Probe `openclaw channels status --probe --json` before private actions. Require `privateApi.available=true` and the needed RPC method/selector.
4. Pick the native semantic: reply, tapback, effect, poll, edit, unsend, attachment, typing/read, or group action.
5. Use OpenClaw's `message` action when exposed and proven for this route. Use direct `imsg` only as a deliberate bridge fallback.
6. Confirm destructive or conspicuous mutations unless the user's exact request already authorizes them.
7. Verify the visible result. A queued/success JSON response proves dispatch, not rendering.

## Capability ladder

### 1. Ordinary channel path

Use normal OpenClaw delivery for plain text and ordinary media when the route is healthy.

- Keep messages conversational and compact.
- Use one blank line between thoughts.
- Use replies instead of quoting whole messages.
- Prefer a tapback for pure acknowledgment.

### 2. OpenClaw private actions

When exposed by the current message tool/channel action surface:

- `react`: native tapback on a specific message.
- `reply`: true threaded reply.
- `sendWithEffect`: bubble or screen effect.
- `edit`: change a message sent by the gateway.
- `unsend`: retract a message sent by the gateway.
- `poll` / `poll-vote`: native Apple Messages polls.
- `upload-file` / attachment send: media, including attachment replies when supported.
- Group actions: rename, icon, add/remove participant, leave.

Action schemas vary by runtime. Inspect the live tool schema or local docs; do not invent fields from memory.

### 3. Direct `imsg` bridge fallback

Use only when OpenClaw does not expose the action, the configured remote wrapper is the failing boundary, or the task needs a bridge-only feature such as multipart text, explicit formatting ranges, stickers, or rich link previews.

Before acting:

- Resolve the exact `chat_id` and full chat GUID.
- Quote chat GUIDs containing semicolons.
- Prefer full message GUIDs for reply, reaction, edit, unsend, poll, and sticker targets.
- Record whether the direct bridge worked so the fallback does not become folklore.

Recipes and the local live matrix are in `references/action-matrix.md`.

## Fast decision rule

- Short conversational response → plain text.
- Answering one message → threaded reply.
- Acknowledging only → tapback.
- Correcting our recent message → edit in place.
- Removing an accidental or sensitive recent message → unsend after confirmation when needed.
- Two to twelve vote choices → native poll.
- Expressive social moment → one proven effect; never effects for serious, urgent, or accessibility-sensitive content.
- Photo/file → attachment; add a short caption separately if the action path cannot combine them.
- Group mutation → inspect participants and confirm exact target first.

## Formatting

- OpenClaw Markdown stored native bold, italic, and strikethrough metadata in the local live battery.
- Raw `<u>` through the normal OpenClaw path did not store underline metadata. Do not use it as a claimed underline path.
- Direct `imsg send-rich` formatting uses UTF-16 `start`/`length` ranges with styles `bold`, `italic`, `underline`, and `strikethrough`; all four stored correctly in the live battery.
- Do not assume Telegram HTML, spoilers, tables, buttons, selects, pins, WebApps, or rich-body blocks exist on iMessage.

## Replies and tapbacks

- Use full message GUIDs when available; short IDs can expire or belong to another chat.
- Supported tapback meanings: love, like, dislike, laugh, emphasize, question.
- Adding and removing specific tapbacks were verified through direct bridge commands and message history.
- Removing a tapback is a visible mutation.
- If a high-level action fails, inspect the transport boundary before claiming the native feature is unsupported.

## Effects

Effects are decorative. Use at most one per message and only when it helps the moment.

Human-visible on the 2026-07-26/27 local battery:

- `impact` / Slam
- `loud`
- `gentle`
- `invisibleink`
- `confetti`
- `lasers`
- `fireworks`
- `echo`
- `sparkles`
- `spotlight`
- `com.apple.messages.effect.CKHappyBirthdayEffect` for balloons/birthday
- `com.apple.messages.effect.CKHeartEffect` for heart
- `com.apple.messages.effect.CKShootingStarEffect` for shooting star

The short aliases `balloon`, `heart`, `happybirthday`, and `shootingstar` queued but did not render because Messages stored those literal strings instead of Apple effect IDs. Use the full IDs above on this local route until alias mapping is fixed.

Do not call an effect supported merely because the bridge returned `queued:true`.

## Polls

- Native poll creation needs 2–12 options and `pollPayloadMessage`.
- Voting needs `pollVoteMessage` plus `poll.vote`.
- Preserve the poll message GUID and option IDs.
- Prefer option ID over label when correctness matters.
- Current local caveat: inbound vote option 2 was rendered as option 1's label. Verify against `option_id` and the original poll instead of trusting the displayed label.
- Poll questions may be delivered as a separate caption because Messages renders only option labels in the balloon.

## Media, stickers, links, and subjects

- Verify the file exists and is intended before sending.
- Inbound attachments require `channels.imessage.includeAttachments=true`; remote setups also require safe attachment roots/SCP routing.
- Enabling inbound attachments is a live config change; follow local approval rules.
- Sticker sends require an iMessage-typed chat plus a compliant PNG/APNG/GIF/JPEG up to 500 KiB and 618×618.
- Rich link previews and stickers can fail when the local DB identifies a conversation as `any`/SMS even if ordinary bridge text arrives blue. Report that boundary; do not silently downgrade a sticker into a normal image.
- iMessage subjects are longstanding, not a recent client feature. The current route queued a subject message, but the recipient saw no subject and the sent row's `subject` column was `NULL`.
- The iPhone `Show Subject Field` setting may affect composition/display, but cannot fix a sender row with no subject metadata. Never put essential hierarchy or meaning only in a subject.

## Typing, delivery, and read receipts

With the private bridge up, OpenClaw normally marks accepted inbound chats read and shows typing while generating.

- Do not manually spam typing indicators.
- Respect `channels.imessage.sendReadReceipts=false`.
- Explicit typing and mark-read actions passed the live battery.
- Sent test messages reached `is_delivered=1`; `is_read` remains recipient-dependent.
- Transport proof is not the same as human-visible UI proof.

## Group actions

Group rename, icon, membership changes, leave, and delete are high-visibility mutations.

1. Inspect the group and participant list.
2. Use a stable group chat ID/GUID.
3. Confirm the exact mutation unless already explicitly authorized.
4. Never test membership or leave/delete behavior in a real social group just to prove capability.
5. Prefer an isolated throwaway group for a full battery.

## Local known failures

See `references/action-matrix.md` before using the current remote route.

The 2026-07-26 workspace battery originally found that OpenClaw high-level
actions resolved the DM to a semicolon-bearing chat GUID that the SSH wrapper
did not quote safely. The wrapper was repaired on 2026-07-27 and high-level
reply, tapback, poll, and media canaries passed. Do not keep treating the old
wrapper failure as live.

The current unresolved send-path failure is different: a high-level iMessage
send can time out after dispatch even though the message later appears in
Messages. Treat every timeout or post-dispatch disconnect as **unknown
delivery**, never as proof of failure. The same path can delay the automatic
`/stop` acknowledgment even when cancellation itself succeeded immediately.

Use `scripts/reconcile-outbound.sh` or an equivalent exact Messages-history
check before deciding whether a fallback or retry is safe.

## Repair flow

- Wrong semantic used → acknowledge briefly and resend as reply/tapback/poll as appropriate.
- Action queued but did not render → report dispatch vs UI separately; do not retry repeatedly.
- Send timed out or disconnected after dispatch → mark it `unknown_delivery`.
  Do not retry, fallback, or send equivalent text through another path until
  Messages history has been reconciled.
- Reconciliation found one exact outbound match → record the existing GUID and
  stop. The original send succeeded even if the caller timed out.
- Reconciliation found no exact match → wait for the bounded delivery window,
  query again, then allow at most one deliberate fallback. Reconcile that
  fallback too.
- Reconciliation found multiple matches or cannot inspect history → stop and
  report ambiguity. Never guess by sending another copy.
- Never run the high-level and direct bridge paths concurrently for the same
  semantic message.
- A `/stop` command owns its own acknowledgment. Do not manually send a second
  stop confirmation. Verify cancellation in Gateway logs separately from
  acknowledgment delivery.
- Before answering a queued follow-up, compare it with the newest inbound
  message and current live state. If a newer `/stop`, replacement request, or
  completed state supersedes it, drop the stale reply.
- Private action says unavailable → refresh the capability probe, then inspect the bridge/helper status.
- Remote wrapper fails on a chat GUID → stop retries, preserve the exact error, and use a confirmed direct bridge route only when authorized.
- Group target is ambiguous → stop and resolve participants before acting.
