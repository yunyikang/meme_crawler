import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import os
import sys

logging.basicConfig(
    filename="/app/logs/bot.log",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def memes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = "/app/out/table.csv"
    if os.path.isfile(file_name):
        await context.bot.send_document(chat_id=update.effective_chat.id, document="/app/out/table.csv")
    else: 
       await context.bot.send_message(chat_id=update.effective_chat.id, text="Report not ready")
    

if __name__ == '__main__':
    
    bot_token_file = os.environ['BOT_TOKEN_FILE']
    bot_token = ""
    with open(bot_token_file, "r") as reader:
        bot_token = reader.read()

    if bot_token == "":
        logging.error("can't find bot token")
        sys.exit("no token")
    logging.info(f"token: {bot_token}")

    application = ApplicationBuilder().token(bot_token).build()
    
    start_handler = CommandHandler('start', start)
    memes_handler = CommandHandler('memes', memes)

    application.add_handler(start_handler)
    application.add_handler(memes_handler)
    
    application.run_polling()