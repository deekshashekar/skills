---
name: agent-web-compatibility
description: Audit and redesign websites for dual consumption — optimised for both human visitors and AI agents acting on their behalf. Use this skill when someone wants to make a website agent-compatible, improve how AI assistants discover or recommend their site, build trust signals for AI-mediated transactions, or ensure their booking/reservation flow works for AI agents. Triggers on phrases like "agent-friendly website", "AI can't book on my site", "make my site work with AI assistants", "optimise for AI agents", "dual consumption", "agentic web", "my site isn't getting picked by AI", or any request to audit or redesign a website for AI compatibility. Also triggers when building new websites for clinics, restaurants, salons, local e-commerce, or event booking where agentic discovery and completion is a goal.
license: MIT
metadata:
  author: antstackio
  version: "1.0.0"
---

# Agent Web Compatibility

Audit and redesign websites so they perform well for **both** human visitors and AI agents acting on a user's behalf.

When an agent is asked _"find me a dermatologist near Indiranagar available this Thursday"_ it doesn't click buttons or read hero images — it parses structured data, verifies trust signals, and picks the option it can confidently complete. This skill addresses all three stages of that decision.

**Best fit:** independent clinics, restaurants, salons, local e-commerce, event venues. Not for chains already integrated into aggregator APIs at scale.

---

## The Three-Layer Framework

```
1. DISCOVERABILITY  — Can the agent find and understand you?
2. PREFERABILITY    — Does the agent trust you enough to recommend you?
3. COMPLETABILITY   — Can the agent finish the transaction without breaking?
```

Work through layers in order. Read the vertical reference file before auditing.

---

## Layer 1: Discoverability

**Schema.org JSON-LD** — highest-impact change. Every entity needs: `name`, `address` (PostalAddress), `telephone`, `geo`, `url`, `openingHoursSpecification`. Vertical-specific required fields are in the reference files.

**Data freshness** — check `dateModified` on all key pages, use `specialOpeningHoursSpecification` for exceptions, set `temporarilyClosed` when the business is shut. Stale data causes agents to deprioritise you.

**llms.txt** — place at domain root with: business description, key page paths, booking policy summary, trust signals. Signals intentionality to AI crawlers.

**Entity consistency** — business name, address, phone, and category must be identical across Google, Maps, Justdial, Sulekha, and all aggregator listings. Inconsistency fractures the entity graph.

---

## Layer 2: Preferability

Agents evaluate verifiable signals, not marketing copy. Every vertical has specific trust credentials — see the reference file. Cross-vertical requirements:

- `aggregateRating` with `ratingCount` present and sourced
- Menu / service list with prices crawlable (not in images or PDFs)
- Booking and cancellation policy in plain prose on the page
- `dateModified` accurate on all key pages
- Author bylines with `author` schema on blog/FAQ content

---

## Layer 3: Completability

**Hostile barriers to remove:**

- CAPTCHA on booking forms → replace with honeypot + IP rate limiting
- Session timeout < 30 minutes → extend to minimum 30 minutes
- OTP-only flows → always offer email confirmation as fallback
- JS-only forms with no HTML fallback → inaccessible to many agents
- Third-party booking redirects mid-flow → embed widgets in-page
- Price shown at checkout differs from listing → taxes must be shown upfront

**Form fields:** every input needs an explicit `label`, semantic `name`/`id` (`guest_count` not `field_1`), and `autocomplete` where relevant.

**Confirmation payload** must include in plain parseable text: business name, date/time (unambiguous format), what was booked, cancellation policy, and a unique booking reference ID.

**Adversarial booking flow tests** — run these against any booking form before marking Layer 3 complete:

- **Double-submit**: click the submit button twice rapidly → expect a single confirmation (no duplicate booking)
- **Empty submission**: submit with all fields blank → expect a validation error, not a crash or silent failure
- **Keyboard-only**: Tab through every field, submit with Enter → the full flow must complete without a mouse
- **Long input**: paste 200 characters into a name or notes field → expect truncation or a clear error, not a crash
- **OTP fallback**: trigger the OTP step, then verify an email confirmation alternative is offered

For eval recipes and screenshot capture on failures, read `references/verification-protocol.md`.

---

## Audit Checklist

Mark each: ✅ Done / ⚠️ Partial / ❌ Missing

**Discoverability**

- [ ] JSON-LD present with correct Schema.org type for vertical
- [ ] `name`, `address`, `telephone`, `geo`, `url` populated
- [ ] Vertical-specific required fields present (see reference file)
- [ ] `openingHoursSpecification` accurate and current
- [ ] `llms.txt` at domain root
- [ ] Entity consistent across all external listings

**Preferability**

- [ ] Vertical trust credentials on page and in schema
- [ ] `aggregateRating` with `ratingCount` present
- [ ] Menu/service list with prices is crawlable
- [ ] `dateModified` present and accurate
- [ ] Booking/cancellation policy in plain prose

**Completability**

- [ ] No CAPTCHA (or agent-safe alternative)
- [ ] Session timeout ≥ 30 minutes
- [ ] All form fields: `label`, `name`, `id`, `autocomplete`
- [ ] OTP flows have email fallback
- [ ] Confirmation contains all 5 required fields
- [ ] Booking reference ID generated

---

## Common Anti-Patterns

