#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pathlib import Path
import fitz
import chromadb
from sentence_transformers import SentenceTransformer


# SETTINGS


MANUALS_FOLDER = Path("manuals")
CHROMA_FOLDER = "chroma_db"
COLLECTION_NAME = "machine_manuals"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# LOAD PDF


def load_pdf(pdf_path):
    """
    Extract text from a PDF page by page.

    Returns:
        list of dictionaries containing:
        - manual name
        - page number
        - text
    """

    document = fitz.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):

        text = page.get_text("text").strip()

        # Ignore completely empty pages
        if text:
            pages.append({
                "manual": pdf_path.name,
                "page": page_number,
                "text": text
            })

    document.close()

    return pages



# LOAD ALL PDF MANUALS


def load_all_pdfs(folder_path):
    """
    Find and read every PDF inside the Manuals folder.
    """

    pdf_files = sorted(folder_path.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files were found in: {folder_path.resolve()}"
        )

    all_pages = []

    print(f"Found {len(pdf_files)} PDF files.\n")

    for pdf_file in pdf_files:

        print(f"Reading: {pdf_file.name}")

        pages = load_pdf(pdf_file)

        print(f"  Pages with text: {len(pages)}")

        all_pages.extend(pages)

    return all_pages



# CREATE CHUNKS


def create_chunks(pages):
    """
    Split page text into overlapping chunks.

    Each chunk keeps its manual name and page number.
    """

    chunks = []

    chunk_id = 0

    for page in pages:

        text = page["text"]

        start = 0

        while start < len(text):

            end = start + CHUNK_SIZE

            if end < len(text):
                while end > start and text[end] != " ":
                    end -= 1

            chunk_text = text[start:end].strip()

            if chunk_text:

                chunks.append({
                    "id": f"chunk_{chunk_id}",
                    "text": chunk_text,
                    "manual": page["manual"],
                    "page": page["page"]
                })

                chunk_id += 1

            start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks



# CREATE VECTOR DATABASE


def create_vector_database(chunks):

    print("\nLoading embedding model...")

    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Creating embeddings...")

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

   
    # Create Chroma client
    

    client = chromadb.PersistentClient(
        path=CHROMA_FOLDER
    )

    # Delete old collection if it exists
    try:
        client.delete_collection(COLLECTION_NAME)
        print("\nOld collection deleted.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME
    )

   
    # Prepare metadata
    

    ids = []

    metadatas = []

    documents = []

    for chunk in chunks:

        ids.append(chunk["id"])

        documents.append(chunk["text"])

        metadatas.append({
            "manual": chunk["manual"],
            "page": chunk["page"]
        })

    
    # Store everything in Chroma
    

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

    print(f"\nStored {len(chunks)} chunks in Chroma.")

    return collection



# MAIN


if __name__ == "__main__":

    print("======================================")
    print(" MACHINE MANUAL RAG - INGESTION")
    print("======================================\n")

    # 1. Read all PDFs
    pages = load_all_pdfs(MANUALS_FOLDER)

    print(f"\nTotal pages loaded: {len(pages)}")

    # 2. Create chunks
    chunks = create_chunks(pages)

    print(f"Total chunks created: {len(chunks)}")

    # 3. Create vector database
    create_vector_database(chunks)

    print("\n======================================")
    print(" INGESTION COMPLETED")
    print("======================================")

