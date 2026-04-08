# Verification Protocol

Supporting detail for the eight verification steps in SKILL.md. Load this file when running a live audit with browser access.

---

## Assertion Format

Every verification step emits exactly one marker:

```
STEP_PASS|<step-id>|<evidence>
STEP_FAIL|<step-id>|<expected> → <actual>|<screenshot-path>
```

- `step-id`: matches the step names in SKILL.md (e.g. `schema-json-ld`, `booking-flow`)
- `evidence`: what you observed that proves the step passed — element ref, eval result, URL, text content
- `expected → actual`: what should have happened vs what did
- `screenshot-path`: path to screenshot captured at the moment of failure (failures only)

---

## Screenshot Capture on Failure

Take a screenshot immediately when a step fails — capture the broken state, not after recovery.

```bash
mkdir -p .context/agent-audit-screenshots
# Save as: .context/agent-audit-screenshots/<step-id>.png
```

Include the path in the STEP_FAIL marker:
```
STEP_FAIL|form-labels|expected label for every input → input#guest_count has no label|.context/agent-audit-screenshots/form-labels.png
```

---

## Deterministic Browser Eval Recipes

Run these with `browse eval` (or equivalent). They return structured data, not visual judgment.

### 1. JSON-LD presence and fields (`schema-json-ld`)

```js
Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
  .map(s => {
    try { return JSON.parse(s.textContent); } catch(e) { return null; }
  })
  .filter(Boolean)
  .map(d => ({ type: d['@type'], hasName: !!d.name, hasAddress: !!d.address, hasTelephone: !!d.telephone, hasGeo: !!d.geo, hasUrl: !!d.url, hasHours: !!d.openingHoursSpecification }))
```

Pass condition: at least one result where `type` matches the vertical, and all required boolean fields are `true`.

### 2. Form label coverage (`booking-flow` / form labels)

```js
Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="submit"])'))
  .map(i => ({
    id: i.id,
    name: i.name,
    hasLabel: !!(i.id && document.querySelector('label[for="' + i.id + '"]')),
    hasAriaLabel: !!(i.getAttribute('aria-label') || i.getAttribute('aria-labelledby'))
  }))
```

Pass condition: every input has `hasLabel: true` or `hasAriaLabel: true`.

### 3. llms.txt accessibility (`schema-json-ld` / discoverability)

```js
fetch('/llms.txt').then(r => ({ status: r.status, ok: r.ok }))
```

Pass condition: `{ status: 200, ok: true }`.

### 4. CAPTCHA detection (`booking-flow`)

```js
({
  recaptcha: document.querySelectorAll('[src*="recaptcha"], [data-sitekey], .g-recaptcha').length,
  hcaptcha: document.querySelectorAll('[src*="hcaptcha"], .h-captcha').length
})
```

Pass condition: both counts are `0`.

### 5. dateModified freshness (`freshness`)

```js
(() => {
  const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
  for (const s of scripts) {
    try {
      const d = JSON.parse(s.textContent);
      if (d.dateModified) {
        const days = Math.floor((Date.now() - new Date(d.dateModified)) / 86400000);
        return { dateModified: d.dateModified, daysAgo: days, fresh: days <= 90 };
      }
    } catch(e) {}
  }
  return { dateModified: null, daysAgo: null, fresh: false };
})()
```

Pass condition: `fresh: true` (within 90 days).

---

## Adversarial Booking Test Steps

Run these in sequence for any booking form. Take a before snapshot, act, take an after snapshot, compare.

### Double-submit
1. Fill all required fields with valid data
2. Click submit twice rapidly (< 500ms apart)
3. Check confirmation: expect exactly one booking reference ID, not two
- PASS: single confirmation message with one reference ID
- FAIL: two confirmation messages, two IDs, or a server error

### Empty submission
1. Navigate to booking form (do not fill anything)
2. Click submit
3. Check response: expect inline validation errors, not a crash or blank page
- PASS: error messages appear on required fields, form stays on page
- FAIL: server error, blank page, or silent failure

