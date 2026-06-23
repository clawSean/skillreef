---
name: shop-agent
description: "Shop or reorder from Amazon/retailers: compare products, check prices, add to cart, and prepare checkout. Use browser automation/web-extract as needed; always stop before purchase."
---

# Shop Agent

Browser-driven shopping assistant. Searches for products, adds to cart, and walks through checkout — but **always stops for user confirmation before placing an order**.

## Prerequisites

- **VPS headless browser (primary)**: Playwright 1.59.1 + Chromium on the VPS. Available for search, comparison, price checks, and cart-building on sites that don't require login.
- The `browser-control` skill for mode routing when login/checkout requires the user's device
- The `web-extract` skill should be used when product/pricing/site data needs a backend choice (lightweight, protected, API, or interactive)
- For full functionality (saved addresses, payment methods, Prime): an attached logged-in browser session on your own machine (requires an OpenClaw browser node connected and `gateway.nodes.browser.mode: "auto"`)

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

Use the `web-extract` skill when data retrieval matters:

- **Casual browsing/research** → prefer free/manual/lightweight paths first
- **Protected history or hard extraction** → use protected-site routing, currently Browserless first and TinyFish Browser API / CDP second
- **Structured Amazon lookup** → do not default to Rainforest; use it only on request or after proposing the credit tradeoff

### Step 3: Select browser mode

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
