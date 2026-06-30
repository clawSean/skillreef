---
name: shop-agent
description: "Shop or reorder from Amazon/retailers: compare products, check prices, add to cart, and prepare checkout. Use web-use as needed; always stop before purchase."
---

# Shop Agent

Browser-driven shopping assistant. Searches for products, adds to cart, and walks through checkout — but **always stops for user confirmation before placing an order**.

## Prerequisites

- **VPS headless browser (primary)**: Playwright 1.59.1 + Chromium on the VPS. Available for search, comparison, price checks, and cart-building on sites that don't require login.
- The `web-use` skill for product/pricing/site-data research and browser context routing: lightweight retrieval, protected extraction, structured APIs, remote extraction sessions, cart, checkout, order history, Prime/login state, CAPTCHA/2FA, or the user's device/session.
- For full functionality (saved addresses, payment methods, Prime): an attached logged-in browser session on your own machine (requires an OpenClaw browser node connected and `gateway.nodes.browser.mode: "auto"`)

## Dependency routing

Shop Agent owns the shopping workflow. Do not make the user or future agent choose
a generic web lane. Use `web-use` when the shopping task spans research plus
cart/checkout.

| Shopping need | Route |
|---|---|
| Product discovery, option comparison, reviews, candidate URLs | `web-use`; stay lightweight unless blocked |
| Current price, stock, seller, Prime, coupon, selected variant | Live retailer page is ground truth; use browser/data path that can see the live offer |
| Protected product/history/review data with no human-visible browser need | `web-use` protected extraction |
| Structured fresh Amazon product data / ASIN fields | Site-specific API only when this skill says the credit tradeoff is worth it |
| Add to cart, checkout review, order history, saved address/payment, Prime/login state | `web-use` browser context |
| Keepa/extension-backed Amazon history | `web-use` selects the extension-capable browser lane; this skill decides whether the history is worth using |
| CAPTCHA, 2FA, manual visual confirmation, final purchase gate | `web-use` interactive browser, then stop for user approval |

Common Amazon flow: use `web-use` to research and select candidates with the
lightest viable data path, then use its browser-context lane for the logged-in Amazon cart and
checkout context.

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
| "Reorder [thing I bought before]" | Navigate to order history if logged in |
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

Use `web-use` for browser context and cart/checkout routing:

- **Just browsing/comparing/price-checking** → **VPS headless browser (default)**. Always available, no user intervention needed.
- **Logged-in session needed** (checkout, order history, Prime pricing) → attached user browser if Mac node is available. If not, tell user what's needed.
- **Adding to cart on Amazon without login** → VPS headless can browse and research, but cart/checkout requires a logged-in session.

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
- If login is required and using managed browser: tell the user they need to log in manually, pause
- If 2FA prompt appears: notify user, pause
- If login session expires mid-flow: notify user, pause

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
