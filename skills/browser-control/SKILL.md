---
name: browser-control
description: "Decide and structure browser-control work across four distinct modes: fresh browser on the user's device, fresh browser on the agent's device, existing browser on the user's device, and lightweight non-browser alternatives. Use when the user wants browser automation UX/design, asks to open or inspect tabs, needs help distinguishing local vs remote browser behavior, or when a task requires choosing between managed browser, attached user browser, and a lighter option. Treat each mode as capability-dependent, not guaranteed in every deployment. Do not use for plain web search, simple URL lookup, or browser tool usage that is already straightforward and does not need this decision layer."
---

# Browser Control

Treat browser work as two separate questions:
1. **Whose browsing context?** Fresh or existing.
2. **Which device?** User device or agent device.

Keep this distinction explicit. Do not collapse "fresh vs existing" into "local vs remote".

Treat every mode as **conditional on environment support**. Some deployments may support only one device, only fresh sessions, or no browser control at all.

## Quick decision rules

### Use no browser at all when possible
Prefer a lighter tool when the task is really:
- web lookup or link gathering
- text-first page retrieval
- a future non-visual Playwright or HTTP flow that does not need browser-state reasoning
- documentation or API investigation

If the task does not need tabs, rendering, sessions, cookies, or UI interaction, do **not** route it through full browser-control language.

### Hand off to web-extract for server-side data extraction
If the task is really about pulling data from a site, especially protected or
bot-gated pages, structured extraction, Browserless, TinyFish, persistent
extraction sessions, or site-specific data APIs, use `web-extract`.

Browser-control decides **whose browser/context/device/session**. Web-extract
decides **which extraction backend**.

### Use browser-control when the task needs one of these
- deciding between fresh browser vs current browser
- deciding between user device vs agent device
- preserving or using an existing logged-in tab/session
- user-facing UX/design for browser intents
- tab targeting rules such as "my current tab" or "the Stripe tab"
- safety/permission posture for collaborative browsing

## Browser mode model

### 1. Fresh browser on user device
Use for requests like:
- "Open a tab on my Mac"
- "Launch this for me locally"
- "Show it on my machine"

If supported by the deployment, this means a managed/clean browser session appears on the user's device.

### 2. Fresh browser on agent device
Use for requests like:
- "Check this site in your own browser"
- "Do this in the background"
- generic autonomous browser work when no local presence or login is needed

If supported by the deployment, this is often a good default for "open a browser and do X" unless the user asks for local/on-screen behavior.

### 3. Existing browser on user device
Use for requests like:
- "Look at my tab"
- "Use my current browser"
- "Continue from the page I already have open"
- anything requiring the user's live login/session

If supported by the deployment, prefer the active tab by default. If ambiguous, identify likely matches and ask one short clarifying question.

### 4. Existing browser on agent device
Usually ignore as a product concept. It is rarely meaningful in normal UX.

## Intent mapping

Interpret user language by intent, not internal plumbing.

- **"Open a browser"** → if available, usually fresh browser on agent device
- **"Open a new tab on my machine"** → if available, fresh browser on user device
- **"Look at my current tab"** → if available, existing browser on user device
- **"Use my logged-in browser"** → if available, existing browser on user device
- **"Do this yourself in a browser"** → if available, fresh browser on agent device

Use human-facing phrasing in explanations:
- **Fresh browser**
- **Your current browser**
- **On your device**
- **On my side**

Avoid leading with implementation terms like `profile=user`, `profile=openclaw`, CDP, or debugging port unless the user is asking about internals.

## Overhead guardrail

This skill is a **decision/UX layer**, not a mandate to always invoke full browser automation.

When applying this skill:
- keep explanations short unless the user wants architecture depth
- do not wrap ordinary web search in browser-control ceremony
- do not force every future Playwright-style action through the full 2x2 model if the task is just "click this button in the managed browser"
- only surface the matrix when ambiguity, product design, or routing choice actually matters

## Recommended defaults

- When supported, default generic browser tasks to **fresh browser on agent device**
- When supported, default "my tab/current page/already open" tasks to **existing browser on user device**
- Prefer **no browser** when lighter tools can finish the job
- Fall back gracefully when a requested mode is unavailable, and say which capability is missing
- Ask a clarifying question only when the requested target is truly ambiguous or a wrong choice would be costly

## Intent-to-tool posture

Use this skill to choose the right level of interaction:

| Need | Preferred approach |
|---|---|
| Search, links, summaries, quick facts | lightweight non-browser path |
| Open or inspect a specific page visually | browser path if available |
| Continue from a user's existing tab/session | attached existing-browser path if available |
| Product or UX reasoning about browser modes | this skill |

## Reference

For a compact matrix and phrasing guide, read `references/modes.md`.
