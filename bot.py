import random
import requests
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load environment variables from .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

# In-memory data storage
users_data = {}

# Function to get user data
def get_user_data(user_id, first_name, last_name):
    if user_id not in users_data:
        users_data[user_id] = {
            "first_name": first_name,
            "last_name": last_name,
            "coins": 0,
            "streak": 0,
            "top_streak": 0,
            "current_character": None,
            "guess_count": 0,
            "correct_guesses": 0,
        }
    return users_data[user_id]

# Fetch a random anime character using Jikan API
def fetch_random_character():
    while True:
        try:
            url = "https://api.jikan.moe/v4/characters?page=1&limit=1000"
            response = requests.get(url)
            if response.status_code == 200:
                characters = response.json().get("data", [])
                if characters:
                    character = random.choice(characters)
                    return character["name"]
        except Exception:
            pass  # Ignore any errors and retry fetching

# Function to generate a fill-in-the-blanks hint like "g_ku"
def generate_hint(character):
    words = character.split(" ")  # Split into words
    hinted_words = []
    for word in words:
        hinted_word = "".join([c if random.random() > 0.5 else "_" for c in word])
        if hinted_word == "_" * len(word):  # Ensure at least one character is visible
            hinted_word = random.choice(word) + "_" * (len(word) - 1)
        hinted_words.append(hinted_word)
    return " ".join(hinted_words)

# Start command
def start(update: Update, context: CallbackContext):
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name or ""
    user_id = update.message.chat.id
    get_user_data(user_id, first_name, last_name)  # Initialize user data

    update.message.reply_text(
        "👋 Welcome to **Philo Guesser**! 🎮\n"
        "✨ I will send anime characters for you to guess. 🎉\n"
        "🔥 You have 5️⃣ attempts per character. Start guessing! 🧐"
    )
    send_new_character(update, context)

# Send a new character to the user
def send_new_character(update: Update, context: CallbackContext):
    user_id = update.message.chat.id
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name or ""
    user_data = get_user_data(user_id, first_name, last_name)

    # Fetch a new character
    character = fetch_random_character()
    user_data["current_character"] = character.lower()
    user_data["guess_count"] = 0

    # Send the first hint
    hint = generate_hint(character)
    update.message.reply_text(f"🧩 Guess the anime character: **{hint}**")

# Guess handler
def guess(update: Update, context: CallbackContext):
    user_id = update.message.chat.id
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name or ""
    user_data = get_user_data(user_id, first_name, last_name)
    guess = update.message.text.strip().lower()

    if not user_data["current_character"]:
        send_new_character(update, context)
        return

    user_data["guess_count"] += 1

    if guess == user_data["current_character"]:
        user_data["coins"] += 100
        user_data["correct_guesses"] += 1
        user_data["streak"] += 1
        user_data["top_streak"] = max(user_data["streak"], user_data["top_streak"])

        update.message.reply_text(
            f"🎉 **Correct!** You earned 💰 100 coins! 🎊\n"
            f"📈 Total coins: {user_data['coins']}\n"
            f"🔥 Streak: {user_data['streak']} 🔥"
        )
        send_new_character(update, context)
    else:
        if user_data["guess_count"] >= 5:
            user_data["streak"] = 0
            update.message.reply_text(
                f"❌ Out of attempts! 😔\n"
                f"The correct answer was: **{user_data['current_character']}**. 🤓\n"
                f"Let's try a new character! 🆕"
            )
            send_new_character(update, context)
        else:
            remaining_attempts = 5 - user_data["guess_count"]
            update.message.reply_text(
                f"❌ Wrong guess! 😅\n"
                f"⚡ Try again! Attempts left: {remaining_attempts}."
            )

# Profile command
def profile(update: Update, context: CallbackContext):
    user_id = update.message.chat.id
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name or ""
    user_data = get_user_data(user_id, first_name, last_name)

    update.message.reply_text(
        f"🧑 **Profile**:\n"
        f"📛 Name: {first_name} {last_name}\n"
        f"💰 Coins: {user_data['coins']}\n"
        f"✅ Correct Guesses: {user_data['correct_guesses']}\n"
        f"🔥 Current Streak: {user_data['streak']}\n"
        f"🌟 Top Streak: {user_data['top_streak']}"
    )

# Top command
def top(update: Update, context: CallbackContext):
    if not users_data:
        update.message.reply_text("⚠️ No players yet! Be the first to play! 🎮")
        return

    # Sort users by coins in descending order
    sorted_users = sorted(users_data.values(), key=lambda x: x["coins"], reverse=True)[:10]

    # Generate leaderboard
    leaderboard = []
    for i, user in enumerate(sorted_users):
        first_name = user["first_name"]
        last_name = user["last_name"]
        coins = user["coins"]
        leaderboard.append(f"{i + 1}. 🥇 {first_name} {last_name}: 💰 {coins} coins")

    leaderboard_text = "\n".join(leaderboard)
    update.message.reply_text(f"🏆 **Top Players**:\n{leaderboard_text}")

# Admin-only broadcast command
def broadcast(update: Update, context: CallbackContext):
    if str(update.message.chat.id) != OWNER_ID:
        update.message.reply_text("🚫 You do not have permission to use this command.")
        return

    message = " ".join(context.args)
    if not message:
        update.message.reply_text("⚠️ Please provide a message to broadcast.")
        return

    for user_id in users_data.keys():
        context.bot.send_message(chat_id=user_id, text=f"📢 **Broadcast**: {message}")

    update.message.reply_text("✅ Message broadcasted successfully!")

# Main function
def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("profile", profile))
    dp.add_handler(CommandHandler("top", top))
    dp.add_handler(CommandHandler("broadcast", broadcast))

    # Message handler for guesses
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, guess))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
