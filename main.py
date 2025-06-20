import os
from multiprocessing import Process

def run_forwarder():
    from bot_forwarder import app as forwarder_app
    forwarder_app.run_polling()

def run_chat():
    from bot_chat import app as chat_app
    chat_app.run_polling()

if __name__ == "__main__":
    p1 = Process(target=run_forwarder)
    p2 = Process(target=run_chat)
    p1.start()
    p2.start()
    p1.join()
    p2.join() 