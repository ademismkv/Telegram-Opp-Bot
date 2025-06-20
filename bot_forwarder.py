import os
import psycopg2
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import date

load_dotenv()
FORWARD_BOT_TOKEN = os.getenv("FORWARD_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
VECTOR_DIM = int(os.getenv("VECTOR_DIMENSION", 384))

model = SentenceTransformer("all-MiniLM-L6-v2")

def insert_message_to_db(message_text, embedding):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO telegram_messages (message_text, embedding, created_at)
        VALUES (%s, %s, %s)
        """,
        (message_text, embedding.tolist(), date.today())
    )
    conn.commit()
    cur.close()
    conn.close()

async def handle_forwarded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg and msg.text and msg.forward_date:
        embedding = model.encode([msg.text])[0]
        insert_message_to_db(msg.text, embedding)
        await msg.reply_text("Message added to database.")

app = ApplicationBuilder().token(FORWARD_BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, handle_forwarded))

if __name__ == "__main__":
    app.run_polling() 