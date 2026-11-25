import csv
import subprocess
from pathlib import Path
BASE = Path.cwd()
CSV_PATH = BASE / "reports" / "reports_inventory.csv"
OUT_DIR = BASE / "reports" / "ocr_output"
LOG_PATH = BASE / "reports" / "ocr_log.csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)
with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
candidates = [r for r in rows if "OUI" in r.get("ocr_candidate", "")]
results = []
for row in candidates:
    source = Path(row["relative_path"])
    output = OUT_DIR / f"{source.stem}_ocr.pdf"
    print(f"\n{'=' * 60}")
    print(f"Rapport : {source.name}")
    if not source.is_file():
        print("ERREUR : fichier source introuvable.")
        results.append({
            "source": str(source),
            "output": str(output),
            "status": "SOURCE_INTROUVABLE",
            "return_code": ""
        })
        continue
    if output.exists():
        print(f"Déjà présent, ignoré pour protéger le résultat : {output.name}")
        results.append({
            "source": str(source),
            "output": str(output),
            "status": "DEJA_PRESENT_NON_ECRASE",
            "return_code": ""
        })
        continue
    command = [
        "ocrmypdf",
        "-l", "fra+ara",
        "--rasterizer", "pypdfium",
        "--output-type", "pdf",
        "--skip-text",
        "--no-overwrite",
        str(source),
        str(output),
    ]
    try:
        completed = subprocess.run(command, check=False)
        status = "OK" if completed.returncode == 0 else "ERREUR_OCR"
        print(f"Résultat : {status} (code {completed.returncode})")
        results.append({
            "source": str(source),
            "output": str(output),
            "status": status,
            "return_code": completed.returncode
        })
    except FileNotFoundError:
        print("ERREUR : la commande ocrmypdf est introuvable dans ce terminal.")
        results.append({
            "source": str(source),
            "output": str(output),
            "status": "OCRMY_PDF_INTROUVABLE",
            "return_code": ""
        })
        break
with LOG_PATH.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=["source", "output", "status", "return_code"]
    )
    writer.writeheader()
    writer.writerows(results)
print(f"\nTerminé. Journal : {LOG_PATH}")
print(f"Dossier des PDF OCR : {OUT_DIR}")
