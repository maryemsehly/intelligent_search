
from pathlib import Path
import csv
import pymupdf

# Dossier du projet
BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "reports" / "ocr_output"
TEXT_DIR = BASE_DIR / "data" / "ocr_text"
MANIFEST_PATH = BASE_DIR / "reports" / "ocr_text_manifest.csv"

def main():
    # Créer les dossiers nécessaires
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Chercher les PDF produits par l'OCR
    pdf_files = sorted(PDF_DIR.glob("*_ocr.pdf"))

    if not pdf_files:
        print(f"Aucun PDF OCR trouvé dans : {PDF_DIR}")
        return

    results = []

    for pdf_path in pdf_files:
        txt_path = TEXT_DIR / f"{pdf_path.stem}.txt"
        print(f"\nExtraction : {pdf_path.name}")

        try:
            pages_text = []
            with pymupdf.open(pdf_path) as doc:
                page_count = len(doc)

                for page_number, page in enumerate(doc, start=1):
                    text = page.get_text("text").strip()
                    pages_text.append(
                        f"===== PAGE {page_number} =====\n\n{text}\n"
                    )

            full_text = "\n\n".join(pages_text)
            txt_path.write_text(full_text, encoding="utf-8")

            char_count = len(full_text)
            status = "OK"
            error = ""

            print(f"  Pages : {page_count}")
            print(f"  Caractères extraits : {char_count}")
            print(f"  Fichier créé : {txt_path.name}")

        except Exception as exc:
            page_count = 0
            char_count = 0
            status = "ERREUR"
            error = str(exc)

            print(f"  Erreur : {error}")

        results.append({
            "pdf_source": pdf_path.name,
            "fichier_texte": str(txt_path),
            "nombre_pages": page_count,
            "nombre_caracteres": char_count,
            "statut": status,
            "erreur": error,
        })

    # Enregistrer le bilan de l'extraction
    with MANIFEST_PATH.open("w", newline="", encoding="utf-8-sig") as csvfile:
        fieldnames = [
            "pdf_source",
            "fichier_texte",
            "nombre_pages",
            "nombre_caracteres",
            "statut",
            "erreur",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 50)
    print(f"PDF traités : {len(results)}")
    print(f"Succès : {sum(r['statut'] == 'OK' for r in results)}")
    print(f"Erreurs : {sum(r['statut'] == 'ERREUR' for r in results)}")
    print(f"Textes : {TEXT_DIR}")
    print(f"Journal : {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
