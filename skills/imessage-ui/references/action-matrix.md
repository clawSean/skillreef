# iMessage UI action matrix

Calibrated 2026-07-26 through 2026-08-03 on OpenClaw 2026.7.1, `imsg 0.13.3`, private API v2, macOS Messages host over the workspace SSH wrapper. This is local evidence, not a universal compatibility promise.

## Live results

- Plain OpenClaw text send: PASS.
- OpenClaw formatting: PASS for bold, italic, strikethrough metadata; FAIL for raw `<u>` underline.
- Direct rich formatting ranges: PASS for bold, italic, underline, strikethrough metadata.
- Direct threaded reply: PASS; history preserved `thread_originator_guid`.
- Direct tapback add/remove by full GUID: PASS; history showed add and cleanup.
- Effects visibly confirmed by recipient: impact/Slam, loud, gentle, invisible ink, confetti, lasers, fireworks, echo, sparkles, spotlight, balloons/birthday, heart, shooting star.
- Early direct-bridge alias failure: short aliases balloon, heart, happy birthday,
  and shooting star stored literal values and did not render.
- Current OpenClaw alias isolation: `balloons` stores
  `com.apple.MobileSMS.expressivesend.balloon`, while `heart` stores
  `com.apple.MobileSMS.expressivesend.heart`. Full-ID controls store the proven
  CK effect IDs. All four delivered; current-build recipient-visible comparison
  is pending.
- Full-ID effect retries: PASS; delivered, stored exact Apple IDs, and recipient confirmed all three animated.
- Edit: PASS.
- Unsend: PASS; local history row became empty/retracted.
- Outbound image attachment: PASS through direct bridge.
- Audio-message attachment: BRIDGE/STORAGE PASS. The delivered row had
  `is_audio_message=1`, `service=iMessage`, and a 26,640-byte `audio/mpeg`
  attachment. Recipient-visible bubble/playback confirmation is pending.
- Attachment reply: PASS; history preserved thread origin.
- Explicit typing (5 seconds): PASS.
- Mark read: PASS.
- Mark unread/read round-trip: PASS; unread count returned to zero.
- Search/history/account/reachability inspection: PASS; the test handle was
  reported reachable on iMessage.
- Scheduled-message inventory, shared nickname metadata, Name & Photo status,
  and chat-background status: readable; no scheduled row or custom background
  was present.
- Notify Anyway: BRIDGE/STORAGE PASS against a genuinely quiet-delivered audio
  message. The one action changed `did_notify_recipient` from 0 to 1 while
  preserving `was_delivered_quietly=1`; recipient-visible notification
  confirmation is pending.
- Delivery state: PASS (`is_delivered=1`); recipient read state is separate.
- Native poll create: PASS.
- Native poll vote and unvote: PASS; correct option ID/text returned by direct `imsg`.
- Inbound vote rendering: FAIL for option 2 label; OpenClaw reported option 1 text.
- Subject message: FAIL in both the owner DM and a properly iMessage-typed test
  group. Both delivered as iMessage, but their sent rows had `subject=NULL`.
- Multipart text: PASS; history stored the combined text.
- Rich URL preview: BRIDGE/STORAGE PASS in the isolated iMessage test group.
  History stored `com.apple.messages.URLBalloonProvider` plus a 168,352-byte
  hidden preview payload. Recipient-visible rendering confirmation is pending.
- Sticker: LOCALLY BLOCKED before dispatch. Native sticker selectors are live,
  but the helper's security check rejects `~/Library/Messages`
  because the directory is world-writable (`0777`). Repair requires explicit
  approval before retesting; no sticker was sent.
- Group rename and icon mutation: BRIDGE/STORAGE PASS in the isolated test group
  containing only the reviewer and the contributor's iMessage alias. History recorded two rename
  events and a group-photo action. Recipient-visible confirmation is pending.
- Group membership: NOT TESTED; no safe third iMessage identity was authorized.
- Group leave: DEFERRED until the isolated group's remaining visual tests are
  complete because leaving is destructive.
- Native Genmoji/Memoji/Image Playground composition: not exposed by the current
  OpenClaw/imsg bridge. Sending a generated image or sticker is ordinary media,
  not native composition parity.
- Inbound attachments: PASS after `includeAttachments=true`; a PNG arrived
  automatically through the remote Messages attachment path and was available
  in the agent turn.

## Remaining feature phases

1. **Recipient confirmation:** native audio bubble/playback; current-build
   balloon/heart alias animation versus full-ID controls; test-group link
   preview/name/icon; Notify Anyway alert.
2. **Approved local repair:** remove the world-writable bit from the exact
   Messages directory, then test native sticker send and sticker attach.
3. **Authorized group identity:** add/remove one safe third iMessage handle,
   then leave the isolated group last.
4. **Upstream candidates:** effect alias mapping and subject metadata now have
   isolated current-build evidence; package them only after the remaining
   recipient-visible comparison where applicable.
5. **Not bridge-native:** Send Later creation, Location, Check In, Digital
   Touch, Genmoji/Memoji/Image Playground composition, Apple Cash, and
   third-party iMessage apps. Test only if a new bridge capability appears.

