
from pathlib import Path
import json
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
CHUNKS_FILE = BASE_DIR / "data" / "chunks" / "chunks.jsonl"
INDEX_DIR = BASE_DIR / "data" / "vector_index"

# Modèle multilingue : français, arabe et de nombreuses autres langues.
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Fichier introuvable : {CHUNKS_FILE}")

    chunks = []
    with CHUNKS_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                chunks.append(json.loads(line))

    if not chunks:
        raise ValueError("Aucun chunk trouvé.")

    texts = [chunk["text"] for chunk in chunks]

    print(f"Nombre de chunks : {len(texts)}")
    print(f"Chargement du modèle : {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print("Calcul des embeddings...")
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    embeddings = np.asarray(embeddings, dtype="float32")

    # Les vecteurs normalisés permettent une recherche par produit scalaire
    # équivalente à une comparaison cosinus.
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    index_path = INDEX_DIR / "faiss.index"
    metadata_path = INDEX_DIR / "chunks_metadata.pkl"

    faiss.write_index(index, str(index_path))

    with metadata_path.open("wb") as file:
        pickle.dump(chunks, file)

    print("\nIndexation terminée !")
    print(f"Vecteurs indexés : {index.ntotal}")
    print(f"Dimension des vecteurs : {embeddings.shape[1]}")
    print(f"Index : {index_path}")
    print(f"Métadonnées : {metadata_path}")


if __name__ == "__main__":
    main()
