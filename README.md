Pipeline

1. Scan

2. Crop

3. AI Extraction

4. Normalize

5. Validate

6. Append

7. Export

[Pipeline]

Raw Images
    ↓
Crop
    ↓
AI Extraction
    ↓
batch###.json
    ↓
append_batch.py
    ↓
cards.json
    ↓
export_ebay_csv.py
    ↓
eBay Upload CSV


[Repository Philosophy]

Raw images are immutable.

Batch JSON files are immutable.

cards.json is the authoritative source of truth.

All exports are generated artifacts and may be deleted and regenerated.
