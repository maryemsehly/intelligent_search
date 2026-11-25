
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# 1. Définir les chemins
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

CHUNKS_FILE = PROJECT_DIR / "data" / "chunks" / "chunks.jsonl"

OUTPUT_DIR = PROJECT_DIR / "data" / "embeddings"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Charger les chunks
# --------------------------------------------------

chunks = []

with open(CHUNKS_FILE, "r", encoding="utf-8") as file:

    for line in file:

        chunk = json.loads(line)

        chunks.append(chunk)


print("Nombre de chunks chargés :", len(chunks))


# --------------------------------------------------
# 3. Extraire les textes
# --------------------------------------------------

texts = [
    chunk["text"]
    for chunk in chunks
]


# --------------------------------------------------
# 4. Charger le modèle
# --------------------------------------------------

model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# --------------------------------------------------
# 5. Transformer les textes en embeddings
# --------------------------------------------------

embeddings = model.encode(
    texts,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)


# --------------------------------------------------
# 6. Vérifier les embeddings
# --------------------------------------------------

print("\nDimensions des embeddings :", embeddings.shape)

print("Type des données :", embeddings.dtype)


# --------------------------------------------------
# 7. Sauvegarder les embeddings
# --------------------------------------------------

embeddings_file = OUTPUT_DIR / "embeddings.npy"

np.save(
    embeddings_file,
    embeddings
)


# --------------------------------------------------
# 8. Sauvegarder les métadonnées
# --------------------------------------------------

metadata_file = OUTPUT_DIR / "metadata.jsonl"

with open(metadata_file, "w", encoding="utf-8") as file:

    for chunk in chunks:

        metadata = {
            "chunk_id": chunk["chunk_id"],
            "source_pdf": chunk["source_pdf"],
            "source_file": chunk["source_file"],
            "page": chunk["page"],
            "chunk_in_page": chunk["chunk_in_page"],
            "text": chunk["text"]
        }

        file.write(
            json.dumps(metadata, ensure_ascii=False) + "\n"
        )


# --------------------------------------------------
# 9. Afficher le résultat
# --------------------------------------------------

print("\nEmbeddings sauvegardés :", embeddings_file)

print("Métadonnées sauvegardées :", metadata_file)

print("\nÉtape terminée avec succès !")
