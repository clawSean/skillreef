# Amazon — Navigation Procedure

Step-by-step browser automation guide for Amazon shopping.

## Search for a product

1. Navigate to `https://www.amazon.com`
2. Locate the search bar (usually `#twotabsearchtextbox` or equivalent)
3. Type the search query
4. Submit search
5. Wait for results page to load

## Select a product

From search results:
1. Scan the results list for relevant matches
2. Prefer results with:
   - High rating (4+ stars)
   - Significant review count
   - Prime eligibility (if user has Prime)
   - Reasonable price
3. If user specified exact product: find closest match
4. If user was vague: pick top 2-3 candidates, present summary to user with buttons

### Product summary format

For each candidate, report:
- Product name (short)
- Price
- Rating + review count
- Prime eligible (yes/no)
- Estimated delivery

## Add to cart

1. Click into the product detail page
2. Verify correct item (title, price, variant/size/color if applicable)
3. Check for variant selectors (size, color, quantity) — select as specified or ask
4. Click "Add to Cart"
5. Wait for cart confirmation
6. If user only asked to add to cart: stop here, confirm

## Proceed to checkout

1. Click "Proceed to checkout" or navigate to cart
2. Verify shipping address (report to user)
3. Verify payment method (report last 4 digits only, never full card)
4. Verify order total including tax and shipping
5. **STOP HERE**

## Checkout confirmation gate

Present via Telegram buttons:

```
🛒 Amazon Order Summary

Item: [product name]
Price: $XX.XX
Shipping: [method + estimate]
Total: $XX.XX
Ship to: [city, state]

Place this order?
```

Buttons:
- ✅ Place Order
- ❌ Cancel

**Do not proceed without explicit ✅ tap.**

## After order placed

1. Capture order confirmation number if visible
2. Capture estimated delivery date
3. Report both to user
4. Optionally: screenshot confirmation page

## Common edge cases

- **Item out of stock:** Report, suggest alternatives
- **Price changed since search:** Report new price, re-confirm
- **Add-on item (requires $25 minimum):** Inform user
- **Subscribe & Save default selected:** Deselect, use one-time purchase
- **Gift card / promo prompt:** Skip unless user requested
- **CAPTCHA:** Notify user, pause for manual solving
- **"Are you a robot" page:** Notify user, pause