### Keyboard-only flow
1. Navigate to booking form
2. Use Tab only to move between fields, type values, use Enter to submit
3. Verify the full flow completes without requiring a mouse click
- PASS: booking confirmed via keyboard alone
- FAIL: any step requires a mouse (e.g. date picker not keyboard-accessible, submit button not reachable via Tab)

### Long input
1. Paste a 200-character string into a name or notes field
2. Submit the form
3. Check response: expect truncation with a clear message, or a validation error
- PASS: graceful truncation or clear error
- FAIL: server error, crash, or data silently corrupted

### OTP fallback
1. Trigger the OTP verification step (e.g. enter phone number)
2. Check the OTP screen: expect a visible "Send to email instead" or equivalent option
- PASS: email fallback option is present and functional
- FAIL: OTP is the only path; no alternative offered

---

## AI Discoverability Score

The score answers: **"What % of the way is this site toward full AI discoverability?"**

### Scoring formula

Three layers, each weighted by how directly it blocks agentic success:

| Layer | Weight | Items | Points per item |
|---|---|---|---|
| Discoverability | 35% | 6 | ~5.8% |
| Preferability | 25% | 5 | 5.0% |
| Completability | 40% | 6 | ~6.7% |

Each checklist item scores: ✅ = full points · ⚠️ = half points · ❌ = 0

**Layer score** = sum of item points in that layer × layer weight  
**Overall score** = sum of all layer scores (0–100%)

### Score interpretation

| Score | Status | Meaning |
|---|---|---|
| 80–100% | Agent-ready | AI agents will find, trust, and complete transactions reliably |
| 60–79% | Partial | Agents can find you but may abandon mid-flow or deprioritise you |
| 40–59% | Weak | Discoverable but significant trust or completion gaps |
| 0–39% | Invisible | Agents are unlikely to recommend or interact with this site |

### Per-item score impact