## Effect storage evidence

Working aliases stored full Apple IDs, for example:

- impact → `com.apple.MobileSMS.expressivesend.impact`
- confetti → `com.apple.messages.effect.CKConfettiEffect`
- echo → `com.apple.messages.effect.CKEchoEffect`
- sparkles → `com.apple.messages.effect.CKSparklesEffect`

Failed short aliases stored the literal values `balloon`, `heart`, `happybirthday`, and `shootingstar`.

The working full-ID retries used:

- `com.apple.messages.effect.CKHappyBirthdayEffect`
- `com.apple.messages.effect.CKHeartEffect`
- `com.apple.messages.effect.CKShootingStarEffect`

The recipient confirmed all three animated. Use the full IDs as the local workaround until short-alias mapping is fixed.

## Remote wrapper status

The original SSH argv bug was repaired on 2026-07-27. The active wrapper now
quotes every remote argument, stages outbound files to an exact temporary Mac
path, and cleans only that staged path. Hostile argv and exact-byte file tests
passed, followed by live high-level reply, tapback add/remove, poll
create/retract, and media send/retract canaries.

Do not diagnose the historical `zsh: command not found` error as current without
reproducing it against the active wrapper.

## Current high-level send ambiguity

On 2026-07-28, a high-level text send remained in the OpenClaw `message` tool
until its 120-second watchdog fired. Messages history later showed that the
text had delivered. A direct fallback sent during that ambiguous interval
therefore created a duplicate.

The same blocked outbound path delayed the automatic `⚙️ Agent was aborted.`
reply even though Gateway logs showed `/stop` canceled the run within about one
second.

Local policy:

1. A timeout or post-dispatch disconnect means `unknown_delivery`.
2. Do not retry or fall back until exact Messages-history reconciliation.
3. One exact outbound match means success; preserve its GUID and stop.
4. No match means wait through the bounded delivery window and query again
   before one fallback.
5. Multiple matches or unavailable history means stop and report ambiguity.
6. Never manually duplicate the `/stop` acknowledgment.

For text sends, use `../scripts/reconcile-outbound.sh` with the exact chat ID,
text, and a `--since` boundary. Media requires equivalent reconciliation by
outbound attachment metadata; if that proof is unavailable, do not retry.

## Safe direct bridge patterns

First load the bundled `imsg` skill for full command rules.

```bash
imsg status --json
imsg chats --json
imsg history --chat-id <id> --limit 20 --attachments --json
```

Threaded reply:

```bash
imsg send-rich --chat '<chat-guid>' --reply-to '<message-guid>' --text 'reply'
```

Tapback:

```bash
imsg tapback --chat '<chat-guid>' --message '<message-guid>' --kind like
```

Effect:

```bash
imsg send-rich --chat '<chat-guid>' --text 'boom' --effect impact
```

For the three broken short aliases, use full IDs:

```bash
imsg send-rich --chat '<chat-guid>' --text 'birthday' --effect com.apple.messages.effect.CKHappyBirthdayEffect
imsg send-rich --chat '<chat-guid>' --text 'heart' --effect com.apple.messages.effect.CKHeartEffect
imsg send-rich --chat '<chat-guid>' --text 'shooting star' --effect com.apple.messages.effect.CKShootingStarEffect
```

Formatting ranges use UTF-16 offsets:

```bash
imsg send-rich --chat '<chat-guid>' --text 'Bold text' \
  --format '[{"start":0,"length":4,"styles":["bold"]}]'
```

Edit and unsend:

```bash
imsg edit --chat '<chat-guid>' --message '<message-guid>' --new-text 'updated'
imsg unsend --chat '<chat-guid>' --message '<message-guid>'
```

Poll:

```bash
imsg poll send --chat '<chat-guid>' --question 'Pick one' \
  --option 'A' --option 'B'
imsg poll vote --chat '<chat-guid>' --poll '<poll-guid>' --option-id '<option-id>'
imsg poll unvote --chat '<chat-guid>' --poll '<poll-guid>' --option-id '<option-id>'
```

Attachment reply:

```bash
imsg send-attachment --chat '<chat-guid>' --reply-to '<message-guid>' --file '<path>'
```

Typing/read:

```bash
imsg typing --chat-id <id> --duration 5s
imsg read --chat-id <id>
```

## OpenClaw action field guide

Check the live message-tool schema first. Current OpenClaw docs define:

- react: `messageId`, `emoji`, optional `remove`.
- reply: `messageId` plus `text`/`message` and a chat target.
- sendWithEffect: `text`/`message` plus `effect`/`effectId`.
- edit: `messageId` plus `text`/`newText`; own sent messages only.
- unsend: `messageId`; own sent messages only.
- poll: `pollQuestion`, 2–12 `pollOption` values, and a chat target.
- poll-vote: `pollId`/`messageId` plus exactly one option index, ID, or text.
- upload-file/sendAttachment: file path/media/buffer and optional filename/voice flag.
- group actions: exact group target plus action-specific name/icon/participant field.

Action names or field exposure may change. Local docs and the injected tool schema win over this reference.
