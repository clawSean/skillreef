# Telegram Rich Message Client Compatibility

Use this reference when Telegram rich-message rendering differs across clients, or when the user says a current Telegram app does not render rich bodies, tables, collapsibles, buttons, or other Bot API 10.1 features as expected.

Keep `SKILL.md` focused on send-time authoring rules. Put install audits, client/version findings, and debug procedures here.

## Core Rule

`channels.telegram.richMessages: true` is an OpenClaw send-path feature, but final display still depends on the receiving Telegram client.

If a rich body renders badly on one client:

1. Do not assume OpenClaw failed to send.
2. Check whether the issue follows the client, chat type, or markup shape.
3. Mirror operationally important content in plain prose or compact lists.
4. Prefer markdown-pipe tables over raw HTML tables.
5. Pick the right fallback for the failure you actually see: client RENDERS rich bodies but collapses newlines (stale renderer) → explicit rich-body blocks (`<p>`, `<ul><li>`, `<br>`); client shows the `not supported in your version of Telegram` fallback → drop the rich body entirely and send normal Telegram formatting with literal line breaks and text bullets (structural `p`/`ul`/`br` are not whitelisted on that path and leak as literal tags).

## JPop Mac Audit — 2026-07-06

Trigger: JPop reported that computer Telegram could not render some rich messaging features, despite showing no available update.

Findings:

- Installed app on <YourMacNode>: `/Applications/Telegram.app`.
- Bundle id: `ru.keepcoder.Telegram`.
- Version: `12.8`.
- Build: `282010`.
- App Store receipt present.
- No universal Telegram Desktop bundle found (`org.telegram.desktop`).
- No `~/Library/Application Support/Telegram Desktop` support dir found.

Interpretation:

- The installed app is the native/App Store macOS Telegram client.
- "No update available" can mean "current native macOS client," not "best/current universal Telegram Desktop rich-message renderer."
- The universal Telegram Desktop release line (`6.9.x`) explicitly shipped rich text formatting for bots plus follow-up rich-message display/layout fixes.
- Native macOS 12.8 release notes around the same release are generic "bug fixes/minor improvements," even though they link to the broad Telegram rich-text announcement.

Recommendation for this specific case:

- Install/run the universal Telegram Desktop app from `desktop.telegram.org` alongside the native macOS app when comparing rich-message behavior.
- Keep the native app if JPop prefers it for ordinary use, but do not use its update status as proof that rich-message rendering is complete.

## Useful Checks

Mac app identity:

```bash
for p in /Applications/Telegram.app /Applications/Telegram\ Desktop.app "$HOME/Applications/Telegram.app" "$HOME/Applications/Telegram Desktop.app"; do
  if [ -d "$p" ]; then
    echo "APP=$p"
    /usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$p/Contents/Info.plist" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Print :CFBundleVersion" "$p/Contents/Info.plist" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$p/Contents/Info.plist" 2>/dev/null || true
    /usr/bin/mdls -name kMDItemVersion -name kMDItemAppStoreHasReceipt -name kMDItemLastUsedDate "$p" 2>/dev/null || true
  fi
done
```

Universal Desktop search:

```bash
mdfind "kMDItemCFBundleIdentifier == 'org.telegram.desktop'" 2>/dev/null || true
mdfind "kMDItemDisplayName == 'Telegram Desktop'" 2>/dev/null || true
ls -ld "$HOME/Library/Application Support/Telegram Desktop" 2>/dev/null || true
```

## Sources Checked On 2026-07-06

- Telegram Bot API changelog: Bot API 10.1 added Rich Messages on 2026-06-11.
- Telegram launch post: "Smartwatch Apps, Rich Text for Bots, AI Guardians for Groups, and Much More."
- Telegram Desktop release notes: 6.9 introduced rich text formatting for bots; 6.9.1 and 6.9.2 included rich-message layout/display fixes.
- Telegram Stable Releases feed: native macOS 12.8 build 282010 listed as a 2026-06-10 native client update with generic bugfix notes and the broad launch-post link.

## Known OpenClaw-Side Compatibility Notes

- On the calibrated post-2026-07-19 iOS client, literal newlines render correctly in rich mode (2026-07-20 rebase — plain markdown is the house default). Older/unverified clients may still collapse them; use explicit rich-body HTML blocks (`<p>`, `<ul><li>`, `<br>`) only after observing that failure on the specific surface.
- Raw HTML tables are path-sensitive and unsafe for group-visible operator cards.
- Markdown-pipe tables are the preferred table path while `richMessages: true` is enabled.
- Inbound replies to our rich bodies may arrive as `[unsupported Telegram rich_message received]`; use message ids instead of relying on quoted body content.
