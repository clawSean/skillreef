# Purchase monitoring handoff

Use `../purchase-log.jsonl` as the one append-only purchase and order-state
ledger across retailers. Do not create a separate active-order list or copy
orders into memory files.

After verified submission, append one `order_submit` JSON object with:

- `timestamp`, `retailer`, `action`, `status`, and a stable `order_key`;
- privacy-safe `items` containing title and quantity;
- verified `order_number` or `purchase_id` when available;
- `checkout_delivery_estimate`, tracking number/URL, and carrier when known;
- `requested_by`, `chat_id`, and `message_id` when available;
- `monitor_delivery: true` unless the user explicitly declines follow-through.

Build `order_key` as `<retailer>:<order_number>` when an order number exists,
otherwise `<retailer>:<purchase_id>`. If neither exists, use the retailer plus
the confirmation timestamp and mark the identifier unverified. Never store a
full street address, payment number, credential, or secret.

When later checking an order, append an `order_status` object with the same
`order_key` only when the verified state materially changes: `confirmed`,
`shipped`, `out_for_delivery`, `delivered`, `delayed`, `exception`, `canceled`,
or `refunded`. Include the new ETA or tracking fields when they changed. Do not
append repeated observations of the same state and ETA.

Heartbeat owns notification state. The ledger records facts; it does not record
or schedule repeated countdown reminders.
