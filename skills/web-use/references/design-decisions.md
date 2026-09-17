# Web Routing Design Decisions

Portable rationale only; machine/account state and private chat history stay in
the local AID floor and local provider/proof registries.

- Choose a category before a provider so provider changes remain contained.
- Allow specialist leapfrogs when task shape proves they fit; do not force cheap
  lanes to fail first.
- Keep native search/fetch as the fast public discovery/read path and route
  source-heavy synthesis early to a cited-research specialist.
- Keep authenticated state local by default; hosted extraction is public-only
  unless explicit domain policy and user authorization say otherwise.
- Treat the user's shared tab as explicit/watch-required/exceptional-sensitivity
  context, never a generic fallback. Unless explicitly selected, exhaust
  relevant self-sufficient local-app and GUI/computer-use lanes before asking
  the user to initiate sharing.
- Separate portable policy from local installation, login, balance, profile,
  and dated proof state.
- Domain skills own intent/account/action policy; `web-use` owns transport and
  fallback; mechanic skills operate only after routing selects their lane.
- A provider failure is not overall incapability. Exhaust relevant proven lanes
  or identify the exact human/authority/risk gate before declaring blockage.

These decisions were hardened from prior capability proofs and independent
architecture/regression reviews on 2026-09-16. New evidence changes the narrow
registry or proof ledger first; portable policy changes only when the evidence
establishes a durable rule.
