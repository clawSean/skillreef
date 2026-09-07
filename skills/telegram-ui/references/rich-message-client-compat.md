# Telegram Rich-Message Client Compatibility

Use this guide when a Telegram client renders rich bodies, tables, details,
lists, buttons, or spacing differently from the current calibrated surface.
Operating rules live in `SKILL.md`; dated results live in
`rich-rendering-matrix.md`.

## Diagnose the failing layer

1. Capture the exact OpenClaw version, selected Telegram account, effective
   `richMessages` value, client platform/version/build, and chat surface.
2. Inspect the stored outbound body or returned send result. A complete payload
   plus incomplete display points downstream to Telegram server/client layout.
3. Identify the symptom before selecting a fallback:
   - **Unsupported-message banner:** the client cannot display this rich body.
   - **Rendered but cramped/misaligned:** the rich path works; isolate markup or
     client layout with the matching canary.
   - **Literal tags:** the body used a tag outside the active path's contract or
     a rich-only island entered a legacy caption/HTML path.
   - **Missing controls:** inspect presentation schema and delivery result; body
     richness does not create buttons.
4. Run only the smallest discriminating canary from
   `rich-rendering-matrix.md`; never mix Markdown and raw-HTML lanes in one test.
5. Inspect the actual client at native/Retina resolution and record message IDs
   plus screenshots.

## Fallbacks

- **Unsupported rich body:** resend with normal Telegram Markdown/HTML only.
  Use literal line breaks and text bullets; omit rich-only tables, details,
  formulas, rich media, and structural HTML islands.
- **Spacing regression on a client that still renders rich bodies:** follow the
  separator boundary map and list-density rule in
  [SKILL.md](../SKILL.md#structure-and-spacing). Check especially that the final
  prose/literal-list item and following prose use a source-adjacent inline break,
  real source blank lines terminate structural islands, and no break is glued to
  them. Avoid a standalone break paragraph because it compounds the gap.
- **Table truncation or leaked markup:** immediately resend every relevant row
  as literal-`•` blocks using the same whole-list density rule, then suspend
  tables on that exact surface until T7 passes.
- **Missing button/action:** keep the choice or exact value visible in text. Do
  not fabricate a look-alike callback or use a token-bearing raw Bot API command.

## macOS inspection

Current native client identity:

```bash
mdls -name kMDItemVersion -name kMDItemCFBundleIdentifier /Applications/Telegram.app
```

Peekaboo 4 uses `app list`, `window list`, and `see`; older `list apps`,
`list windows`, and `image` commands are stale.

```bash
peekaboo permissions status --json
peekaboo app list --json
peekaboo see --app Telegram --mode window --retina --no-elements --path /tmp/telegram-rich-audit.png --json
```

Keep the screen awake during an approved visual audit. Capture the message at
Retina resolution and crop/zoom the exact bubble before judging baseline or
spacing differences.

## Current boundaries

- The default Markdown path sends typed rich blocks when rich messages are on;
  captions remain legacy Telegram HTML and cap at 1024 characters.
- Current rich Markdown and legacy `textMode: html` are separate rendering
  paths. A whitelist statement about one path does not govern the other.
- Current rich HTML treats `p`, `span`, and `div` as transparent containers;
  they are not dependable visual-spacing controls.
- Reply quotes of our rich bodies may arrive as an unsupported placeholder.
  Preserve message IDs and recent conversation context instead of relying on
  quoted body text.
- Copy Text stays capability-gated. Consult the dated result in the
  [rendering matrix](rich-rendering-matrix.md); treat any future support as
  unproven until the active schema and a live clipboard canary both pass.

## Recording a result

Append only the durable outcome to `rich-rendering-matrix.md`:

```text
Date · OpenClaw version · rich ON/OFF · client/version/build · chat surface
Message IDs · exact markup lane · expected result · observed result · screenshot
```

Do not duplicate the result here or promote it to a production rule until the
canary isolates the behavior.
