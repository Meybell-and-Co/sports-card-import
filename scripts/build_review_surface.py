"""Build a disposable image-first presentation review surface for one reading batch."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = PROJECT_ROOT / "working" / "reading-batches"


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{ color-scheme: light; --ink: #17212b; --muted: #5b6975; --line: #d7dee4; --accent: #b44b24; --accent-soft: #fff1e9; --paper: #f6f7f5; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; color: var(--ink); background: var(--paper); font: 14px/1.45 Georgia, serif; }}
header {{ position: sticky; top: 0; z-index: 2; padding: 18px 24px 16px; background: rgba(246,247,245,.96); border-bottom: 1px solid var(--line); backdrop-filter: blur(8px); }}
h1 {{ margin: 0 0 4px; font: 700 23px/1.1 "Trebuchet MS", sans-serif; letter-spacing: .02em; }}
.summary {{ margin: 0; color: var(--muted); }}
.legend {{ display: flex; flex-wrap: wrap; gap: 8px 18px; margin-top: 12px; color: var(--muted); font: 12px/1.3 "Trebuchet MS", sans-serif; }}
.legend strong {{ color: var(--accent); }}
.review-actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 13px; }}
.export-button, .rotate-button {{ padding: 8px 11px; color: var(--ink); background: white; border: 1px solid var(--line); border-radius: 3px; cursor: pointer; font: 700 11px/1.2 "Trebuchet MS", sans-serif; letter-spacing: .04em; }}
.export-button:hover, .export-button:focus-visible, .rotate-button:hover, .rotate-button:focus-visible {{ border-color: var(--accent); color: var(--accent); }}
main {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; padding: 20px 24px 32px; }}
.exceptions {{ padding: 20px 24px 0; }}
.exceptions h2 {{ margin: 0 0 4px; font: 700 18px/1.2 "Trebuchet MS", sans-serif; color: var(--accent); }}
.exceptions > p {{ margin: 0 0 12px; color: var(--muted); }}
.exception-card {{ margin-bottom: 16px; padding: 13px; background: #fffaf7; border: 1px solid #e3b9a5; border-radius: 6px; }}
.exception-reason {{ margin: 0 0 10px; color: var(--ink); font: 700 12px/1.35 "Trebuchet MS", sans-serif; }}
.recoveries {{ padding: 20px 24px 0; }}
.recoveries h2 {{ margin: 0 0 4px; font: 700 18px/1.2 "Trebuchet MS", sans-serif; color: #256b55; }}
.recoveries > p {{ margin: 0 0 12px; color: var(--muted); }}
.recovery-card {{ margin-bottom: 16px; padding: 13px; background: #f5fbf8; border: 1px solid #9ac7b4; border-radius: 6px; }}
.recovery-card img {{ cursor: zoom-in; }}
.recovery-lightbox[hidden] {{ display: none; }}
.recovery-lightbox {{ position: fixed; inset: 0; z-index: 10; display: grid; place-items: center; padding: 24px; background: rgba(23,33,43,.94); }}
.recovery-lightbox img {{ max-width: 96vw; max-height: 88vh; width: auto; height: auto; object-fit: contain; }}
.recovery-lightbox button {{ position: absolute; top: 18px; right: 20px; padding: 10px 14px; color: white; background: var(--accent); border: 0; border-radius: 3px; cursor: pointer; font: 700 12px/1.2 "Trebuchet MS", sans-serif; }}
.recovery-lightbox p {{ position: absolute; bottom: 10px; left: 0; right: 0; margin: 0; color: white; text-align: center; font: 12px/1.3 "Trebuchet MS", sans-serif; }}
article {{ min-width: 0; padding: 13px; background: white; border: 1px solid var(--line); border-radius: 6px; box-shadow: 0 2px 8px rgba(23,33,43,.06); }}
.card-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; margin-bottom: 10px; font-family: "Trebuchet MS", sans-serif; }}
.card-id {{ font-weight: 700; }}
.decision {{ padding: 4px 7px; color: var(--accent); background: var(--accent-soft); border-radius: 3px; font-size: 11px; font-weight: 700; text-align: right; }}
.images {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
figure {{ margin: 0; min-width: 0; }}
.frame {{ display: grid; place-items: center; height: 245px; overflow: hidden; background: #e9edf0; border: 1px solid #c8d0d7; }}
img {{ display: block; width: 100%; height: 100%; object-fit: contain; transition: transform .2s ease; }}
.rotate-button {{ width: 100%; margin-top: 7px; color: white; background: var(--ink); }}
figcaption {{ padding-top: 6px; color: var(--muted); font: 12px/1.35 "Trebuchet MS", sans-serif; }}
figcaption strong {{ color: var(--ink); }}
.notes {{ margin: 10px 0 0; padding-top: 9px; border-top: 1px solid var(--line); color: var(--muted); font: 12px/1.35 "Trebuchet MS", sans-serif; }}
@media (max-width: 560px) {{ header {{ padding: 15px; }} main {{ grid-template-columns: 1fr; padding: 14px; }} .frame {{ height: 220px; }} }}
</style>
</head>
<body>
<header>
<h1>{batch_id} / Presentation Review</h1>
<p class="summary">{card_count} cards for normal review | {exception_count} source-image exceptions | source files remain unchanged</p>
<div class="legend"><span><strong>ROTATE</strong> changes only the displayed image</span><span>rotation state is shown on each image</span><span>front/back remains a proposal until approved</span></div>
<div class="review-actions"><button class="export-button" id="export-corrections" type="button">EXPORT PROPOSED CORRECTIONS</button></div>
</header>
<section class="recoveries" id="recoveries"></section>
<section class="exceptions" id="exceptions"></section>
<main id="cards"></main>
<div class="recovery-lightbox" id="recovery-lightbox" hidden><button id="close-recovery" type="button">CLOSE</button><img id="recovery-large-image" alt=""><p id="recovery-large-label"></p></div>
<script>
const batchId = {batch_id_json};
const cards = {cards_json};
const exceptions = {exceptions_json};
const recoveries = {recoveries_json};
const initialCorrections = {corrections_json};
const rotations = new Map();
const root = document.querySelector("#cards");
const lightbox = document.querySelector("#recovery-lightbox");
const largeImage = document.querySelector("#recovery-large-image");
const largeLabel = document.querySelector("#recovery-large-label");

function openRecoveryImage(image, label) {{
    largeImage.src = image.src;
    largeImage.alt = image.alt;
    largeLabel.textContent = label;
    lightbox.hidden = false;
}}

function closeRecoveryImage() {{
    lightbox.hidden = true;
    largeImage.removeAttribute("src");
}}

document.querySelector("#close-recovery").addEventListener("click", closeRecoveryImage);
lightbox.addEventListener("click", (event) => {{
    if (event.target === lightbox) closeRecoveryImage();
}});
document.addEventListener("keydown", (event) => {{
    if (event.key === "Escape") closeRecoveryImage();
}});

function rotationLabel(degrees) {{
    if (degrees === 0) return "0 deg";
    if (degrees === 90) return "90 deg CW";
    if (degrees === 180) return "180 deg";
    return "90 deg CCW";
}}

function updateImage(image, button, id, side) {{
    const degrees = rotations.get(`${{id}}_${{side}}`);
    image.style.transform = `rotate(${{degrees}}deg)`;
    button.textContent = `ROTATE | NOW ${{rotationLabel(degrees)}}`;
    button.setAttribute("aria-label", `Rotate ${{id}} supplied ${{side}} clockwise 90 degrees; currently ${{rotationLabel(degrees)}}`);
}}

for (const card of cards) {{
    const id = card.reading_id;
    const correction = initialCorrections[id] || {{}};
    const article = document.createElement("article");
    const front = correction.supplied_front;
    const back = correction.supplied_back;
    const decision = front && back ? `${{front.toUpperCase()}} FRONT / ${{back.toUpperCase()}} BACK` : "REVIEW REQUIRED";
    article.innerHTML = `
        <div class="card-head"><span class="card-id">${{id}}</span><span class="decision">${{decision}}</span></div>
        <div class="images">
            <figure><div class="frame"><img data-side="a" src="images/${{id}}_a.jpg" alt="${{id}} supplied side A"></div><button class="rotate-button" data-side="a" type="button">ROTATE</button><figcaption><strong>Supplied A</strong><br>${{back === "a" ? "proposed back" : "front/back undecided"}}</figcaption></figure>
            <figure><div class="frame"><img data-side="b" src="images/${{id}}_b.jpg" alt="${{id}} supplied side B"></div><button class="rotate-button" data-side="b" type="button">ROTATE</button><figcaption><strong>Supplied B</strong><br>${{front === "b" ? "proposed front" : "front/back undecided"}}</figcaption></figure>
        </div>
        <p class="notes">Click ROTATE until the displayed orientation is correct. The current state is retained in this page.</p>`;
    root.appendChild(article);

    for (const side of ["a", "b"]) {{
        const key = `${{id}}_${{side}}`;
        rotations.set(key, Number(correction[`${{side}}_rotation_clockwise`] || 0));
        const image = article.querySelector(`img[data-side="${{side}}"]`);
        const button = article.querySelector(`button[data-side="${{side}}"]`);
        updateImage(image, button, id, side);
        button.addEventListener("click", () => {{
            rotations.set(key, (rotations.get(key) + 90) % 360);
            updateImage(image, button, id, side);
        }});
    }}
}}

if (exceptions.length) {{
    const section = document.querySelector("#exceptions");
    section.innerHTML = `<h2>Source-image exceptions / excluded from approval</h2><p>These cards require source recovery or diagnosis. Do not approve them through this page.</p>`;
    for (const exception of exceptions) {{
        const card = document.createElement("article");
        card.className = "exception-card";
        card.innerHTML = `
            <div class="card-head"><span class="card-id">${{exception.reading_id}}</span><span class="decision">SOURCE EXCEPTION</span></div>
            <p class="exception-reason">${{exception.reason}}</p>
            <div class="images">
                <figure><div class="frame"><img src="images/${{exception.reading_id}}_a.jpg" alt="${{exception.reading_id}} supplied side A"></div><figcaption><strong>Supplied A</strong><br>held for separate diagnosis</figcaption></figure>
                <figure><div class="frame"><img src="images/${{exception.reading_id}}_b.jpg" alt="${{exception.reading_id}} supplied side B"></div><figcaption><strong>Supplied B</strong><br>held for separate diagnosis</figcaption></figure>
            </div>
            <p class="notes">Source pair: ${{exception.source_pair_key}}<br>Recorded files: ${{exception.source_files.a}} and ${{exception.source_files.b}}<br>Complete source search: ${{exception.search_result}}</p>`;
        section.appendChild(card);
    }}
}}

if (recoveries.length) {{
    const section = document.querySelector("#recoveries");
    section.innerHTML = `<h2>{recovery_heading}</h2><p>{recovery_note}</p>`;
    for (const recovery of recoveries) {{
        const card = document.createElement("article");
        card.className = "recovery-card";
        card.innerHTML = `
            <div class="card-head"><span class="card-id">${{recovery.reading_id}}</span><span class="decision">{recovery_badge}</span></div>
            <div class="images">
                <figure><div class="frame"><img src="${{recovery.image_a}}" alt="${{recovery.reading_id}} proposed recovered side A"></div><figcaption><strong>Candidate A</strong><br>${{recovery.source_a}}</figcaption></figure>
                <figure><div class="frame"><img src="${{recovery.image_b}}" alt="${{recovery.reading_id}} proposed recovered side B"></div><figcaption><strong>Candidate B</strong><br>${{recovery.source_b}}</figcaption></figure>
            </div>
            <p class="notes">Identity: ${{recovery.source_pair_key}} / crop slot ${{recovery.slot}}<br>${{recovery.match_basis}}</p>`;
        section.appendChild(card);
        for (const image of card.querySelectorAll("img")) {{
            image.addEventListener("click", () => openRecoveryImage(image, `${{recovery.reading_id}} proposed recovery`));
        }}
    }}
}}

document.querySelector("#export-corrections").addEventListener("click", () => {{
    const corrections = {{}};
    for (const card of cards) {{
        const id = card.reading_id;
        const prior = initialCorrections[id] || {{}};
        corrections[id] = {{
            supplied_front: prior.supplied_front || null,
            supplied_back: prior.supplied_back || null,
            a_rotation_clockwise: rotations.get(`${{id}}_a`),
            b_rotation_clockwise: rotations.get(`${{id}}_b`),
            side_swap_required: prior.side_swap_required ?? null
        }};
    }}
    const blob = new Blob([JSON.stringify({{ batch_id: batchId, corrections }}, null, 2)], {{ type: "application/json" }});
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${{batchId}}-reviewed-presentation-proposal.json`;
    link.click();
    URL.revokeObjectURL(link.href);
}});
</script>
</body>
</html>
"""


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_batch(batch_id: str) -> tuple[list[dict], dict, list[dict]]:
    batch_root = BATCH_ROOT / batch_id
    manifest = load_json(batch_root / "manifest.json", None)
    if not isinstance(manifest, dict) or manifest.get("batch_id") != batch_id:
        raise RuntimeError(f"Invalid manifest for {batch_id}: {batch_root / 'manifest.json'}")
    cards = manifest.get("cards")
    if not isinstance(cards, list) or not cards:
        raise RuntimeError(f"Manifest has no cards: {batch_root / 'manifest.json'}")
    review_state = load_json(batch_root / "review-state.json", {})
    proposal = review_state or load_json(batch_root / f"{batch_id}-presentation.json", {})
    if not isinstance(proposal, dict):
        raise RuntimeError(f"Presentation proposal must be an object: {batch_id}")
    corrections = proposal.get("corrections", {})
    if not isinstance(corrections, dict):
        corrections = {}
    exception_data = load_json(batch_root / "review-exceptions.json", {})
    exceptions = exception_data.get("exceptions", []) if isinstance(exception_data, dict) else []
    if not isinstance(exceptions, list):
        raise RuntimeError(f"Review exceptions must be a list: {batch_id}")
    exception_ids = {item.get("reading_id") for item in exceptions}
    if None in exception_ids or any(not isinstance(item, dict) for item in exceptions):
        raise RuntimeError(f"Review exceptions contain an invalid record: {batch_id}")
    if exception_ids - {card.get("reading_id") for card in cards}:
        raise RuntimeError(f"Review exceptions contain unknown reading IDs: {batch_id}")
    recovery_data = load_json(batch_root / "review-recovery.json", {})
    recovery_status = recovery_data.get("review_status", "proposed_recovery") if isinstance(recovery_data, dict) else "proposed_recovery"
    recoveries = recovery_data.get("recoveries", []) if isinstance(recovery_data, dict) else []
    if not isinstance(recoveries, list):
        raise RuntimeError(f"Review recovery must be a list: {batch_id}")
    return cards, corrections, exceptions, recoveries, recovery_status


