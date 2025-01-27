import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")

def Insert_chat_history(username: str, message: str, chat_response: str, date: str):
    try:
        conn = sqlite3.connect(DB_HOST)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_history (username, message, chat_response, date) VALUES (?, ?, ?, ?)", (username, message, chat_response, date))
        conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error inserting document: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()