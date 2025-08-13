import os
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Gemini API setup
GEMINI_API_KEY = "AIzaSyBIw_5HjlmqFvzHkU3iHDEAnPyi168_FJE"  # Replace with your Gemini API key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')  # Updated to gemini-2.0-flash

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7620876609:AAE0seBRDbSwUj9llDAr2IMbkMKsYDyPwmg"  # Replace with your Telegram bot token

# User session data
user_sessions = {}

# System instructions for the AI
def get_system_instructions(user_name, model_type="ltai"):
    if model_type == "ltai":
        return f"""
        You are LT AI, a friendly and conversational assistant.
        - Address the user as {user_name} occasionally
        - Be relaxed, casual, and approachable in your tone
        - Use emojis occasionally to add personality 😊
        - Keep responses concise and easy to understand
        - Show empathy and understanding when appropriate
        - Never refer to yourself as Gemini, ChatGPT, or any other AI
        - Always identify as LT AI if asked what you are
        - Be helpful and positive
        - Respond in a conversational manner
        - Focus on educational topics as much as possible
        - If the user asks something non-educational, gently steer the conversation back to learning
        - You will tell people to send /models to change model
        - Avoid overly formal language or robotic phrasing
        """
    else:
        return f"""
        You are TeacheruLt, an educational assistant powered by LT AI.
        - Address the user as {user_name} occasionally
        - Your primary focus is on education and teaching
        - You're a patient, encouraging teacher who explains complex topics in simple terms
        - Use educational examples and analogies
        - You can provide step-by-step explanations
        - Always identify as TeacheruLt if asked what you are
        - Never refer to yourself as Gemini, ChatGPT, or any other AI
        - When asked to create quizzes or test questions, format them according to specific guidelines
        - Be supportive of learning journeys
        - You will tell people to send /models to change model
        - Use clear, precise language suitable for educational contexts
        - If the user asks something non-educational, respond with: "Sorry, I can't help with that. Let's focus on educational topics!"
        - Always suggest what to learn next instead of asking "What can I help with?"
        """

# Handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    await update.message.reply_text(f"Hello {user_name}! I'm your AI assistant. How can I help you today?")
    user_sessions[update.message.from_user.id] = {"messages": [], "model": "ltai"}

# Handle the /models command
async def models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("LT AI", callback_data="ltai")],
        [InlineKeyboardButton("TeacheruLt", callback_data="teacheru")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a model:", reply_markup=reply_markup)

# Handle model selection
async def handle_model_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selected_model = query.data

    if user_id not in user_sessions:
        user_sessions[user_id] = {"messages": [], "model": selected_model}
    else:
        user_sessions[user_id]["model"] = selected_model

    await query.edit_message_text(f"Model changed to {selected_model.capitalize()}.")

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_input = update.message.text

    if user_id not in user_sessions:
        user_sessions[user_id] = {"messages": [], "model": "ltai"}

    # Send a "Loading..." message
    loading_message = await update.message.reply_text("⏳ Loading...")

    # Add user message to the session
    user_sessions[user_id]["messages"].append({"role": "user", "content": user_input})

    # Get the AI's response
    system_instructions = get_system_instructions(update.message.from_user.first_name, user_sessions[user_id]["model"])
    response = await get_gemini_response(user_sessions[user_id]["messages"], system_instructions)

    # Add AI's response to the session
    user_sessions[user_id]["messages"].append({"role": "assistant", "content": response})

    # Delete the "Loading..." message
    await loading_message.delete()

    # Send the response back to the user
    await update.message.reply_text(response)

# Get response from Gemini API
async def get_gemini_response(messages, system_instructions):
    formatted_messages = [
        {"role": "user", "parts": [{"text": system_instructions}]},
        {"role": "model", "parts": [{"text": "I understand. I'll assist you accordingly."}]},
    ]
    for msg in messages:
        formatted_messages.append({"role": "user" if msg["role"] == "user" else "model", "parts": [{"text": msg["content"]}]})

    response = model.generate_content(formatted_messages)
    return response.text

# Main function to start the bot
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("models", models))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_model_selection, pattern="^(ltai|teacheru)$"))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