| Anti-pattern                      | Why it hurts           | Fix                                       |
| --------------------------------- | ---------------------- | ----------------------------------------- |
| Menu as image or PDF              | Agents can't read it   | HTML menu with JSON-LD `hasMenuItem`      |
| "Call to book" only               | Agents can't call      | Add online booking or callback form       |
| Hours in image format             | Agents miss changes    | Use `openingHoursSpecification`           |
| Generic page titles               | Weak entity signal     | `[Business] — [Service] — [Area]`         |
| Mixed name spellings              | Fractures entity graph | Standardise across all touchpoints        |
| Availability always "open"        | Destroys trust         | Real-time or manually updated status      |
| Reviews only on third-party sites | Agent can't verify     | `aggregateRating` schema with source link |

---

## Vertical Reference Files

Read the relevant file before auditing — each contains required schema fields, trust signals, JSON-LD examples, and booking flow notes:

- `references/healthcare.md` — clinics, diagnostic labs, doctors
- `references/restaurants.md` — restaurants, cafes, cloud kitchens
- `references/salons.md` — salons, spas, grooming
- `references/ecommerce.md` — local D2C, same-day delivery
- `references/quickcommerce.md` — quick commerce, on-demand delivery

---

## Output Format

Deliver eight artefacts:

1. **Scorecard + AI Discoverability Score** — checklist with ✅ / ⚠️ / ❌ per item, layer scores, and an overall AI Discoverability % (0–100). The score reflects how likely an AI agent is to find, trust, and complete a task on this site right now. See `references/verification-protocol.md` for the scoring formula.

2. **Priority fixes** — top 5 ranked by score impact, each showing the estimated % gain and the reason it moves the score:
   - Fix: _add `geo` coordinates to LocalBusiness JSON-LD_
   - Layer: Discoverability
   - Score impact: +8% (from 34% → 42%)
   - Why: without `geo`, agents cannot verify physical location — they skip businesses they cannot geoconfirm when answering location-based queries

3. **Schema block** — ready-to-paste JSON-LD for the vertical

4. **llms.txt draft** — ready to upload

5. **Booking flow notes** — specific friction points and fixes from the adversarial booking tests

6. **AEO content brief** — list of question queries to target, with required answer format (paragraph / list / table) and `FAQPage` entries for top 5 questions

7. **GEO content gaps** — missing E-E-A-T signals, weak/missing author schema, unattributed stats, and heading copy that needs rewriting for AI extraction

8. **Audit report + Implementation prompt** — STEP_PASS/STEP_FAIL markers for all 8 verification steps, screenshots for failures, overall score (X/8 passed), and a ready-made prompt at the end that the user can paste directly into Claude Code or any AI assistant to implement all suggested fixes in one shot. See `references/verification-protocol.md` for the report template and prompt format.

Every recommendation must be specific enough for a developer to act on without a follow-up question. Not _"improve structured data"_ — but _"add `hasMenuItem` array with each dish as a `MenuItem` containing `name`, `description`, and `offers.price`"_.

---

## Verification Steps

Each step must emit a structured marker. Use `STEP_PASS|<id>|<evidence>` or `STEP_FAIL|<id>|<expected> → <actual>`. On failure, take a screenshot immediately. For browser eval recipes and screenshot guidance, read `references/verification-protocol.md`.

1. **schema-json-ld** — run the deterministic JSON-LD check; confirm `@type`, required fields, and vertical-specific fields are present

   - `STEP_PASS|schema-json-ld|LocalBusiness JSON-LD found with name, address, telephone, geo, openingHoursSpecification`
   - `STEP_FAIL|schema-json-ld|expected @type: LocalBusiness with geo → geo field missing`

2. **booking-flow** — run the five adversarial booking tests from Layer 3; all must pass

   - `STEP_PASS|booking-flow|double-submit produced single confirmation; keyboard-only completed; OTP fallback present`
   - `STEP_FAIL|booking-flow|double-submit → two confirmation emails sent`

3. **entity-consistency** — Google the business name in quotes; check name, address, and phone match across all results

   - `STEP_PASS|entity-consistency|name/address/phone identical across Google, Maps, Justdial`
   - `STEP_FAIL|entity-consistency|expected consistent address → Justdial shows old address`

4. **freshness** — run the deterministic `dateModified` check; confirm value is within 90 days

   - `STEP_PASS|freshness|dateModified: 2026-03-15 (24 days ago)`
   - `STEP_FAIL|freshness|expected dateModified within 90 days → 2025-07-01 (281 days ago)`

5. **aeo-snippet** — Google the primary service + location query; check for Featured Snippet or People Also Ask appearance

   - `STEP_PASS|aeo-snippet|site appears in Featured Snippet for "dermatologist Indiranagar"`
   - `STEP_FAIL|aeo-snippet|expected Featured Snippet or PAA → site not present in either`

6. **geo-transactional** — ask ChatGPT and Perplexity: _"Find me a [vertical] in [neighbourhood] that [requirement]"_

   - `STEP_PASS|geo-transactional|business recommended by Perplexity with source link`
   - `STEP_FAIL|geo-transactional|expected recommendation → not mentioned by either model`

7. **geo-content** — ask Perplexity the primary question the site's content should answer; check for citation

   - `STEP_PASS|geo-content|site cited as source with link`
   - `STEP_FAIL|geo-content|expected citation → competitor cited instead`

8. **ai-overview** — Google the primary question query; check the AI Overview panel for citation or exclusion
   - `STEP_PASS|ai-overview|site cited in AI Overview for "how to book same-day dermatologist appointment"`
   - `STEP_FAIL|ai-overview|expected AI Overview citation → panel present but site excluded`
