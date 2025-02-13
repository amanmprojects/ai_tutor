# AI Tutor Telegram Bot

A Telegram bot that serves as an intelligent tutoring system, providing personalized learning experiences and quizzes across various topics.

## Features

- 🎓 Personalized Learning: Choose any topic to study
- 📝 Interactive Quizzes: Test your knowledge with adaptive difficulty
- 📊 Progress Tracking: Monitor your learning journey
- 🤖 AI-Powered: Uses Groq's LLM for intelligent interactions
- 💡 Topic Recommendations: Get suggestions based on your learning history

## Setup

1. Install required dependencies:
```sh
pip install -r requirements.txt
```

2. Create a .env file with required API keys:
```
TELEGRAM_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
```

3. Run the bot:
```sh
python main.py
```

## Commands

- `/start` - Initialize the bot and see available commands
- `/learn <topic>` - Start learning a new topic
- `/quiz` - Take a quiz on your current topic
- `/progress` - View your learning progress
- `/topics` - See your past topics and get recommendations
- `/help` - Display help message

## Technical Details

- Built with Python-Telegram-Bot v20.7
- Uses Groq's deepseek-r1-distill-llama-70b model for AI responses
- SQLite database for storing user progress and topic data
- Supports topic normalization for consistent tracking

## Project Structure

- main.py - Core bot logic and command handlers
- llm_handler.py - AI model integration and quiz generation
- database.py - Database operations and topic management
- config.py - Configuration and environment variables

## Requirements

- Python 3.x
- python-telegram-bot
- groq
- python-dotenv
- SQLite3

## License

MIT License
