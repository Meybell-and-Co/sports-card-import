# MAM Timesheet

## Scout & Steward — Time Reconstruction

**Status:** In progress
**Last reconciled:** August 13, 2026

This document is the working accounting record for reconstructing time spent on Scout & Steward work for Cy.

The goal is a conservative, supportable accounting of actual work performed — not maximizing billable hours.

---

## Accounting Principles

### 45-Minute Rule

A gap of **45 minutes or more** between evidence events is treated as a potential break in work.

A gap is not automatically billable merely because work occurred before and after it.

Ambiguous gaps are classified as:

- **BRIDGE** — corroborating evidence supports continuous work.
- **SPLIT** — evidence or recollection indicates a genuine break.
- **UNSURE** — insufficient evidence; investigate if worthwhile.

When reasonable evidence cannot establish that work continued through a gap, the unaccounted time is excluded.

### Evidence Sources

Time reconstruction currently uses:

1. **Photo filesystem timestamps**
   - Windows `LastWriteTime`
   - JPG, JPEG, PNG, and WEBP files
   - 3,952 image files examined

2. **sports-card-import Git history**
   - 60 commits
   - Earliest commit: August 6, 2026 at 10:23 AM
   - Includes card ingestion, canonical inventory, batch processing, eBay export, R2 preparation, and Portal publication.

3. **scout-and-steward-portal Git/local history**
   - Portal development
   - Pricing and market-evidence system
   - eBay integration
   - Turtle image-processing/autocrop development

4. **ChatGPT conversation timestamps**
   - Used selectively to corroborate work occurring between machine-generated evidence.
   - Particularly useful for research, planning, debugging, eBay work, and development sessions that did not themselves create filesystem or Git events.

5. **Human recollection**
   - Used to identify known breaks and distinguish separate work sessions.
   - Should generally be used conservatively.

---

## Machine Evidence Baselines

### Photo Activity

Using filesystem timestamps alone and splitting sessions whenever a gap reaches 45 minutes:

**Reconstructed photo activity: 23.95 hours**

This is an evidence baseline, **not an independently additive billable total**, because some photo activity overlaps Git and ChatGPT-supported work.

### Unified Evidence

The first unified Photo + Import Git + Portal Git reconstruction produced:

- **190 machine evidence events**
- **29 same-day gaps of 45+ minutes requiring review**
- Overnight and multi-day gaps excluded automatically from the review queue

### Conservative Git-Era Estimate

A preliminary estimate using Git timestamps alone, deliberately excluding unaccounted gaps and avoiding generous inference:

**Approximately 30 hours, rounded to the nearest 10 hours**

This is a deliberately conservative **Git-era floor**, not an estimate of the entire Scout & Steward engagement.

It does not fully account for:

- June/July photo processing
- work before the first commit or after the last commit in a session
- research and planning performed in ChatGPT
- manual eBay work
- image-processing work not captured by Git
- other corroborated work between commits

Portal development may also include intentional **goodwill/non-billed hours**.

No final billable-hour total has been established.

---

## Payment Received

### July 17, 2026

**Payment received: $1,200**

Treatment:

Payment on account toward accrued and/or future Scout & Steward work.

The payment was **not allocated to a specific invoice or specific block of hours when received**.

Therefore:

> Total substantiated fees
> LESS $1,200 payment received July 17
> = Remaining balance due

Work performed before July 17 should not automatically be excluded from the reconstruction.

---

# Manual Reconciliation

## August 12, 2026

This date has been substantially reconciled using filesystem, Git, ChatGPT, and human-recollection evidence.

### Morning

**7:15 AM**
Portal/Git evidence — configuring listing logic.

**7:30–8:21 AM**
ChatGPT — `Listing 113 Items`

Continuous Cy-related work.

**9:05 AM**
Photo/WebP evidence.

**10:15–11:21 AM**
ChatGPT — `eBay Valuation Challenges`

**10:40–11:12 AM**
Photo activity overlaps the ChatGPT work.

There remain smaller internal periods without direct evidence; do not automatically bill them solely because activity occurred on both sides.

