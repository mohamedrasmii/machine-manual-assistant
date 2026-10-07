#!/usr/bin/env python
# coding: utf-8

import os

import chromadb
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# Optional: load settings from a .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass



# SETTINGS


CHROMA_FOLDER = "chroma_db"
COLLECTION_NAME = "machine_manuals"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5
DISTANCE_THRESHOLD = 1.30


# ============================================================
# LLM SETTINGS (works with any OpenAI-compatible provider)
#
# Set these three values in a .env file or as environment variables:
#   LLM_BASE_URL  - the provider's OpenAI-compatible URL
#   LLM_API_KEY   - your key (any text is fine for Ollama)
#   LLM_MODEL     - the model name
#
# If nothing is set, it uses a local Ollama server (no key needed).
# See .env.example for ready-made values for each provider.
# ============================================================

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")

llm_client = OpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
    max_retries=0,
)

print(f"LLM: {LLM_MODEL} via {LLM_BASE_URL}")


def llm(instructions, user_input):
    """Send one request to the configured LLM and return the text."""

    response = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": user_input},
        ],
    )

    return response.choices[0].message.content



# EMBEDDING MODEL


print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)



# CHROMA


print("Connecting to Chroma...")

chroma_client = chromadb.PersistentClient(
    path=CHROMA_FOLDER
)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)

print("RAG system ready.")



# RETRIEVE


def retrieve(question, top_k=TOP_K):

    question_embedding = embedding_model.encode(question)

    results = collection.query(
        query_embeddings=[
            question_embedding.tolist()
        ],
        n_results=top_k
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    chunks = []
    print("\nQuestion:", question)
    print("Retrieved distances:", distances)

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        if distance <= DISTANCE_THRESHOLD:
            chunks.append({
                "text": document,
                "manual": metadata["manual"],
                "page": metadata["page"],
                "distance": distance
            })

    return chunks



# BUILD CONTEXT


def build_context(chunks):

    context = []

    for i, chunk in enumerate(chunks, start=1):

        context.append(
            f"""
SOURCE {i}
Manual: {chunk["manual"]}
Page: {chunk["page"]}

Content:
{chunk["text"]}
"""
        )

    return "\n".join(context)



# GENERATE ANSWER


def generate_answer(question, chunks):

    context = build_context(chunks)

    instructions = """
You are a machine-manual assistant.

Answer the user's question using ONLY
the provided manual excerpts.

Rules:

1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not contained in the excerpts, say:
   "I could not find this information in the manuals."
4. Give clear practical answers.
5. For procedures, use numbered steps.
6. Preserve machine parameters and values.
7. Identify the manual and page supporting the answer.
"""

    prompt = f"""
MANUAL EXCERPTS:

{context}

USER QUESTION:

{question}
"""

    return llm(instructions, prompt)



# COMPLETE RAG


def ask_machine(question):

    question_lower = question.lower().strip()

    
    # NORMAL CONVERSATION
    

    casual_messages = [
        "hi",
        "hello",
        "hey",
        "hi there",
        "hello there",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "how are you?",
        "thanks",
        "thank you",
        "who are you",
        "what can you do"
    ]

    try:

        if question_lower in casual_messages:

            answer_text = llm(
                """
You are a friendly machine-manual chatbot.

Respond naturally to casual conversation.
Do not mention the manuals unless relevant.
Do not provide sources for casual conversation.
Keep the response concise.
""",
                question
            )

            return {
                "answer": answer_text,
                "sources": []
            }

        
        # RAG
        
        chunks = retrieve(question)

        if not chunks:

            return {
                "answer": "I could not find this information in the manuals.",
                "sources": []
            }

        answer = generate_answer(
            question,
            chunks
        )

    except Exception as error:

        # Show a readable message in the chat instead of a server crash
        print("LLM error:", error)

        return {
            "answer": (
                "The language model could not be reached. "
                "Check LLM_BASE_URL, LLM_API_KEY and LLM_MODEL "
                "(and that Ollama is running, if you use it). "
                f"Details: {error}"
            ),
            "sources": []
        }

    sources = []

    for chunk in chunks:
        sources.append({
            "manual": chunk["manual"],
            "page": chunk["page"]
        })

    return {
        "answer": answer,
        "sources": sources
    }
