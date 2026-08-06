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
