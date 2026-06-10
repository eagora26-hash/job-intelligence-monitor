# Case Study — Multi-Source Job Intelligence Monitor

All facts below are from the actual project record (git history, validation reports, live
runs). Nothing is invented.

---

## Challenge

Build a portfolio-grade product on top of an existing open-source scraping engine
(Scrapling) that monitors five job marketplaces — RemoteOK, We Work Remotely, Freelancer,
Fiverr and Wellfound — scores opportunities against a freelancer's keyword profile, and
alerts via Telegram, with a professional analytics dashboard. The brief demanded 40+
specific requirements: deduplication, change history, source health, resume capability,
backups, Docker, CI, exports, demo mode, and a codebase that "looks like a commercial SaaS
product, not a scraper project." Two of the five sources actively resist automation.

## Approach

1. **Plan before code.** Analyzed the vendored engine and authored four governance docs
   (implementation plan, task board, portfolio analysis, handover) before any feature work.
2. **Phased delivery with a per-phase test gate** — foundations → scrapers → enrichment →
   orchestration → dashboard → extensions → ops. 21 commits, each phase landing green.
3. **Audit-driven completion.** After "done," ran a full evidence-based audit (every
   subsystem exercised live), which found and fixed real gaps instead of assuming success.

## Architecture

A dedicated `job_monitor/` package layered strictly downward (interfaces → orchestration →
services → domain → acquisition), reusing the engine's parser and its `curl_cffi`
TLS-fingerprint backend while deliberately avoiding its Playwright-coupled fetcher — so
the runtime needs no browser. Repository pattern for all persistence; a registry makes a
new source a one-line addition; notifications, AI, graph and API are interfaces with
working default implementations.

## Implementation highlights (real incidents)

- **Fiverr returned 0 records** at the first audit: the site had dropped the `ld+json`
  markup the parser targeted. Investigation showed the data had moved into a
  `perseus-initial-props` JSON island (~48 gigs/page) — and, unusually, that plain
  TLS-impersonated HTTP gets the data while real headless browsers get blocked.
  Rewrote the parser: **0 → ~90 records/run**.
- **Wellfound is Cloudflare-blocked at the IP level.** Installed a full stealth browser
  stack to test (needing a platform override on Ubuntu 26.04, where Playwright builds
  don't exist) — still 403. Decision: document honestly, isolate the failure, disable the
  source in scheduled runs. The parser stays fixture-tested for when egress changes.
- **Alert flooding** surfaced in live testing: the first run on an empty database produced
  118 "new" jobs, and Fiverr's promoted-gig rotation kept generating a trickle of new URLs.
  Redesigned the notification semantics: a **silent baseline run** (everything marked
  notified, one summary message) plus a per-source alert allow-list. Validated over three
  consecutive live cycles: exactly one message total.
- **A real config bug** found during validation: pydantic-settings silently ignored
  field-name constructor arguments in favor of `.env` values (`populate_by_name` was
  unset) — the kind of bug only live verification catches.

## Results

- **4 of 5 sources extracting live** (~350 jobs/run, 100% extraction success each);
  249 real jobs under management at delivery.
- **Telegram alerting proven live**: delivery receipts captured, zero duplicates across
  repeated runs, baseline behavior validated end-to-end.
- **7-page dashboard**, all pages error-free in automated headless validation; deployed
  pattern: GitHub Actions refreshes data every 6 h, Streamlit Cloud auto-redeploys.
- **65 tests, 67% coverage, lint clean, CI green** (Lint + Tests + Scheduled Scrape all
  passing on GitHub at delivery).
- Full client package: installation/user/admin guides, deployment walkthrough, validation
  reports, screenshots.

## Lessons learned

1. **"Tests pass" is not "it works."** Three of the most important fixes (Fiverr parser,
   alert flooding, the settings bug) were invisible to the green suite and only surfaced
   through live, evidence-collecting validation.
2. **Anti-bot is a spectrum, not a wall.** The same site can serve full data to a
   well-impersonated HTTP client while blocking a real browser. Verify per-site before
   reaching for heavier tooling.
3. **Monitoring semantics are product decisions.** "Notify on new jobs" sounds trivial
   until the first run floods a chat; baseline-then-delta is the behavior users actually
   expect, and it must live in the database to survive restarts.
4. **Honest failure handling is a feature.** Returning empty (never fabricated) data,
   isolating failures, and disclosing limits made the product more credible, not less.
