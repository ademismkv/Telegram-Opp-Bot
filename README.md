# Opp_bot: Telegram Opportunity Assistant

This project is a Telegram-based assistant that uses LLaMA (via Groq) and FAISS to answer user queries based on Telegram channel messages.

## Project Structure

```
Opp_bot/
│
├── data/
│   └── messages.json
├── faiss_index/
│   └── index.faiss
├── .env
├── download_messages.py         # (local only, downloads messages)
├── bot_forwarder.py             # Forward bot: ingests new messages
├── bot_chat.py                  # Chatbot: answers user queries
├── vector_store.py              # FAISS and embedding logic
├── requirements.txt
└── README.md
```

## Setup

1. **Clone the repo and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Prepare your `.env` file:**
   See below for required variables.

3. **Download initial messages (local only):**
   ```bash
   python download_messages.py
   ```
   This will create `./data/messages.json`.

4. **Create required directories:**
   ```bash
   mkdir -p data faiss_index
   ```

## .env Example

```
TELEGRAM_API_ID="..."
TELEGRAM_API_HASH="..."
GROQ_API_KEY="..."
FORWARD_BOT_TOKEN="..."
CHAT_BOT_TOKEN="..."
GROQ_MODEL="llama3-8b-8192"
VECTOR_DIMENSION="384"
MAX_SEARCH_RESULTS="20"
SYSTEM_PROMPT="You are a smart and helpful assistant..."
HOST="0.0.0.0"
PORT="8000"
MAX_MESSAGE_AGE_DAYS="1095"
MAX_MESSAGES_PER_CHANNEL="10000"
```

## Running the Bots

### Forward Bot
Listens for new forwarded messages and updates the vector store.
```bash
python bot_forwarder.py
```

### Chat Bot
Answers user queries using the vector store and Groq LLaMA.
```bash
python bot_chat.py
```

## Deployment
- Deploy both bots as separate Railway services.
- Ensure `.env` and required directories/files are present in each service.

## Notes
- Uses [python-telegram-bot](https://core.telegram.org/bots/api) for async bot handling.
- All secrets/config are loaded from `.env`.
- Make sure `faiss_index/` and `data/` directories exist.
- You can run both bots in separate processes or deploy as separate Railway services. 