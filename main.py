from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackContext, CallbackQueryHandler,
    MessageHandler, filters
)
from config import TELEGRAM_TOKEN
from database import Database
from llm_handler import LLMHandler
import asyncio

db = Database()
llm = LLMHandler()

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome to AI Tutor! 🎓\n\n"
        "Use these commands to interact with me:\n"
        "/learn <topic> - Start learning a new topic\n"
        "/quiz [instructions] - Take a quiz (optionally with specific instructions)\n"
        "/progress - View your learning progress\n"
        "/topics - See your past topics and recommendations\n"
        "/help - Show this help message"
    )

async def learn(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Please specify a topic! Example: /learn Python")
        return
    
    topic = " ".join(context.args)
    user_id = update.message.from_user.id
    normalized_topic = db.set_user_topic(user_id, topic)
    
    await update.message.reply_text(
        f"Great! You're now learning {normalized_topic}. "
        f"Use /quiz to test your knowledge!"
    )

async def quiz(update: Update, context: CallbackContext, retry: bool = False):
    user_id = update.message.from_user.id
    topic = db.get_user_topic(user_id)
    
    if not topic:
        await update.message.reply_text(
            "Please select a topic first using /learn <topic>"
        )
        return

    progress = db.get_progress(user_id)
    difficulty = progress.get(topic, 0.0)
    
    # Get optional instructions from the command
    instructions = " ".join(context.args) if context.args else ""
    
    quiz_data = llm.generate_quiz(topic, difficulty, instructions)
    if not quiz_data:
        if not retry:
            await quiz(update, context, retry=True)
        else:
            await update.message.reply_text("Sorry, I couldn't generate a quiz right now. Please try again.")
        return

    context.user_data['quiz'] = quiz_data
    context.user_data['current_question'] = 0
    context.user_data['score'] = 0
    
    await send_question(update, context)

async def send_question(update: Update, context: CallbackContext):
    quiz_data = context.user_data['quiz']
    current = context.user_data['current_question']
    
    if current >= len(quiz_data):
        score = context.user_data['score']
        total = len(quiz_data)
        percentage = (score / total) * 100
        
        user_id = update.effective_user.id
        topic = db.get_user_topic(user_id)
        db.update_progress(user_id, topic, percentage / 100)
        
        await update.effective_message.reply_text(
            f"Quiz completed! Your score: {score}/{total} ({percentage:.1f}%)"
        )
        return

    question = quiz_data[current]
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(
            option, callback_data=f"quiz_{current}_{i}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        f"Question {current + 1}:\n{question['question']}", 
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action = data[0]
    
    if action == 'quiz':
        _, q_num, ans = data
        q_num, ans = int(q_num), int(ans)
        
        if ans == context.user_data['quiz'][q_num]['correct_answer']:
            context.user_data['score'] += 1
            await query.message.reply_text("✅ Correct!")
        else:
            correct = context.user_data['quiz'][q_num]['options'][
                context.user_data['quiz'][q_num]['correct_answer']
            ]
            await query.message.reply_text(f"❌ Wrong! The correct answer was: {correct}")
        
        context.user_data['current_question'] += 1
        await send_question(update, context)
    elif action == 'learn':
        topic_idx = int(data[1])
        # Get the topic from user_data or use default topics
        topics = context.user_data.get('recommended_topics', ["Python", "JavaScript", "Machine Learning"])
        if topic_idx < len(topics):
            topic = topics[topic_idx]
            user_id = update.effective_user.id
            normalized_topic = db.set_user_topic(user_id, topic)
            await query.message.reply_text(
                f"Great! You're now learning {normalized_topic}. "
                f"Use /quiz to test your knowledge!"
            )

async def progress(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    progress_data = db.get_progress(user_id)
    
    if not progress_data:
        await update.message.reply_text("You haven't completed any quizzes yet!")
        return
    
    message = "Your Learning Progress:\n\n"
    for topic, score in progress_data.items():
        percentage = score * 100
        level = "🟢" if score >= 0.7 else "🟡" if score >= 0.3 else "🔴"
        message += f"{topic}: {percentage:.1f}% {level}\n"
    
    await update.message.reply_text(message)

async def topics(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    progress_data = db.get_progress(user_id)
    past_topics = list(progress_data.keys()) if progress_data else []
    
    message = "Your Learning History:\n"
    if past_topics:
        for topic in past_topics:
            score = progress_data[topic] * 100
            level = "🟢" if score >= 70 else "🟡" if score >= 30 else "🔴"
            message += f"• {topic}: {score:.1f}% {level}\n"
    else:
        message += "No topics studied yet.\n"
    
    # Get recommendations
    if past_topics:
        message += "\nRecommended Topics:\n"
        recommendations = llm.get_topic_recommendations(past_topics)[:3]  # Limit to 3 recommendations
        keyboard = []
        for i, topic in enumerate(recommendations):
            message += f"• {topic}\n"
            # Use a simple index as callback data
            keyboard.append([InlineKeyboardButton(
                f"Learn {topic}", callback_data=f"learn_{i}"
            )])
        
        if keyboard:  # Only add reply_markup if we have recommendations
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message)
    else:
        suggestions = ["Python", "JavaScript", "Machine Learning"]  # Default suggestions
        message += "\nSuggested Topics to Start:\n"
        keyboard = []
        for i, topic in enumerate(suggestions):
            message += f"• {topic}\n"
            keyboard.append([InlineKeyboardButton(
                f"Learn {topic}", callback_data=f"learn_{i}"
            )])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)

async def help_command(update: Update, context: CallbackContext):
    await start(update, context)

async def handle_message(update: Update, context: CallbackContext):
    if update.message.text.startswith('/'):  # Ignore command messages
        return
        
    user_id = update.message.from_user.id
    current_topic = db.get_user_topic(user_id)
    
    if not current_topic:
        await update.message.reply_text(
            "Please select a topic first using /learn <topic> before asking questions!"
        )
        return
    
    question = update.message.text
    response = llm.answer_question(current_topic, question)
    await update.message.reply_text(response)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("learn", learn))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("progress", progress))
    app.add_handler(CommandHandler("topics", topics))
    
    # Callback and message handlers
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^quiz_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()