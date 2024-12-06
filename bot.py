import random
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables from .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

# In-memory data storage
CHARACTER_LIST = [
    "Naruto Uzumaki", "Sasuke Uchiha", "Sakura Haruno", "Kakashi Hatake"
]
SUDO_USERS = set()
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

# Fetch a random character from the list
def fetch_random_character():
    return random.choice(CHARACTER_LIST)

# Generate a hint for the character name
def generate_hint(character):
    words = character.split(" ")
    hinted_words = []
    for word in words:
        hinted_word = "".join([c if random.random() > 0.5 else "_" for c in word])
        if hinted_word == "_" * len(word):
            hinted_word = random.choice(word) + "_" * (len(word) - 1)
        hinted_words.append(hinted_word)
    return " ".join(hinted_words)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name or ""
    user_id = update.effective_chat.id
    get_user_data(user_id, first_name, last_name)

    await update.message.reply_text(
        "👋 Welcome to **Naruto Guess Bot**! 🎮\n"
        "✨ I will send anime characters for you to guess. 🎉\n"
        "🔥 You have 5️⃣ attempts per character. Start guessing! 🧐\n"
        "🍀 Test your knowledge of the Naruto universe and aim for the top streak!"
    )
    await send_new_character(update, context)

# Send a new character to the user
async def send_new_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name or ""
    user_data = get_user_data(user_id, first_name, last_name)

    character = fetch_random_character()
    user_data["current_character"] = character.lower()
    user_data["guess_count"] = 0

    hint = generate_hint(character)
    await update.message.reply_text(f"🧩 Guess the anime character: **{hint}**")

# Guess command
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name or ""
    user_data = get_user_data(user_id, first_name, last_name)
    guess = update.message.text.strip().lower()

    if not user_data["current_character"]:
        await send_new_character(update, context)
        return

    user_data["guess_count"] += 1

    if guess == user_data["current_character"]:
        user_data["coins"] += 100
        user_data["correct_guesses"] += 1
        user_data["streak"] += 1
        user_data["top_streak"] = max(user_data["streak"], user_data["top_streak"])

        await update.message.reply_text(
            f"🎉 **Correct!** You earned 💰 100 coins! 🎊\n"
            f"📈 Total coins: {user_data['coins']}\n"
            f"🔥 Streak: {user_data['streak']} 🔥"
        )
        await send_new_character(update, context)
    else:
        if user_data["guess_count"] >= 5:
            user_data["streak"] = 0
            await update.message.reply_text(
                f"❌ Out of attempts! 😔\n"
                f"The correct answer was: **{user_data['current_character']}**. 🤓\n"
                f"Let's try a new character! 🆕"
            )
            await send_new_character(update, context)
        else:
            remaining_attempts = 5 - user_data["guess_count"]
            await update.message.reply_text(
                f"❌ Wrong guess! 😅\n"
                f"⚡ Try again! Attempts left: {remaining_attempts}."
            )

# Upload command
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if str(user_id) != OWNER_ID and user_id not in SUDO_USERS:
        await update.message.reply_text("🚫 You do not have permission to upload character names.")
        return

    character_name = " ".join(context.args)
    if not character_name:
        await update.message.reply_text("⚠️ Please provide a character name to upload.")
        return

    CHARACTER_LIST.append(character_name)
    await update.message.reply_text(f"✅ Character '{character_name}' has been added successfully!")

# Addsudo command
async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if str(user_id) != OWNER_ID:
        await update.message.reply_text("🚫 Only the owner can add sudo users.")
        return

    try:
        sudo_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Please provide a valid user ID to add as sudo.")
        return

    SUDO_USERS.add(sudo_id)
    await update.message.reply_text(f"✅ User ID {sudo_id} has been added as a sudo user!")

# Profile command
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name or ""
    user_data = get_user_data(user_id, first_name, last_name)

    await update.message.reply_text(
        f"🧑 **Profile**:\n"
        f"📛 Name: {first_name} {last_name}\n"
        f"💰 Coins: {user_data['coins']}\n"
        f"✅ Correct Guesses: {user_data['correct_guesses']}\n"
        f"🔥 Current Streak: {user_data['streak']}\n"
        f"🌟 Top Streak: {user_data['top_streak']}"
    )

# Top command
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not users_data:
        await update.message.reply_text("⚠️ No players yet! Be the first to play! 🎮")
        return

    sorted_users = sorted(users_data.values(), key=lambda x: x["coins"], reverse=True)[:10]
    leaderboard = []
    for i, user in enumerate(sorted_users):
        first_name = user["first_name"]
        last_name = user["last_name"]
        coins = user["coins"]
        leaderboard.append(f"{i + 1}. 🥇 {first_name} {last_name}: 💰 {coins} coins")

    leaderboard_text = "\n".join(leaderboard)
    await update.message.reply_text(f"🏆 **Top Players**:\n{leaderboard_text}")

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(CommandHandler("addsudo", addsudo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess))

    app.run_polling()

if __name__ == "__main__":
    main()
