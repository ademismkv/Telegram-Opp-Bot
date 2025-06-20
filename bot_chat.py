import os
import requests
import time
import psycopg2
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from vector_store import VectorStore

load_dotenv()
CHAT_BOT_TOKEN = os.getenv("CHAT_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
VECTOR_DIM = int(os.getenv("VECTOR_DIMENSION", 384))
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", 20))
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT") or (
    "You are a smart and helpful assistant that specializes in identifying and explaining educational opportunities, including scholarships, internships, competitions, and academic programs.\n\n"
    "**Formatting Instructions:**\n"
    "- Always answer in a clear, structured Q&A format.\n"
    "- Use bold section headers (e.g., **General Information & Getting Started**).\n"
    "- For each user question, provide a concise, relevant answer.\n"
    "- Use bullet points for lists.\n"
    "- Use markdown formatting for clarity.\n"
    "- Separate each Q&A pair with a blank line.\n"
    "- If the context is insufficient, respond politely and ask for clarification.\n"
    "- Do NOT include references to specific people, testimonials, or consultancy companies unless the user explicitly asks for them.\n"
    "- Avoid promotional or marketing language."
)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

MAX_CONTEXT_CHARS = 6000  # Limit context to avoid 413 errors

class DBVectorStore:
    def __init__(self, db_url, dim):
        self.db_url = db_url
        self.dim = dim
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(dim)
        self.messages = []

    def load_from_db(self):
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        cur.execute("SELECT message_text, embedding FROM telegram_messages")
        rows = cur.fetchall()
        self.messages = [row[0] for row in rows]
        embeddings = np.array([row[1] for row in rows], dtype=np.float32)
        if len(embeddings) > 0:
            self.index = faiss.IndexFlatL2(self.dim)
            self.index.add(embeddings)
        cur.close()
        conn.close()

    def search(self, query, k=20):
        emb = self.model.encode([query])
        D, I = self.index.search(np.array(emb, dtype=np.float32), k)
        return [self.messages[i] for i in I[0] if i < len(self.messages)]

def query_groq_llama(context, question, retries=3, delay=2):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    data = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]
    }
    for attempt in range(retries):
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except requests.exceptions.ChunkedEncodingError:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            return "Sorry, there was a network error while contacting the LLaMA API. Please try again."
        except requests.exceptions.RequestException as e:
            return f"Sorry, there was an error: {e}"

def build_limited_context(messages, max_chars):
    context = []
    total = 0
    for msg in messages:
        if total + len(msg) > max_chars:
            break
        context.append(msg)
        total += len(msg)
    return "\n---\n".join(context)

vector_store = DBVectorStore(DATABASE_URL, VECTOR_DIM)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vector_store.load_from_db()
    welcome = (
        "👋 Welcome to the Opportunity Assistant!\n\n"
        "This bot is currently in development. Sometimes responses may take a while, and you may encounter occasional errors.\n\n"
        "Ask me about scholarships, competitions, internships, or academic programs.\n\n"
        "Note: Sessions last only 1 day.\n\n"
        "Thank you for your patience and feedback!"
    )
    await update.message.reply_text(welcome)

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    top_msgs = vector_store.search(question, k=MAX_SEARCH_RESULTS)
    context_str = build_limited_context(top_msgs, MAX_CONTEXT_CHARS)
    answer = query_groq_llama(context_str, question)
    await update.message.reply_text(answer, parse_mode="Markdown")

app = ApplicationBuilder().token(CHAT_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.FORWARDED), handle_query))

if __name__ == "__main__":
    app.run_polling() 