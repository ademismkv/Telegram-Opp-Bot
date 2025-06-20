import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self, index_path, messages_path, dim, allow_rebuild=False):
        self.index_path = index_path
        self.messages_path = messages_path
        self.dim = dim
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(dim)
        self.messages = []
        self.allow_rebuild = allow_rebuild
        self.load()

    def load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        if os.path.exists(self.messages_path):
            with open(self.messages_path, "r", encoding="utf-8") as f:
                raw_messages = json.load(f)
                # If messages are dicts, extract the 'text' field
                if raw_messages and isinstance(raw_messages[0], dict) and 'text' in raw_messages[0]:
                    self.messages = [msg['text'] for msg in raw_messages if 'text' in msg]
                else:
                    self.messages = raw_messages
        # Only rebuild if allowed and index is missing
        if self.allow_rebuild and len(self.messages) > 0 and self.index.ntotal == 0:
            self.rebuild_index()

    def rebuild_index(self):
        embeddings = self.model.encode(self.messages, show_progress_bar=True)
        self.index = faiss.IndexFlatL2(self.dim)
        self.index.add(np.array(embeddings, dtype=np.float32))
        self.save()

    def add_message(self, message):
        self.messages.append(message)
        emb = self.model.encode([message])
        self.index.add(np.array(emb, dtype=np.float32))
        self.save()

    def search(self, query, k=20):
        emb = self.model.encode([query])
        D, I = self.index.search(np.array(emb, dtype=np.float32), k)
        return [self.messages[i] for i in I[0] if i < len(self.messages)]

    def save(self):
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.messages_path, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2) 