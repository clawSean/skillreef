# Browser control modes

## 2 x 2 model

This matrix describes the conceptual space, not guaranteed availability. Any given deployment may support only some cells.

| Context | User device | Agent device |
|---|---|---|
| Fresh browser | Open a clean browser/tab on the user's machine, if supported | Open a clean browser/tab on the agent's machine, if supported |
| Existing browser | Attach to the user's already-open browser/tab, if supported | Usually not a normal product mode |

## Preferred plain-English labels

- Fresh browser
- Your current browser
- On your device
- On my side

## Example interpretations

- "Open a browser and check this" -> if available, fresh browser on agent device
- "Open this on my Mac" -> if available, fresh browser on user device
- "Look at my tab" -> if available, existing browser on user device
- "Use my current logged-in page" -> if available, existing browser on user device
- "Do it yourself in a browser" -> if available, fresh browser on agent device

## Internal mapping hints

Keep these internal unless discussing implementation. These are examples, not universal requirements.

- fresh + user device -> node/browser relay + managed profile
- fresh + agent device -> host/sandbox managed browser
- existing + user device -> attached user browser/profile/session

## Non-browser fallback rule

Before selecting a browser mode, ask:
1. Does this task actually need rendering, tabs, cookies, or interaction?
2. Could web search, direct HTTP retrieval, or a lighter automation path solve it?
3. Is the requested browser mode even available in this environment?

If a lighter path works, skip full browser-control framing. If the desired browser mode is unavailable, explain the constraint and choose the closest acceptable fallback.
