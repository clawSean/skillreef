# Price History and Structured Amazon Data

Use Rainforest for **structured Amazon data**, not as the default path and not as a true price-history solution.

## Credentials

Fetch at runtime only:

```bash
op read "op://<vault>/Rainforest API Key/password"
```

Never hardcode the key.

## When to use Rainforest

Use Rainforest only when:
- the user explicitly asks for it, or
- you propose spending a credit because clean structured Amazon data will materially help

Good fits:
- search results with ASINs
- structured product detail lookup
- fresh price confirmation before presenting a buy choice
- final price re-check before checkout

Bad fits:
- casual product browsing when a free/manual path is enough
- true historical price research
- protected-site extraction outside Amazon

## Base endpoint

```text
https://api.rainforestapi.com/request
```

## Product lookup by ASIN

```bash
curl "https://api.rainforestapi.com/request?api_key=<KEY>&type=product&asin=<ASIN>&amazon_domain=amazon.com"
```

Useful return fields: title, price, rating, review count, brand, variants, availability, Prime eligibility.

## Search

```bash
curl "https://api.rainforestapi.com/request?api_key=<KEY>&type=search&search_term=<QUERY>&amazon_domain=amazon.com"
```

Useful return fields:
- `title`
- `price.value`
- `rating`
- `ratings_total`
- `is_prime`
- `is_sponsored`
- `asin`

## Default handling when Rainforest is used

- Filter out `is_sponsored: true` by default
- Prefer highly rated organic results
- Use ASIN product lookup to confirm fresh pricing before a serious buy step

## Price history

Rainforest does **not** provide the real historical price view we want.

For true history:
- try CamelCamelCamel or similar sources
- if protected, route through `web-use` protected-site logic
- if the fallback needs login, CAPTCHA/2FA, a visible browser, or an extension-capable browser, use `web-use` browser-context routing
- current canonical VPS order: **Browserless first** (`/stealth/bql` or `/unblock`), then **TinyFish Browser API / CDP session** if needed
- do **not** assume TinyFish Agent API is the right path for CCC-style history pages
- if still blocked, say so plainly and offer manual/browser-assisted checking

If reusable execution helps, `web-use` ships bundled helpers for both working VPS-side lanes:
- `skills/web-use/scripts/browserless_extract.py`
- `skills/web-use/scripts/tinyfish_browser_extract.py`

## Credit note

- 1 credit per request
- Credit-sensitive, do not treat as the default browsing path
- Use deliberately, not automatically
