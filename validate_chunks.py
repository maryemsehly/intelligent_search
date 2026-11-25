
import json
from pathlib import Path

chunks_file = Path("data/chunks/chunks.jsonl")

total = 0
sources = set()
ids = set()
invalid = []
empty_text = 0
duplicate_ids = 0

with chunks_file.open("r", encoding="utf-8") as f:
    for line_number, line in enumerate(f, start=1):
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            invalid.append(line_number)
            continue

        total += 1

        if not item.get("text", "").strip():
            empty_text += 1

        if not item.get("source_file") or not item.get("chunk_id"):
            invalid.append(line_number)

        sources.add(item.get("source_file"))

        chunk_id = item.get("chunk_id")
        if chunk_id in ids:
            duplicate_ids += 1
        ids.add(chunk_id)

print("===== VALIDATION DES CHUNKS =====")
print("Chunks lus :", total)
print("Sources distinctes :", len(sources))
print("Identifiants uniques :", len(ids))
print("Chunks avec texte vide :", empty_text)
print("Identifiants dupliqués :", duplicate_ids)
print("Lignes invalides :", len(invalid))

if total == 38338 and len(sources) == 210 and not (
    empty_text or duplicate_ids or invalid
):
    print("Résultat : VALIDATION REUSSIE")
else:
    print("Résultat : VERIFICATION NECESSAIRE")