Use these to populate the "+X%" impact estimate in Priority fixes (artefact #2):

**Discoverability (35% total)**
- JSON-LD with correct `@type`: +10% — without this, agents have no machine-readable entity anchor; they cannot reliably identify what the business is or does
- `name`, `address`, `telephone`, `geo`, `url` all present: +8% — missing any of these breaks the entity signature agents use for geoconfirmation and contact resolution
- Vertical-specific required fields: +6% — agents use vertical fields (e.g. `servesCuisine`, `medicalSpecialty`) to match businesses to intent; missing fields cause mis-categorisation
- `openingHoursSpecification` accurate: +5% — agents reject businesses with stale or absent hours when the query is time-sensitive (e.g. "open now", "available Thursday")
- `llms.txt` at domain root: +4% — signals intentionality to AI crawlers; its absence does not block discovery but reduces crawl priority
- Entity consistency across listings: +2% — inconsistent name/address/phone fractures the entity graph; agents lower confidence scores for ambiguous entities

**Preferability (25% total)**
- Vertical trust credentials in schema: +6% — agents compare verifiable credentials (licence numbers, certifications) when ranking options; unverifiable businesses are deprioritised
- `aggregateRating` with `ratingCount`: +6% — agents use rating signals to rank within a category; no rating = no basis for preference over a rated competitor
- Menu/service list with prices crawlable: +5% — if prices are in images or PDFs, agents cannot surface them in answers or confirm affordability for the user's budget
- `dateModified` present and accurate: +4% — stale `dateModified` (>90 days) signals the business may be inactive; agents deprioritise it for time-sensitive queries
- Booking/cancellation policy in plain prose: +4% — agents need to relay policy to users before confirming a booking; if it's absent, they either hallucinate or abandon

**Completability (40% total)**
- No CAPTCHA (or agent-safe alternative): +8% — CAPTCHA is a hard blocker; an agent cannot solve it and will abandon the flow entirely
- All form fields have `label`, `name`, `id`, `autocomplete`: +8% — agents fill forms by matching field semantics to known data; unlabelled or generically-named fields (`field_1`) cannot be reliably targeted
- Session timeout ≥ 30 minutes: +6% — agents may pause mid-flow to confirm details with the user; a short timeout forces a restart, breaking the transaction
- OTP flows have email fallback: +6% — agents cannot receive SMS OTPs; without an email path, phone-verified flows are completely inaccessible
- Confirmation contains all 5 required fields: +6% — agents parse the confirmation to relay booking details to the user; a missing reference ID or cancellation policy makes the confirmation unusable
- Booking reference ID generated: +6% — without a unique ID, the agent cannot provide the user with a way to manage or cancel the booking

> Note: items marked ⚠️ (partial) give half the listed value. Items that are prerequisites (e.g. JSON-LD must exist before field-level items score) — if the parent is ❌, child items cannot contribute.

---

## Implementation Prompt

Generate this at the end of artefact #8. It must be copy-pasteable — no placeholders left unfilled. Every fix listed in Priority fixes (artefact #2) must appear here as a concrete instruction.

**Format:**

```
I need to implement AI compatibility improvements on [business name]'s website ([URL]).
Current AI Discoverability Score: [X]%. Target after fixes: [Y]%.

Please implement the following changes in order of impact:

**1. [Fix title] — +[X]% impact**
[Exact change: file path if known, code to add/modify, or content to create]

**2. [Fix title] — +[X]% impact**
[Exact change]

...

**Schema to add to <head> of homepage:**
```json
[paste artefact #3 JSON-LD block here]
```

**llms.txt — create at /llms.txt on the domain root:**
```
[paste artefact #4 content here]
```

Start with the schema block — it has the highest single impact. Confirm each change before moving to the next.
```

**Rules for the implementation prompt:**
- All code blocks must be complete and ready to paste — no `[your value here]` gaps
- If a fix requires a specific file path, include it (or note "ask the developer for the path to their `<head>` template")
- Order fixes by score impact descending
- The prompt must stand alone — someone should be able to paste it into a new conversation with no additional context

---

## HTML Audit Report

Generate after all 8 verification steps are complete. The report is a self-contained HTML file with embedded screenshots.

**Structure:**
- Header: business name, URL, audit date, overall score (X/8 passed), **AI Discoverability %** with colour-coded status badge (green ≥80%, amber 60–79%, red <60%)
- Score projection banner: "Implementing all suggested fixes will raise your score from X% → Y%" followed by a breakdown: one line per failing item showing the delta and the reason (pulled from the per-item reason table above)
- Failures section (open by default): one card per STEP_FAIL with expected → actual, screenshot, and suggested fix
- Passes section (collapsed): one card per STEP_PASS with evidence
- Implementation prompt section at the bottom: the full copy-pasteable prompt in a `<pre>` block with a one-click copy button

**Output path:** `.context/agent-audit-report.html`

**Embedding screenshots:**
```bash
base64 -i .context/agent-audit-screenshots/<step-id>.png | tr -d '\n'
# Use as: src="data:image/png;base64,<output>"
```

**Score calculation:**
- Checklist score: use the layer weights and per-item values from the AI Discoverability Score section above
- Verification step score: passed / 8 (shown separately as "live checks")
- Flag as critical if `schema-json-ld` or `booking-flow` fails — these block agentic task completion entirely
- Projection: sum the impact values of all ❌ and ⚠️ items → "fixes available: +X%"

**Minimal card structure:**
```html
<!-- Failure card -->
<details open>
  <summary><span class="fail">FAIL</span> schema-json-ld — expected geo field → missing</summary>
  <p><strong>Expected:</strong> LocalBusiness JSON-LD with geo coordinates</p>
  <p><strong>Actual:</strong> geo field absent from all JSON-LD blocks</p>
  <p><strong>Score impact:</strong> +8% after fix (from 34% → 42%)</p>
  <p><strong>Why this matters:</strong> without <code>geo</code>, agents cannot geoconfirm the business location — they skip businesses they cannot place on a map when answering location-based queries like "near me" or "in Indiranagar"</p>
  <p><strong>Fix:</strong> Add "geo": {"@type": "GeoCoordinates", "latitude": ..., "longitude": ...}</p>
  <img src="data:image/png;base64,..." alt="schema-json-ld failure screenshot">
</details>

<!-- Pass card -->
<details>
  <summary><span class="pass">PASS</span> entity-consistency — name/address/phone match across Google, Maps, Justdial</summary>
</details>
```
