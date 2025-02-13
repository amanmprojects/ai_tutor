from dotenv import load_dotenv
import os

load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Groq API Key
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Model configuration
LLM_MODEL = "deepseek-r1-distill-llama-70b"

# Database configuration
DB_PATH = "data/user_data.db"

# Ensure data directory exists
os.makedirs('data', exist_ok=True)