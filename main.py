import os
import telebot
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from openai import OpenAI

# Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Hugging Face Client Setup
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

def extract_text_from_epub(epub_path):
    book = epub.read_epub(epub_path)
    text_content = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text_content.append(soup.get_text())
    return "\n".join(text_content)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_path = "temp.epub"
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.reply_to(message, "EPUB received! Processing...")
        
        # Extract text
        full_text = extract_text_from_epub(file_path)
        
        # Example of how you might use the HF API
        # Sending a snippet to HF to summarize or process
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3", # Adjusted to available HF models
            messages=[{"role": "user", "content": f"Summarize this briefly: {full_text[:500]}"}],
        )
        
        summary = response.choices[0].message.content
        
        # Send back as a text file
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(full_text)
            
        with open("output.txt", "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"Processing complete!\nAI Summary: {summary}")
            
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    # Run Flask in a thread to keep Render happy
    Thread(target=run_flask).start()
    # Run Bot
    bot.infinity_polling()
