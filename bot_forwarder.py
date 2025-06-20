import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from vector_store import VectorStore

load_dotenv()
FORWARD_BOT_TOKEN = os.getenv("FORWARD_BOT_TOKEN")
INDEX_PATH = "./faiss_index/index.faiss"
MESSAGES_PATH = "./data/messages.json"
VECTOR_DIM = int(os.getenv("VECTOR_DIMENSION", 384))

# allow_rebuild=True for forwarder bot
vector_store = VectorStore(INDEX_PATH, MESSAGES_PATH, VECTOR_DIM, allow_rebuild=True)

async def handle_forwarded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg and msg.text and msg.forward_date:
        vector_store.add_message(msg.text)
        await msg.reply_text("Message added to vector store.")

app = ApplicationBuilder().token(FORWARD_BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, handle_forwarded))

if __name__ == "__main__":
    app.run_polling() 