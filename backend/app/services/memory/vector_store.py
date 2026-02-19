"""
Vector Memory Store using ChromaDB.

Provides long-term semantic memory across all chat sessions.
Messages are embedded and stored so the agent can recall relevant
facts from past conversations via similarity search.
"""

import chromadb
from chromadb.config import Settings
from datetime import datetime
from pathlib import Path
import os


class VectorMemory:
    """ChromaDB-backed semantic memory for the inventory chatbot."""

    def __init__(self, persist_dir: str = None):
        """
        Initialize ChromaDB persistent client.

        Args:
            persist_dir: Directory for ChromaDB storage.
                         Defaults to 'data/chromadb' relative to project root.
        """
        if persist_dir is None:
            # Store alongside the SQLite database
            base_dir = Path(__file__).resolve().parents[4]  # project root
            persist_dir = str(base_dir / "data" / "chromadb")

        os.makedirs(persist_dir, exist_ok=True)

        try:
            self._client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name="chat_memory",
                metadata={"description": "Long-term chat conversation memory"},
            )
            self._available = True
        except Exception as e:
            print(f"[VectorMemory] ChromaDB init failed, running without vector memory: {e}")
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        timestamp: datetime = None,
    ) -> None:
        """
        Embed and store a single chat message.

        Args:
            session_id: The chat session this message belongs to.
            role: 'user' or 'assistant'.
            content: The text content of the message.
            timestamp: When the message was sent.
        """
        if not self._available or not content or not content.strip():
            return

        if timestamp is None:
            timestamp = datetime.now()

        doc_id = f"{session_id}_{role}_{timestamp.strftime('%Y%m%d%H%M%S%f')}"
        ts_str = timestamp.strftime("%Y-%m-%d %H:%M")

        try:
            self._collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[{
                    "session_id": session_id,
                    "role": role,
                    "timestamp": ts_str,
                }],
            )
        except Exception as e:
            print(f"[VectorMemory] Failed to store message: {e}")

    def search_relevant(self, query: str, n_results: int = 5, exclude_session: str = None) -> list[dict]:
        """
        Search for past messages semantically similar to the query.

        Args:
            query: The user's current question.
            n_results: Max number of results to return.
            exclude_session: Optionally exclude the current session
                             (since it's already loaded via SQLite).

        Returns:
            List of dicts with keys: content, role, timestamp, session_id.
        """
        if not self._available or not query or not query.strip():
            return []

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results * 2,  # fetch extra, then filter
            )

            matches = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    sid = meta.get("session_id", "")

                    # Skip messages from the current session (already in SQLite context)
                    if exclude_session and sid == exclude_session:
                        continue

                    matches.append({
                        "content": doc,
                        "role": meta.get("role", "unknown"),
                        "timestamp": meta.get("timestamp", "unknown"),
                        "session_id": sid,
                    })

                    if len(matches) >= n_results:
                        break

            return matches

        except Exception as e:
            print(f"[VectorMemory] Search failed: {e}")
            return []

    def get_stats(self) -> dict:
        """Return basic stats about the vector store."""
        if not self._available:
            return {"available": False, "count": 0}

        try:
            return {
                "available": True,
                "count": self._collection.count(),
            }
        except Exception:
            return {"available": False, "count": 0}


# Singleton instance
_memory_instance: VectorMemory | None = None


def get_vector_memory() -> VectorMemory:
    """Get or create the singleton VectorMemory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = VectorMemory()
    return _memory_instance
