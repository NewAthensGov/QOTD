import discord
print(discord.__version__)
from discord.ext import tasks, commands
import random
import os
import asyncio
from datetime import datetime, timedelta
from typing import Union

# Set up the bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix="/") 

# IDs for the channel and role
CHANNEL_ID = CHANNEL_ID_GOES_HERE
ROLE_ID = ROLE_ID_GOES_HERE

# Path to the directory with question files and the file to track asked questions
QUESTIONS_DIR = './lists/'
ASKED_QUESTIONS_FILE = './asked_questions.txt'

# Load asked questions into a set for quick lookup
if os.path.exists(ASKED_QUESTIONS_FILE):
    with open(ASKED_QUESTIONS_FILE, 'r') as file:
        asked_questions = set(file.read().splitlines())
else:
    asked_questions = set()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # Start the task when the bot is ready
    send_daily_message.start()

@tasks.loop(hours=24)
async def send_daily_message():
    await bot.wait_until_ready()  # Ensure the bot is ready

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Channel with ID {CHANNEL_ID} not found")
        return

    # Get all questions from all files in the directory
    questions = []
    for filename in os.listdir(QUESTIONS_DIR):
        if filename.endswith('.txt'):
            with open(os.path.join(QUESTIONS_DIR, filename), 'r') as file:
                questions.extend(file.read().splitlines())

    # Filter out already asked questions
    new_questions = [q for q in questions if q not in asked_questions]
    if not new_questions:
        print("No new questions available.")
        return

    # Select a random question
    question = random.choice(new_questions)
    asked_questions.add(question)

    # Append the question to the asked questions file
    with open(ASKED_QUESTIONS_FILE, 'a') as file:
        file.write(f"{question}\n")

    # Create an embed message
    embed = discord.Embed(title="Question of the Day", description=question, color=0x00ff00)

    # Send the message and pin it
    message = await channel.send(content=f"<@&{ROLE_ID}>", embed=embed)
    await message.pin()

    # Unpin the previous message
    pinned_messages = await channel.pins()
    for pinned in pinned_messages:
        if pinned.id != message.id:
            await pinned.unpin()

@send_daily_message.before_loop
async def before_send_daily_message():
    # Calculate the time until the next noon GMT
    now = datetime.utcnow()
    next_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if now >= next_noon:
        next_noon += timedelta(days=1)
    wait_time = (next_noon - now).total_seconds()
    await asyncio.sleep(wait_time)

@bot.slash_command(name="qotd", description="Immediately send the Question of the Day message.")
async def qotd(ctx: discord.ApplicationContext):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        await ctx.respond(f"Channel with ID {CHANNEL_ID} not found", ephemeral=True)
        return

    # Get all questions from all files in the directory
    questions = []
    for filename in os.listdir(QUESTIONS_DIR):
        if filename.endswith('.txt'):
            with open(os.path.join(QUESTIONS_DIR, filename), 'r') as file:
                questions.extend(file.read().splitlines())

    # Filter out already asked questions
    new_questions = [q for q in questions if q not in asked_questions]
    if not new_questions:
        await ctx.respond("No new questions available.", ephemeral=True)
        return

    # Select a random question
    question = random.choice(new_questions)
    asked_questions.add(question)

    # Append the question to the asked questions file
    with open(ASKED_QUESTIONS_FILE, 'a') as file:
        file.write(f"{question}\n")

    # Create an embed message
    embed = discord.Embed(title="Question of the Day", description=question, color=0x00ff00)

    # Send the message and pin it
    message = await channel.send(content=f"<@&{ROLE_ID}>", embed=embed)
    await message.pin()

    # Unpin the previous message
    pinned_messages = await channel.pins()
    for pinned in pinned_messages:
        if pinned.id != message.id:
            await pinned.unpin()

    await ctx.respond("Question of the Day has been sent.", ephemeral=True)

# Run the bot with your token
bot.run('BOT_TOKEN_GOES_HERE')
