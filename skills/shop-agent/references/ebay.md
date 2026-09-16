# eBay Read-Only Research and Auction Monitoring

## Lane ownership

- **Official `ebay-readonly` MCP:** live public listing discovery and item details through eBay's production APIs. It uses application-token OAuth and exposes only `query_ebay_api` and `call_ebay_api`.
- **Authenticated Product Research or verified Mac browser:** sold history, accepted offers, bid pages, listing photos and descriptions, recent seller activity, and finalist review. Verify the live session; former VPS proof is historical.
- **User:** all bids, offers, checkout, payment, and final purchase decisions. Never automate bidding or sniping.

## Activation gate

The MCP remains disabled until its local 1Password item resolves both
`client_id` and `client_secret`. The owning local provider registry/config maps
the item; this portable reference never names a private vault or item.

If credentials or the MCP are unavailable, use `web-use` and the live eBay page. Do not imply the API is live or that public search results form a complete sales census.

## Live listing workflow

1. Clarify the target configuration, condition, location, return preference, and maximum price.
2. Use `query_ebay_api` to inspect the official endpoint/schema when needed, then `call_ebay_api` for production GET requests only.
3. Capture the item ID, title/configuration, current price, shipping, currency, buying format, seller score, end time, condition, returns, and canonical URL when available.
4. Snapshot meaningful changes for ongoing watches and preserve the valuation/cap rationale in the buy list or project state.
5. Browser-audit finalists for photos, description contradictions, bid history, and recent seller activity.
6. Alert the user with the listing, current price, countdown, risk notes, and one recommended maximum. The user places the bid manually.

For ordinary eBay-protected Mac purchases, do not penalize a listing merely because photos do not prove Activation Lock or MDM status. Verify promptly after delivery and use item-not-as-described protection for misrepresentation.

## Historical valuation

- The Browse API is for live inventory; it is not a complete sold-history source.
- Prefer authenticated eBay Product Research for the three-year sold/completed view.
- If Product Research is unavailable, direct ended pages and search-engine results are useful price anchors only. Say the sample is non-exhaustive.
- Accepted Best Offers may hide the actual transaction price; distinguish visible ask, struck-through price, and confirmed sale price.

## Safety boundary

- Keep the MCP on production, application-token, GET-only access.
- Do not add user OAuth, account, payment, selling, offer, bid, or checkout scopes.
- Never use `PlaceOffer`, scheduled bidding, automatic bidding, or sniping.
- A declined payment method is not a cancellation path.
- The global checkout rule still applies: stop before any final purchase action without explicit approval.
