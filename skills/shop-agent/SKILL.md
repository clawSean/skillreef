---
name: "shop-agent"
description: "Research and prepare purchases through live-verified Mac browser state and a hard purchase gate."
---

# Shop Agent

Use for product research, retailer/eBay live data, cart work, checkout
preparation, and purchase follow-through. Always stop before placing an order.

## Current browser contract

- The managed OpenClaw browser is Mac-local on ClawPop.
- Login, cart, Prime, order-history, saved-address, and payment state are never
  inferred from the former VPS profile. Verify the live page first.
- Use an attached user-visible browser only when co-interaction, extension state,
  CAPTCHA/2FA, or the user's current tab is required.
- Load `web-use` for browser/data-path routing.

## Route by need

| Need | Route |
|---|---|
| Product discovery, reviews, candidate links | `web-use`; start with search/fetch |
| Current price, stock, seller, coupon, selected variant | Live retailer page |
| Structured Amazon/retailer data | Site API only when the domain reference approves cost/fit |
| Live eBay search/item/auction/shipping/seller/end time | `ebay-readonly` MCP when enabled; otherwise public live page |
| eBay sold/completed history or bid/photos/descriptions audit | Authenticated Product Research/live browser if currently available |
| Cart, checkout review, order history, account state | Mac managed browser after live login verification |
| Keepa or another extension | Verified extension-capable browser context |
| CAPTCHA, 2FA, manual review | Pause for the user or switch to a visible co-interaction lane |
| Final order placement | Explicit approval gate below |

Public ended eBay pages are non-exhaustive. The eBay MCP provides public
read-only data only when enabled; it does not bid, sell, pay, or access an
account.

## Hard purchase gate

Never click “Place your order,” “Buy now,” “Confirm purchase,” or equivalent
without explicit user approval for that exact checkout.

Before placement:

1. Present item, quantity, price, shipping, tax/fees, delivery estimate, and
   selected address/payment labels without exposing sensitive details.
2. Ask for a clear confirm/cancel choice using the current channel's safest UI.
3. Wait for explicit confirmation.
4. Re-read the final checkout total and selections.
5. Place only if they still match; otherwise stop and report the drift.

Adding to cart is allowed when requested; it is not purchase approval.

## Workflow

### 1. Classify

- Specific product → find exact match.
- Vague category → present two or three good options.
- Reorder → use order history only after current login verification.
- Add to cart → add and confirm; do not advance the purchase gate.
- Compare/check price → report without cart mutation unless requested.
- Track eBay auction → read-only MCP/live page plus finalist browser audit.
- Sold-history request → authenticated Product Research when available; label
  public fallback evidence as incomplete.

### 2. Select the lightest data path

- Search/fetch for public research.
- Live page for current offer truth.
- Protected extraction only when ordinary retrieval fails.
- Paid/credit APIs only after their tradeoff is justified.
- Browser only when rendering, login, cart, account, or visual proof matters.

### 3. Verify browser context

1. Confirm the target profile is available.
2. Open the retailer and verify login/account state from the live page.
3. If signed out, follow the retailer reference's approved session-repair path.
4. Never print/log credentials or pass secrets in process arguments.
5. Pause for CAPTCHA or 2FA.
6. Do not claim a cart/order-history capability until the page proves it.

### 4. Navigate and verify

1. Open retailer.
2. Search/select exact variant and seller.
3. Confirm price, stock, shipping, and return terms.
4. Add to cart when requested.
5. Review checkout.
6. Stop at the hard purchase gate.
7. On approval, re-read and place.
8. Report order number/total/delivery only when visible and verified.

## Login handling

- Credentials, when an approved workflow needs them, come from 1Password at
  runtime and never appear in chat, logs, files, or command arguments.
- A signed-out page is a live state fact, not proof that another device is
  logged in.
- Use a visible browser for user-controlled authentication or 2FA.
- Never copy browser profiles or account credentials to the VPS.

## VPS boundary

The VPS may host public shopping helpers or receive non-sensitive webhooks, but
it is not the default shopping browser and must not regain personal browser
profiles or broad retail credentials.

## When not to use

- One public price lookup with no purchase intent: ordinary web search is enough.
- General product research with no cart/account work: web research is enough.
- Post-purchase carrier tracking: use the appropriate order/carrier workflow.

## Retailer references

- `references/amazon.md`
- `references/ebay.md`
- `references/safety.md`
- `references/price-history.md`

All retailer references inherit this Mac-first browser contract. Treat any
remaining host-specific claim as drift until current live proof confirms it.
