import os
import requests
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from vector_store import VectorStore

load_dotenv()
CHAT_BOT_TOKEN = os.getenv("CHAT_BOT_TOKEN")
INDEX_PATH = "./faiss_index/index.faiss"
MESSAGES_PATH = "./data/messages.json"
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

# allow_rebuild=False for chat bot
vector_store = VectorStore(INDEX_PATH, MESSAGES_PATH, VECTOR_DIM, allow_rebuild=False)

MAX_CONTEXT_CHARS = 6000  # Limit context to avoid 413 errors

def needs_context(question: str) -> bool:
    keywords = [
        "from the channel", "recent messages", "recent opportunities",
        "posted", "forwarded", "in the channel", "show me", "latest"
    ]
    q = question.lower()
    return any(kw in q for kw in keywords)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "👋 Welcome to the Opportunity Assistant!\n\n"
        "This bot is currently in development. Sometimes responses may take a while, and you may encounter occasional errors.\n\n"
        "Ask me about scholarships, competitions, internships, or academic programs.\n\n"
        "Note: Sessions last only 1 day.\n\n"
        "Thank you for your patience and feedback!"
    )
    await update.message.reply_text(welcome)

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

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    if needs_context(question):
        top_msgs = vector_store.search(question, k=MAX_SEARCH_RESULTS)
        context_str = build_limited_context(top_msgs, MAX_CONTEXT_CHARS)
    else:
        context_str = ""
    answer = query_groq_llama(context_str, question)
    await update.message.reply_text(answer, parse_mode="Markdown")

app = ApplicationBuilder().token(CHAT_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.FORWARDED), handle_query))

if __name__ == "__main__":
    app.run_polling() 