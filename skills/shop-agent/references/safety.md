# Checkout Safety Rules

## Core principle

The agent assists with shopping but the **user makes the purchase decision**. No exceptions.

## Mandatory confirmation gate

Before any action that spends money:
1. Present full order summary (items, price, shipping, total, destination)
2. Use Telegram inline buttons for approval
3. Wait for explicit ✅ tap
4. Only then click the final purchase button

## What counts as a purchase action

- "Place your order" on Amazon
- "Complete purchase" on any retailer
- "Submit order"
- "Buy now" / "1-click order" — **especially dangerous, skip 1-click entirely**
- Any button that charges a payment method

## What does NOT require confirmation

- Adding to cart (reversible)
- Searching for products
- Comparing prices
- Navigating product pages

## Credential handling

- Never ask for passwords or payment details
- Never type credentials into any field
- If login is needed: pause and tell the user to log in manually
- Report payment method by last 4 digits only ("Visa ending 1234")
- Never screenshot or capture full payment/address details

## 2FA and CAPTCHA

- If a 2FA prompt appears: notify user, pause, wait for them to complete it
- If CAPTCHA appears: notify user, pause
- Do not attempt to solve CAPTCHAs

## Session safety

- If the browser session appears logged into someone else's account: STOP immediately, notify user
- If address or payment method looks wrong/unfamiliar: flag it before proceeding
- If order total seems unexpectedly high: flag it

## Failure handling

- If checkout fails: report the error, do not retry automatically
- If payment declines: report, do not retry with different payment
- If page hangs or times out: report, offer to retry from cart

## One-click buy

- **Never use 1-click buy**, even if available
- Always go through the full checkout flow so the user can review before purchase
- If 1-click is the only visible option, navigate to cart instead
