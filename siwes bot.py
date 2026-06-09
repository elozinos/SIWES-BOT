import time
import asyncio
from typing import Final
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, Application, filters
from google import genai

# --- CONFIGURATION ---
TOKEN: Final = "8708075469:AAGe9VNAy8Ugces92dXwNbQCH-yqdPzGIGY"
# WARNING: Generate a NEW key in AI Studio and replace this one immediately.
GEMINI_API_KEY: Final = "AIzaSyBT8L8yeyutAumjzBuWr73ALa5KpfRqSAg"

# Initialize the Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # Check if user wants "Deep Research"
    if user_text.lower().startswith("research:"):
        await deep_research_flow(update, user_text.replace("research:", "").strip())
    else:
        await standard_chat_flow(update, user_text)


async def standard_chat_flow(update: Update, user_text: str):
    """Normal fast response using Gemini 2.5 Flash"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=genai.types.GenerateContentConfig(
                system_instruction="You are the SIWES Navigator. Provide procedural, precise Nigerian SIWES guidance."
            ),
            contents=user_text
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Chat Error: {e}")
        await update.message.reply_text("I hit a snag. Try again in a moment!")


async def deep_research_flow(update: Update, query: str):
    """Background research flow using Gemini 3.1 Pro Deep Research"""
    status_msg = await update.message.reply_text(
        "🔍 Initializing Deep Research... This usually takes 2-5 minutes. I will notify you when the report is ready.")

    try:
        # Start the background interaction
        interaction = client.interactions.create(
            input=f"Research this SIWES topic in depth: {query}",
            agent='deep-research-pro-preview-12-2025',
            background=True
        )

        # Polling loop to check if it's done
        while True:
            await asyncio.sleep(20)  # Wait 20 seconds between checks
            res = client.interactions.get(interaction.id)

            if res.status == 'completed':
                final_report = res.outputs[-1].text
                # Telegram has a 4096 character limit per message
                if len(final_report) > 4000:
                    for i in range(0, len(final_report), 4000):
                        await update.message.reply_text(final_report[i:i + 4000])
                else:
                    await update.message.reply_text(final_report)
                break
            elif res.status == 'failed':
                await update.message.reply_text("❌ The research task failed. Please try a simpler query.")
                break

    except Exception as e:
        print(f"Research Error: {e}")
        await update.message.reply_text("Sorry, Deep Research is currently unavailable for this query.")


if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', lambda u, c: u.message.reply_text(
        "SIWES Navigator active. Ask a question or use 'research: [topic]' for a deep report.")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("SIWES Navigator is running...")
    app.run_polling()