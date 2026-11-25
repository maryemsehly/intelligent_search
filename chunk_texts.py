
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CORPUS_DIR = BASE_DIR / "data" / "corpus_complet"
OUTPUT_FILE = BASE_DIR / "data" / "chunks" / "chunks.jsonl"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Reconnaître les marqueurs de page présents dans les textes OCR
PAGE_MARKER = re.compile(r"^===== PAGE (\d+) =====\s*$", re.MULTILINE)


def split_into_chunks(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Découper un texte en passages avec un chevauchement."""
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))

        # Éviter de couper au milieu d'un mot si possible
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start + size // 2:
                end = boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks


def extract_pages(text):
    """Retourner les pages si des marqueurs sont présents."""
    matches = list(PAGE_MARKER.finditer(text))

    if not matches:
        return [(None, text)]

    pages = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        page_text = text[start:end].strip()
        page_number = int(match.group(1))

        if page_text:
            pages.append((page_number, page_text))

    return pages


def main():
    if not CORPUS_DIR.exists():
        raise FileNotFoundError(
            f"Dossier introuvable : {CORPUS_DIR}"
        )

    files = sorted(CORPUS_DIR.glob("*.txt"))
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    total_chunks = 0
    empty_files = []
    sources_with_chunks = set()

    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        for file_path in files:
            text = file_path.read_text(
                encoding="utf-8", errors="replace"
            ).strip()

            if not text:
                empty_files.append(file_path.name)
                continue

            pages = extract_pages(text)

            for page_number, page_text in pages:
                chunks = split_into_chunks(page_text)

                for chunk_index, chunk in enumerate(chunks):
                    record = {
                        "chunk_id": f"{file_path.stem}_{total_chunks:06d}",
                        "source_pdf": f"{file_path.stem}.pdf",
                        "source_file": file_path.name,
                        "page": page_number,
                        "chunk_in_page": chunk_index,
                        "text": chunk,
                    }

                    output.write(
                        json.dumps(record, ensure_ascii=False) + "\n"
                    )

                    total_chunks += 1
                    sources_with_chunks.add(file_path.name)

    print("\n===== BILAN DU DECOUPAGE =====")
    print(f"Fichiers texte trouvés : {len(files)}")
    print(f"Rapports ayant au moins un chunk : {len(sources_with_chunks)}")
    print(f"Nombre total de chunks : {total_chunks}")
    print(f"Fichiers vides : {len(empty_files)}")
    print(f"Fichier de sortie : {OUTPUT_FILE}")

    if empty_files:
        print("Fichiers vides détectés :")
        for name in empty_files[:10]:
            print(" -", name)


if __name__ == "__main__":
    main()
