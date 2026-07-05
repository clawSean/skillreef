---
name: "shop-agent"
description: "Shop/reorder from Amazon/retailers via the VPS logged-in browser (primary); compare, add to cart, prepare checkout. Stop before purchase."
---

# Shop Agent

Browser-driven shopping assistant. Searches for products, adds to cart, and walks through checkout — but **always stops for user confirmation before placing an order**.

## Browser lanes (READ FIRST — corrects a recurring mistake)

- **VPS managed `openclaw` browser = PRIMARY, and it is already logged in.** The VPS-local headless Chrome (`profile="openclaw"`, `target="host"`, CDP `:18800`, persistent `userDataDir` `~/.openclaw/browser/openclaw/user-data`) holds a durable signed-in Amazon session as Jared (ships to San Diego 92130). It handles search, compare, price checks, **and logged-in cart/checkout/order-history**. Use it first for everything.
- **Do NOT assume "logged in" means the user's Mac browser.** The Mac node browser (`clawnode-arc`, CDP `:18802`) is a **strictly compatibility fallback**: it is normally logged into nothing, and its bridge is flaky. Use it only when (a) the VPS session is actually logged out / blocked, or (b) JPop explicitly wants to co-interact in a visible browser live.
- Never conclude "the VPS can't touch your cart." It can. Verify login state on the live page instead of guessing from lane.

## Prerequisites

- **VPS managed `openclaw` browser (primary, logged in)**: headless Chromium on the VPS with a persistent, Amazon-authenticated profile. Use for search, comparison, price checks, cart-building, and checkout review.
- The `web-use` skill for product/pricing/site-data research and browser-context routing: lightweight retrieval, protected extraction, structured APIs, remote extraction sessions, cart, checkout, order history, Prime/login state, CAPTCHA/2FA.
- **Mac node browser (fallback only)**: an attached logged-in session on JPop's Mac (requires an OpenClaw browser node connected and `gateway.nodes.browser.mode: "auto"`). Not assumed logged in; use only when the VPS lane fails or live co-interaction is wanted.

## Dependency routing

Shop Agent owns the shopping workflow. Do not make the user or future agent choose
a generic web lane. Use `web-use` when the shopping task spans research plus
cart/checkout.

| Shopping need | Route |
|---|---|
| Product discovery, option comparison, reviews, candidate URLs | `web-use`; stay lightweight unless blocked |
| Current price, stock, seller, Prime, coupon, selected variant | Live retailer page is ground truth; use the VPS `openclaw` browser to read the live offer |
| Protected product/history/review data with no human-visible browser need | `web-use` protected extraction |
| Structured fresh Amazon product data / ASIN fields | Site-specific API only when this skill says the credit tradeoff is worth it |
| Add to cart, checkout review, order history, saved address/payment, Prime/login state | VPS `openclaw` browser (logged in) via `web-use` browser context |
| Keepa/extension-backed Amazon history | `web-use` selects the extension-capable browser lane; this skill decides whether the history is worth using |
| CAPTCHA, 2FA, manual visual confirmation, final purchase gate | VPS `openclaw` browser first; escalate to the Mac fallback only if the VPS lane is blocked, then stop for user approval |

Common Amazon flow: use `web-use` to research/select candidates with the
lightest viable data path, then drive the logged-in VPS `openclaw` browser for the
Amazon cart and checkout review.

## Core safety rule

**Never click "Place your order" or equivalent without explicit user approval.**

Before any purchase confirmation:
1. Present a summary: item(s), quantity, price, shipping estimate
2. Send as Telegram buttons: ✅ Place Order / ❌ Cancel
3. Wait for tap
4. Only proceed on explicit ✅

This rule has no exceptions.

## Workflow

### Step 1: Understand the request

Classify what the user wants:

| Request type | Action |
|---|---|
| "Buy me [specific product]" | Search and navigate directly |
| "Order [category/vague item]" | Search, present 2-3 options, let user pick |
| "Reorder [thing I bought before]" | Navigate to order history (VPS browser is logged in) |
| "Add [item] to cart" | Search, add, confirm — do not proceed to checkout |
| "Check price of [item]" | Search, report price — no cart action |
| "Compare [items]" | Search both, present side-by-side summary |

### Step 2: Select data path

Use `web-use` when data retrieval matters:

- **Casual browsing/research** → prefer free/manual/lightweight paths first
- **Amazon research for a cart** → collect candidates/ASINs/prices first, then hand the chosen item to the browser/cart step
- **Protected history or hard extraction** → use protected-site routing, currently Browserless first and TinyFish Browser API / CDP second
- **Structured Amazon lookup** → do not default to Rainforest; use it only on request or after proposing the credit tradeoff

### Step 3: Select browser mode

- **Anything on Amazon (browse, compare, price, cart, checkout review, order history)** → **VPS `openclaw` browser (default, logged in).** No user intervention needed.
- **VPS session logged out / blocked, or JPop wants to co-interact live** → Mac node browser fallback. Confirm it is logged in first; it usually is not.
- **Never** tell the user the cart is untouchable without first verifying login state on the live VPS page.

### Step 4: Navigate the retailer

Follow the retailer-specific procedure. See `references/amazon.md` for Amazon.

General pattern:
1. Open retailer site
2. Search for product
3. Select best match (or present options)
4. Add to cart
5. Proceed to checkout
6. **STOP — present summary and wait for approval**
7. On approval: complete purchase
8. Confirm order placed, share order number if visible

### Step 5: Report back

After order or cancellation:
- Confirm what happened
- Share relevant details (order number, estimated delivery, total charged)
- If cancelled: leave items in cart or remove, based on user preference

## Login handling

- **Never store, request, or handle login credentials**
- The VPS `openclaw` browser is expected to be logged in; if it is logged out mid-flow, notify the user and pause (do not attempt to re-auth silently)
- If 2FA prompt appears: notify user, pause
- If a CAPTCHA / "are you a robot" page appears: notify user, pause

## When not to use this skill

- Price lookup only with no purchase intent → web search is lighter
- Product research / reviews → web search or Perplexity is better
- Tracking an existing order → this skill doesn't cover post-purchase yet

## Supported retailers

| Retailer | Reference file | Status |
|---|---|---|
| Amazon | `references/amazon.md` | 🟡 Building |
| Target | `references/target.md` | ⬜ Future |
| Walmart | `references/walmart.md` | ⬜ Future |

## Reference

- `references/amazon.md` — Amazon-specific navigation procedure
- `references/safety.md` — Checkout confirmation rules and edge cases
- `references/price-history.md` — optional Rainforest usage and price-history guidance (not default, credit-sensitive)
