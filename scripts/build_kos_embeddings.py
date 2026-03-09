"""Utility to preprocess the KOS_DOC reference files and build a vector database of embeddings.

Usage:
    python scripts/build_kos_embeddings.py

This script will walk through the `reference_docs/KOS_DOC` directory,
read each HTML/text file, split it into segments, and compute an embedding
for each segment. The resulting vectors and their source text will be
stored in a local vector database (e.g. FAISS or Chroma). Because the
KOS documentation is static and rarely changes, this process needs to be
run only once unless the docs are updated.

The generated database can then be queried by the "knowledge_search" tool
described in the agent architecture; agents will call that tool to fetch
relevant passages.
"""

import os
import glob

# note: actual embedding requires an external library such as OpenAI's
# or any other provider; this file is a template showing the intended
# structure.  The user should install the appropriate packages and supply
# an API key if using a cloud service.

from pathlib import Path

# actual embedding imports
import chromadb
from chromadb.config import Settings

# attempt to import OpenAI; optional
try:
    from openai import OpenAI
    has_openai = True
except ImportError:
    has_openai = False

# attempt to load local sentence-transformers model
try:
    from sentence_transformers import SentenceTransformer
    local_model = SentenceTransformer("all-MiniLM-L6-v2")
    has_local = True
except ImportError:
    has_local = False

# choose embedding provider
client = None
use_openai = False
if has_openai and os.environ.get("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    use_openai = True
elif not has_local:
    raise RuntimeError("No embedding provider available. Install sentence-transformers or set OPENAI_API_KEY and install openai.")

DOC_DIR = Path(__file__).parent.parent / "reference_docs" / "KOS_DOC"
OUTPUT_DB = Path(__file__).parent.parent / "data" / "kos_embeddings.db"


def extract_texts_from_html(path: Path):
    # simplistic text extraction; in reality you may want to use BeautifulSoup
    texts = []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # split on headings/cr-lf for coarse segments
    for part in content.split("\n\n"):
        cleaned = part.strip()
        if cleaned:
            texts.append(cleaned)
    return texts


def main():
    all_segments = []
    for file in DOC_DIR.rglob("*.html"):
        segments = extract_texts_from_html(file)
        for seg in segments:
            all_segments.append((file.name, seg))
    # now compute embeddings and store in vector db
    texts = [seg for (_, seg) in all_segments]
    if not texts:
        print("No segments found, nothing to embed.")
        return

    # compute embeddings using selected provider
    if use_openai:
        resp = client.embeddings.create(input=texts, model="text-embedding-3-small")
        vectors = [r["embedding"] for r in resp["data"]]
    else:
        # local model
        vectors = local_model.encode(texts, show_progress_bar=True).tolist()

    # create Chromadb collection
    chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=str(OUTPUT_DB.parent)))
    collection = chroma_client.get_or_create_collection(name="kos_doc")
    # store documents with metadata (filename)
    metadatas = [{"source": file} for (file, _) in all_segments]
    ids = [str(i) for i in range(len(texts))]
    collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=vectors)
    chroma_client.persist()
    print(f"Indexed {len(texts)} passages into Chromadb at {OUTPUT_DB.parent}")


if __name__ == "__main__":
    main()
