#!/usr/bin/env python3
"""
Inventaire de rapports PDF pour le projet de recherche intelligente de PFE.

- Ne modifie jamais les PDF originaux.
- Parcourt le dossier indiqué et ses sous-dossiers.
- Extrait le texte disponible avec PyMuPDF.
- Enregistre un fichier texte par PDF et un CSV d'inventaire.
- Signale les PDF qui nécessitent probablement un OCR.
"""

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERREUR : PyMuPDF n'est pas installé.")
    print("Installe-le avec : python -m pip install pymupdf pandas tqdm")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_stem(path: Path) -> str:
    # Nom lisible et stable pour les fichiers texte de sortie.
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", path.stem).strip("._")
    return (cleaned or "rapport")[:80]


def extract_pdf(pdf_path: Path, text_output: Path) -> dict:
    record = {
        "file_name": pdf_path.name,
        "relative_path": str(pdf_path),
        "file_size_mb": round(pdf_path.stat().st_size / (1024 * 1024), 3),
        "sha256": "",
        "page_count": 0,
        "extracted_characters": 0,
        "average_characters_per_page": 0,
        "ocr_candidate": "",
        "status": "OK",
        "error": "",
        "text_output": "",
    }

    try:
        record["sha256"] = sha256_file(pdf_path)
        page_texts = []
        with fitz.open(pdf_path) as doc:
            record["page_count"] = len(doc)
            for page_number, page in enumerate(doc, start=1):
                page_text = page.get_text("text") or ""
                page_texts.append(f"\n\n===== PAGE {page_number} =====\n\n{page_text}")

        full_text = "".join(page_texts).strip()
        # Compte les caractères non blancs pour éviter de surévaluer les espaces.
        non_whitespace_chars = len(re.sub(r"\s+", "", full_text))
        record["extracted_characters"] = non_whitespace_chars
        if record["page_count"]:
            record["average_characters_per_page"] = round(
                non_whitespace_chars / record["page_count"], 1
            )

        # Seuil indicatif seulement : un humain doit confirmer avant OCR.
        candidate = (
            record["page_count"] == 0
            or non_whitespace_chars < 200
            or record["average_characters_per_page"] < 100
        )
        record["ocr_candidate"] = "OUI - à vérifier" if candidate else "Non évident"

        text_output.mkdir(parents=True, exist_ok=True)
        # Inclut un préfixe basé sur le hash pour éviter les collisions de noms.
        short_hash = record["sha256"][:10]
        out_path = text_output / f"{safe_stem(pdf_path)}_{short_hash}.txt"
        out_path.write_text(full_text, encoding="utf-8", errors="replace")
        record["text_output"] = str(out_path)

        if candidate:
            record["status"] = "A_VERIFIER_OCR"

    except Exception as exc:
        record["status"] = "ERREUR"
        record["error"] = f"{type(exc).__name__}: {exc}"

    return record


def main():
    parser = argparse.ArgumentParser(
        description="Inventorie les PDF et extrait le texte avec PyMuPDF."
    )
    parser.add_argument(
        "pdf_folder",
        help='Chemin du dossier contenant les PDF, par exemple "C:\\\\PFE\\\\PDFs"',
    )
    parser.add_argument(
        "--output",
        default=".",
        help="Dossier de sortie du projet (par défaut : dossier courant).",
    )
    args = parser.parse_args()

    pdf_folder = Path(args.pdf_folder).expanduser().resolve()
    output_root = Path(args.output).expanduser().resolve()

    if not pdf_folder.exists() or not pdf_folder.is_dir():
        print(f"ERREUR : dossier PDF introuvable : {pdf_folder}")
        sys.exit(2)

    pdf_files = sorted(
        (p for p in pdf_folder.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"),
        key=lambda p: str(p).lower(),
    )
    if not pdf_files:
        print(f"Aucun PDF trouvé dans : {pdf_folder}")
        sys.exit(3)

    extracted_dir = output_root / "data" / "extracted_text"
    reports_dir = output_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    print(f"PDF trouvés : {len(pdf_files)}")
    print(f"Dossier source : {pdf_folder}")
    print(f"Dossier de sortie : {output_root}")
    print("L'inventaire commence...")

    records = []
    iterator = tqdm(pdf_files, desc="Traitement des PDF") if tqdm else pdf_files
    for pdf_path in iterator:
        records.append(extract_pdf(pdf_path, extracted_dir))

    csv_path = reports_dir / "reports_inventory.csv"
    fieldnames = [
        "file_name", "relative_path", "file_size_mb", "sha256", "page_count",
        "extracted_characters", "average_characters_per_page", "ocr_candidate",
        "status", "error", "text_output"
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    total = len(records)
    errors = sum(r["status"] == "ERREUR" for r in records)
    ocr_candidates = sum("OCR" in r["status"] for r in records)
    successful = total - errors
    total_pages = sum(r["page_count"] for r in records)

    summary_path = reports_dir / "inventory_summary.txt"
    summary = (
        f"Date d'exécution : {datetime.now().isoformat(timespec='seconds')}\n"
        f"Dossier source : {pdf_folder}\n"
        f"Nombre de PDF trouvés : {total}\n"
        f"PDF traités sans erreur : {successful}\n"
        f"PDF avec erreur : {errors}\n"
        f"PDF candidats OCR (à vérifier) : {ocr_candidates}\n"
        f"Nombre total de pages détectées : {total_pages}\n"
        f"CSV : {csv_path}\n"
        f"Textes extraits : {extracted_dir}\n"
        "\nATTENTION : le statut OCR est une estimation basée sur la quantité de texte extrait.\n"
        "Vérifiez visuellement quelques PDF avant de lancer un OCR en masse.\n"
    )
    summary_path.write_text(summary, encoding="utf-8")

    print("\n--- Résumé ---")
    print(summary)
    print("Terminé. Les PDF originaux n'ont pas été modifiés.")


if __name__ == "__main__":
    main()
