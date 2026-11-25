
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INVENTORY = BASE_DIR / "reports" / "reports_inventory.csv"
OCR_MANIFEST = BASE_DIR / "reports" / "ocr_text_manifest.csv"
OUTPUT_DIR = BASE_DIR / "data" / "corpus_complet"
MANIFEST = BASE_DIR / "reports" / "corpus_complet_manifest.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Nettoyer uniquement les anciens textes du corpus de sortie
for path in OUTPUT_DIR.glob("*.txt"):
    path.unlink()

# Charger les textes OCR et les associer au nom du PDF original
ocr_by_source = {}

with open(OCR_MANIFEST, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        ocr_pdf_name = Path(row["pdf_source"]).name
        original_pdf_name = ocr_pdf_name.replace("_ocr.pdf", ".pdf")
        text_path = Path(row["fichier_texte"])

        if text_path.exists():
            ocr_by_source[original_pdf_name] = text_path

with open(INVENTORY, encoding="utf-8-sig", newline="") as f:
    inventory = list(csv.DictReader(f))

results = []
missing = []
empty = []

for row in inventory:
    pdf_name = row["file_name"]
    original_text = Path(row["text_output"]) if row.get("text_output") else None

    status = row.get("status", "")
    candidate = row.get("ocr_candidate", "")
    
# Priorité absolue à l'OCR pour les 4 rapports concernés
    if pdf_name in ocr_by_source:
       source_text = ocr_by_source[pdf_name]
       method = "OCR"
    elif original_text and original_text.exists():
        source_text = original_text
        method = "extraction_initiale"
    else:
        missing.append(pdf_name)
        results.append({
            "file_name": pdf_name,
            "text_file": "",
          "method": "MANQUANT",
        "characters": 0,
        "status": "TEXTE INTROUVABLE",
        })
        continue


    content = source_text.read_text(
        encoding="utf-8", errors="replace"
    ).strip()

    if not content:
        empty.append(pdf_name)

    output_path = OUTPUT_DIR / f"{Path(pdf_name).stem}.txt"
    output_path.write_text(content, encoding="utf-8")

    results.append({
        "file_name": pdf_name,
        "text_file": str(output_path),
        "method": method,
        "characters": len(content),
        "status": "VIDE" if not content else "OK",
    })

with open(MANIFEST, "w", encoding="utf-8-sig", newline="") as f:
    columns = ["file_name", "text_file", "method", "characters", "status"]
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(results)

print("\n===== BILAN DU CORPUS =====")
print(f"Rapports dans l'inventaire : {len(inventory)}")
print(f"Fichiers texte créés : {len(list(OUTPUT_DIR.glob('*.txt')))}")
print("Extraction initiale :", sum(
    r["method"] == "extraction_initiale" for r in results
))
print("OCR :", sum(r["method"] == "OCR" for r in results))
print("Textes introuvables :", len(missing))
print("Textes vides :", len(empty))
print("Manifeste :", MANIFEST)

if missing:
    print("\nRapports sans texte :")
    for name in missing[:10]:
        print(" -", name)

if empty:
    print("\nRapports dont le texte est vide :")
    for name in empty[:10]:
        print(" -", name)