def build_review_surface(batch_id: str) -> Path:
    cards, corrections, exceptions, recoveries, recovery_status = load_batch(batch_id)
    card_ids = {card.get("reading_id") for card in cards}
    if None in card_ids or any(not isinstance(card_id, str) for card_id in card_ids):
        raise RuntimeError(f"Manifest contains a card without reading_id: {batch_id}")
    unknown = set(corrections) - card_ids
    if unknown:
        raise RuntimeError(f"Proposal contains unknown reading IDs: {sorted(unknown)}")
    exception_ids = {item["reading_id"] for item in exceptions}
    normal_cards = [card for card in cards if card["reading_id"] not in exception_ids]
    corrections = {key: value for key, value in corrections.items() if key not in exception_ids}
    recovery_approved = recovery_status == "approved_recovery"
    output = BATCH_ROOT / batch_id / "review.html"
    page = PAGE_TEMPLATE.format(
        title=html.escape(f"{batch_id} Presentation Review"),
        batch_id=html.escape(batch_id),
        card_count=len(normal_cards),
        exception_count=len(exceptions),
        batch_id_json=json.dumps(batch_id),
        cards_json=json.dumps(normal_cards, ensure_ascii=True),
        exceptions_json=json.dumps(exceptions, ensure_ascii=True),
        recoveries_json=json.dumps(recoveries, ensure_ascii=True),
        corrections_json=json.dumps(corrections, ensure_ascii=True),
        recovery_heading=("Approved source recovery / installed in working images" if recovery_approved else "Proposed source recovery / approval required"),
        recovery_note=("These approved candidates were installed only into the Batch0015 working-image slots; production and canonical data remain unchanged." if recovery_approved else "These complete candidates match the recorded source pair and crop slots. They are shown for approval only; current batch files remain unchanged."),
        recovery_badge=("APPROVED RECOVERY" if recovery_approved else "PROPOSED RECOVERY"),
    )
    output.write_text(page, encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch_id", help="Reading batch such as batch0014")
    args = parser.parse_args()
    output = build_review_surface(args.batch_id)
    print(f"REVIEW_SURFACE: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