### Midday / Afternoon

**1:08–1:35 PM**
ChatGPT — `Dalmatian eBay Strategy`

**1:36–2:40 PM**
Photo activity.

**2:31–3:21 PM**
ChatGPT — `Automating Image Rotation`

The ChatGPT work overlaps the photo evidence and demonstrates work continued beyond the 2:40 PM machine endpoint.

### Known Break

Work stopped after the 3:21 PM image-rotation session.

Mark specifically remembers **going downstairs to Larry**.

Treat this as a genuine personal break.

**Do not bridge this interval.**

### Evening

**5:42–8:10 PM**
ChatGPT — `Automating Image Rotation`

Portal/Git activity around 6:01–6:03 PM and photo activity around 7:57 PM occur inside this continuous ChatGPT-supported work block.

Therefore the machine-evidence gap in this period is:

**BRIDGE**

### Separate Sofa Session

**9:24–9:57 PM**
ChatGPT — `Rudy Bostic Painting`

Cy/eBay listing work.

Mark specifically remembers doing this separately **from the sofa while watching television**.

Treat as its own work session.

Do **not** use it to bridge the entire surrounding evening gap.

### Late Night

**10:13 PM–12:16 AM (August 13)**
ChatGPT — `Automating Image Rotation`

Git commits around 10:36–10:45 PM fall within this work session.

This is a distinct late-night work block crossing midnight.

---

## August 12 Gap Decisions

Known decisions:

- Morning ChatGPT evidence substantially corroborates the machine activity.
- 2:40 PM → evening: **SPLIT**
  - Work supported through 3:21 PM.
  - Genuine personal break afterward.
  - Work resumes at 5:42 PM.
- 6:03 PM → 7:57 PM: **BRIDGE**
- 7:57 PM → 10:36 PM: **SPLIT**
  - Image-rotation work through 8:10 PM.
  - Separate Rudy Bostic session 9:24–9:57 PM.
  - Image-rotation work resumes at 10:13 PM.
- Late-night image-rotation work continues through **12:16 AM August 13**.

Do not convert August 12 into one continuous all-day session.

---

# Remaining Reconciliation

Manual review should resume backward from:

1. **August 11**
2. August 10
3. August 8
4. August 7
5. August 6
6. Older June/July photo-processing dates

Use ChatGPT timestamps only where machine evidence leaves a meaningful ambiguity.

Do not spend disproportionate time investigating tiny gaps if excluding them is reasonable.

---

# Important Accounting Guardrails

Git commits prove that work existed at a particular moment.

They do **not** prove that every minute between commits was spent working.

Filesystem timestamps have the same limitation.

Automated image conversions and Turtle runs can create many timestamps without representing equivalent amounts of human labor.

Conversely, research, planning, debugging, conversation, and decision-making can consume substantial work time without creating a filesystem or Git event.

For that reason, the final timesheet should use **corroborated work sessions**, not raw event counts.

When evidence is ambiguous and not worth further investigation, favor the conservative interpretation.

---

# Current Bookmark

As of August 13, 2026:

- Evidence collection framework: **COMPLETE**
- Photo timestamp reconstruction: **COMPLETE**
- Git histories collected: **COMPLETE**
- Unified machine timeline: **COMPLETE**
- 45-minute reconciliation methodology: **ESTABLISHED**
- August 12 manual reconciliation: **SUBSTANTIALLY COMPLETE**
- Remaining dates: **PENDING**
- Preliminary conservative Git-era floor: **~30 hours**
- Final engagement hours: **NOT YET CALCULATED**
- Payment already received: **$1,200 on July 17**
- Final invoice balance: **NOT YET CALCULATED**

## Next Step

Resume with **August 11, 2026** and adjudicate its ambiguous same-day gaps using ChatGPT timestamps only where necessary.

Do not restart the forensic reconstruction from scratch.

Scanning/acquisition time is present in surviving CreationTime metadata. Approximately 8 hours of strong early scanning-session evidence identified June 26–July 4; additional July 18–19 activity requires reconciliation. Do not add these hours independently to photo-session totals until overlaps are resolved.
