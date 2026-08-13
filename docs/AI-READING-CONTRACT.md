# Scout & Steward AI Reading Contract

## Purpose

Read sports-card image pairs and produce structured identification data.

The reader identifies and transcribes cards.

The reader also reports presentation corrections needed by Turtle Shower.
The reader does not rename, rotate, move, or modify image files.

## Core Rule

**Evidence over inference. Unknown is better than guessed.**

Populate a field only when the individual card or other explicit evidence
supplied for that record supports it.

Do not propagate an identification, set, subset, classification, rookie
status, copyright statement, condition observation, card number, or other
attribute merely because neighboring cards appear related.

When evidence is insufficient:

- use `null` where the schema permits;
- lower confidence appropriately;
- set `review_required` to `true` when human review is warranted.

Uncertainty is a valid result. It is not a validation failure.

## Image Pair Contract

Each reading record is supplied with two working images:

- `<reading_id>_a.<ext>`
- `<reading_id>_b.<ext>`

The suffixes describe supplied sides only.

They are **not guaranteed** to mean:

- `_a` = card front
- `_b` = card back

Determine front and back from the supplied images.

Do not assume the filenames are already correct.

## Presentation Report

Every output record must include a `presentation` object with:

- `supplied_front`
- `supplied_back`
- `a_rotation_clockwise`
- `b_rotation_clockwise`
- `side_swap_required`

Allowed values:

- `supplied_front`: `"a"`, `"b"`, or `null`
- `supplied_back`: `"a"`, `"b"`, or `null`
- `a_rotation_clockwise`: `0`, `90`, `180`, `270`, or `null`
- `b_rotation_clockwise`: `0`, `90`, `180`, `270`, or `null`
- `side_swap_required`: `true`, `false`, or `null`

### Front / Back

Determine front and back independently from card identity.

If supplied `_a` is confidently the front and `_b` the back:

    "supplied_front": "a"
    "supplied_back": "b"
    "side_swap_required": false

If supplied `_b` is confidently the front and `_a` the back:

    "supplied_front": "b"
    "supplied_back": "a"
    "side_swap_required": true

If front/back cannot be established confidently:

    "supplied_front": null
    "supplied_back": null
    "side_swap_required": null

Do not merely note that the images appear reversed.

**Report the correction required.**

Turtle Shower is authorized to perform the filesystem correction later.

### Rotation

For each supplied image, report the clockwise rotation required to make
the card naturally readable.

- already upright: `0`
- one clockwise quarter-turn: `90`
- upside down: `180`
- one counterclockwise quarter-turn: `270`

Evaluate `_a` and `_b` independently.

Do not rotate merely to force portrait orientation.
Landscape card designs may legitimately be landscape.

If natural readable orientation cannot be established confidently, use `null`.

## Identification

Identify only what the evidence supports for the individual card.

Use `null` rather than extrapolating from adjacent records.

In particular, do not infer:

- year
- manufacturer
- brand
- set
- subset
- title
- card number
- rookie status
- classification
- parallel status
- copyright text

solely from neighboring cards.

Context may help interpret visible evidence, but it must not replace
record-specific evidence.

## Condition

This reading pass is **not a card-grading workflow**.

Do not infer physical card damage from scanner artifacts, glare, dust,
sleeves, platen marks, compression, or other image artifacts.

Leave condition fields null unless an observation is clearly supported
and the workflow explicitly requires it.

## Confidence and Review

Confidence describes the reliability of the record produced.

Use `review_required` when:

- identification is uncertain;
- important transcription is uncertain;
- front/back cannot be established confidently;
- rotation cannot be established confidently when correction appears needed;
- supplied images may not form a valid pair;
- evidence conflicts.

Do not increase confidence merely because neighboring cards are similar.

## Reader Boundary

The reader may:

- identify;
- transcribe;
- distinguish front from back;
- determine readable orientation;
- report uncertainty.

The reader may not:

- rename files;
- swap files;
- rotate files;
- modify source imagery;
- modify working imagery;
- invent missing identification data.

**Presentation decisions belong to the reader.**

**Filesystem corrections belong to Turtle Shower.**
