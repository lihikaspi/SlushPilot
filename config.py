import os
import dotenv

dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
DB_PROJECT_URL = os.getenv("DB_PROJECT_URL")
DB_API_KEY = os.getenv("DB_API_KEY")

BASE_URL = "https://api.llmod.ai/v1"
CHAT_MODEL = "RPRTHPB-gpt-5-mini"
EMBED_MODEL = "RPRTHPB-text-embedding-3-small"

ARCHITECTURE_IMAGE = "images/SlushPilot.png"

PROJECT_STATUS = {
    "new": {"label": "New Project", "color": "gray"},
    "publisher_search" : {"label": "Publisher Search", "color": "yellow"},
    "drafting": {"label": "Letter Writing", "color": "blue"}
}

LETTER_STATUS = {
    "new": {"label": "New Letter/Unwritten", "color": "gray"},
    "draft": {"label": "Drafted", "color": "blue"},
    "sent": {"label": "Sent", "color": "green"},
    "respond": {"label": "Response Received", "color": "red"},
    "rejected": {"label": "Rejected", "color": "black"}
}