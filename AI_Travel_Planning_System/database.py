import psycopg
import streamlit as st

# Database Connection
DATABASE_URL = st.secrets["DATABASE_URL"]

connection = psycopg.connect(
    DATABASE_URL,
    autocommit=True
)


# Create Table
def create_conversation_table():
    with connection.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS travel_conversations (
            id SERIAL PRIMARY KEY,
            thread_id TEXT NOT NULL,
            user_query TEXT NOT NULL,
            final_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)


def save_conversation(
    thread_id,
    user_query,
    final_response
):
    with connection.cursor() as cur:

        cur.execute(
            """
            INSERT INTO travel_conversations
            (
                thread_id,
                user_query,
                final_response
            )

            VALUES (%s,%s,%s)
            """,
            (
                thread_id,
                user_query,
                final_response
            )
        )