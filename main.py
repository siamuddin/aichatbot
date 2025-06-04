import discord
from discord.ext import commands
import aiohttp
import json
import random
import asyncio
import os
from datetime import datetime, timezone
import math

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Game data storage (in memory - resets on restart)
user_data = {}
trivia_questions = [
    {"question": "What is the capital of Japan?", "answer": "tokyo", "options": ["Tokyo", "Osaka", "Kyoto", "Hiroshima"]},
    {"question": "Which planet is known as the Red Planet?", "answer": "mars", "options": ["Venus", "Mars", "Jupiter", "Saturn"]},
    {"question": "What is 15 + 27?", "answer": "42", "options": ["40", "42", "44", "46"]},
    {"question": "Who painted the Mona Lisa?", "answer": "leonardo da vinci", "options": ["Leonardo da Vinci", "Pablo Picasso", "Vincent van Gogh", "Claude Monet"]},
    {"question": "What is the largest mammal?", "answer": "blue whale", "options": ["Elephant", "Blue Whale", "Giraffe", "Hippopotamus"]},
]

# Utility functions
def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'coins': 100,
            'level': 1,
            'xp': 0,
            'games_played': 0,
            'games_won': 0
        }
    return user_data[user_id]

def add_xp(user_id, amount):
    data = get_user_data(user_id)
    data['xp'] += amount
    # Level up every 100 XP
    new_level = (data['xp'] // 100) + 1
    if new_level > data['level']:
        data['level'] = new_level
        return True  # Leveled up
    return False

async def get_ai_response(message):
    """Get AI response from OpenRouter"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "anthropic/claude-3-haiku",
                "messages": [{"role": "user", "content": message}],
                "max_tokens": 500
            }
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                data = await response.json()
                return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"AI API Error: {e}")
        return "Sorry, I'm having trouble thinking right now. Try again later!"

# Bot events
@bot.event
async def on_ready():
    print(f'{bot.user} is online and ready!')
    await bot.change_presence(activity=discord.Game(name="!help for commands"))

# AI Chat Command
@bot.command(name='ask')
async def ask_ai(ctx, *, question):
    """Ask the AI anything!"""
    if not question:
        await ctx.send("Please provide a question! Example: `!ask What is quantum physics?`")
        return
    
    async with ctx.typing():
        response = await get_ai_response(question)
        
        # Split long messages
        if len(response) <= 2000:
            await ctx.reply(response)
        else:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            await ctx.reply(chunks[0])
            for chunk in chunks[1:]:
                await ctx.send(chunk)
    
    # Add XP for using AI
    leveled_up = add_xp(ctx.author.id, 5)
    if leveled_up:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to level {get_user_data(ctx.author.id)['level']}!")

# Profile & Stats Commands
@bot.command(name='profile')
async def profile(ctx, member: discord.Member = None):
    """Check your or someone else's profile"""
    if member is None:
        member = ctx.author
    
    data = get_user_data(member.id)
    embed = discord.Embed(title=f"{member.display_name}'s Profile", color=0x00ff00)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="Level", value=data['level'], inline=True)
    embed.add_field(name="XP", value=data['xp'], inline=True)
    embed.add_field(name="Coins", value=f"💰 {data['coins']}", inline=True)
    embed.add_field(name="Games Played", value=data['games_played'], inline=True)
    embed.add_field(name="Games Won", value=data['games_won'], inline=True)
    
    win_rate = (data['games_won'] / data['games_played'] * 100) if data['games_played'] > 0 else 0
    embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
    
    await ctx.send(embed=embed)

# Coin System
@bot.command(name='daily')
async def daily_coins(ctx):
    """Get your daily coins!"""
    data = get_user_data(ctx.author.id)
    daily_amount = random.randint(50, 150)
    data['coins'] += daily_amount
    
    await ctx.send(f"💰 {ctx.author.mention} received {daily_amount} daily coins! Total: {data['coins']} coins")

# Fun Utilities
@bot.command(name='roll')
async def roll_dice(ctx, sides: int = 6):
    """Roll a dice (default 6 sides)"""
    if sides < 2 or sides > 100:
        await ctx.send("Please choose between 2 and 100 sides!")
        return
    
    result = random.randint(1, sides)
    await ctx.send(f"🎲 {ctx.author.mention} rolled a {result} (1-{sides})")

@bot.command(name='flip')
async def flip_coin(ctx):
    """Flip a coin"""
    result = random.choice(['Heads', 'Tails'])
    emoji = '🪙' if result == 'Heads' else '🥈'
    await ctx.send(f"{emoji} {result}!")

@bot.command(name='8ball')
async def magic_8ball(ctx, *, question):
    """Ask the magic 8-ball a question"""
    if not question:
        await ctx.send("You need to ask a question!")
        return
    
    responses = [
        "Yes, definitely!", "It is certain", "Without a doubt", "Yes, absolutely",
        "You may rely on it", "As I see it, yes", "Most likely", "Outlook good",
        "Signs point to yes", "Reply hazy, try again", "Ask again later",
        "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
        "Don't count on it", "My reply is no", "My sources say no",
        "Outlook not so good", "Very doubtful"
    ]
    
    response = random.choice(responses)
    await ctx.send(f"🎱 {response}")

@bot.command(name='joke')
async def tell_joke(ctx):
    """Get a random joke"""
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Why did the scarecrow win an award? He was outstanding in his field!",
        "Why don't eggs tell jokes? They'd crack each other up!",
        "What do you call a fake noodle? An impasta!",
        "Why did the math book look so sad? Because it had too many problems!",
        "What do you call a bear with no teeth? A gummy bear!",
        "Why can't a bicycle stand up by itself? It's two tired!",
        "What do you call a fish wearing a bowtie? Sofishticated!"
    ]
    
    joke = random.choice(jokes)
    await ctx.send(f"😂 {joke}")

# Games
@bot.command(name='rps')
async def rock_paper_scissors(ctx, choice: str = None):
    """Play Rock Paper Scissors"""
    if not choice or choice.lower() not in ['rock', 'paper', 'scissors']:
        await ctx.send("Please choose: `!rps rock`, `!rps paper`, or `!rps scissors`")
        return
    
    user_choice = choice.lower()
    bot_choice = random.choice(['rock', 'paper', 'scissors'])
    
    emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
    
    data = get_user_data(ctx.author.id)
    data['games_played'] += 1
    
    # Determine winner
    if user_choice == bot_choice:
        result = "It's a tie!"
        coins_won = 10
    elif (user_choice == 'rock' and bot_choice == 'scissors') or \
         (user_choice == 'paper' and bot_choice == 'rock') or \
         (user_choice == 'scissors' and bot_choice == 'paper'):
        result = "You win!"
        coins_won = 25
        data['games_won'] += 1
        add_xp(ctx.author.id, 10)
    else:
        result = "I win!"
        coins_won = 5
    
    data['coins'] += coins_won
    
    embed = discord.Embed(title="Rock Paper Scissors", color=0xff6b6b)
    embed.add_field(name="Your choice", value=f"{emojis[user_choice]} {user_choice.title()}", inline=True)
    embed.add_field(name="My choice", value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)
    embed.add_field(name="Result", value=result, inline=False)
    embed.add_field(name="Coins earned", value=f"💰 +{coins_won}", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='guess')
async def guess_number(ctx, number: int = None):
    """Guess a number between 1-100"""
    if number is None:
        await ctx.send("Please guess a number! Example: `!guess 42`")
        return
    
    if number < 1 or number > 100:
        await ctx.send("Please guess a number between 1 and 100!")
        return
    
    secret_number = random.randint(1, 100)
    data = get_user_data(ctx.author.id)
    data['games_played'] += 1
    
    difference = abs(number - secret_number)
    
    if difference == 0:
        result = "🎉 Exact match! Amazing!"
        coins_won = 100
        data['games_won'] += 1
        add_xp(ctx.author.id, 25)
    elif difference <= 5:
        result = "🔥 Very close!"
        coins_won = 50
        data['games_won'] += 1
        add_xp(ctx.author.id, 15)
    elif difference <= 10:
        result = "👍 Close!"
        coins_won = 25
        add_xp(ctx.author.id, 10)
    elif difference <= 20:
        result = "🤔 Not bad"
        coins_won = 10
        add_xp(ctx.author.id, 5)
    else:
        result = "😅 Way off!"
        coins_won = 5
    
    data['coins'] += coins_won
    
    await ctx.send(f"The number was **{secret_number}**. Your guess: **{number}**\n"
                   f"{result} You earned **{coins_won}** coins!")

@bot.command(name='trivia')
async def trivia_game(ctx):
    """Play a trivia game"""
    question_data = random.choice(trivia_questions)
    
    embed = discord.Embed(title="🧠 Trivia Time!", description=question_data["question"], color=0x4ecdc4)
    
    options_text = ""
    for i, option in enumerate(question_data["options"], 1):
        options_text += f"{i}. {option}\n"
    
    embed.add_field(name="Options", value=options_text, inline=False)
    embed.set_footer(text="Type the number or answer in chat! You have 30 seconds.")
    
    await ctx.send(embed=embed)
    
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel
    
    try:
        answer_msg = await bot.wait_for('message', timeout=30.0, check=check)
        user_answer = answer_msg.content.lower().strip()
        
        # Check if answer is correct (by number or text)
        correct = False
        if user_answer == question_data["answer"].lower():
            correct = True
        elif user_answer.isdigit():
            index = int(user_answer) - 1
            if 0 <= index < len(question_data["options"]):
                if question_data["options"][index].lower() == question_data["answer"].lower():
                    correct = True
        
        data = get_user_data(ctx.author.id)
        data['games_played'] += 1
        
        if correct:
            data['games_won'] += 1
            coins_won = 30
            data['coins'] += coins_won
            add_xp(ctx.author.id, 15)
            await ctx.send(f"🎉 Correct! You earned {coins_won} coins!")
        else:
            coins_won = 5
            data['coins'] += coins_won
            await ctx.send(f"❌ Wrong! The answer was: **{question_data['answer'].title()}**\n"
                          f"You still get {coins_won} coins for trying!")
            
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ Time's up! The answer was: **{question_data['answer'].title()}**")

# Utility Commands
@bot.command(name='weather')
async def weather_info(ctx):
    """Get weather info (placeholder - you'd need a weather API)"""
    await ctx.send("🌤️ Weather feature coming soon! For now, try asking the AI: `!ask What's the weather like in [city]?`")

@bot.command(name='time')
async def current_time(ctx):
    """Get current UTC time"""
    now = datetime.now(timezone.utc)
    await ctx.send(f"🕐 Current UTC time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")

@bot.command(name='calc')
async def calculator(ctx, *, expression):
    """Simple calculator (be careful with input!)"""
    try:
        # Only allow basic math operations for security
        allowed_chars = "0123456789+-*/.() "
        if not all(c in allowed_chars for c in expression):
            await ctx.send("❌ Only basic math operations allowed: +, -, *, /, (, )")
            return
        
        result = eval(expression)
        await ctx.send(f"🧮 `{expression}` = **{result}**")
        
    except Exception as e:
        await ctx.send(f"❌ Invalid expression! Error: {str(e)}")

# Custom Help Command
@bot.remove_command('help')
@bot.command(name='help')
async def custom_help(ctx, category: str = None):
    """Show all available commands"""
    
    if category is None:
        embed = discord.Embed(title="🤖 Bot Commands", description="Use `!help [category]` for detailed info", color=0x7289da)
        
        embed.add_field(name="🤖 AI & Chat", value="`!ask` - Chat with AI\n`!help ai`", inline=True)
        embed.add_field(name="🎮 Games", value="`!rps` `!guess` `!trivia`\n`!help games`", inline=True)
        embed.add_field(name="🎲 Fun", value="`!roll` `!flip` `!8ball` `!joke`\n`!help fun`", inline=True)
        embed.add_field(name="👤 Profile", value="`!profile` `!daily`\n`!help profile`", inline=True)
        embed.add_field(name="🔧 Utilities", value="`!calc` `!time` `!weather`\n`!help utils`", inline=True)
        
        await ctx.send(embed=embed)
        
    elif category.lower() == 'ai':
        embed = discord.Embed(title="🤖 AI Commands", color=0x00ff00)
        embed.add_field(name="!ask [question]", value="Ask the AI anything! Gives XP.", inline=False)
        embed.add_field(name="Examples", value="`!ask What is Python?`\n`!ask Tell me a story`\n`!ask Help me with math`", inline=False)
        await ctx.send(embed=embed)
        
    elif category.lower() == 'games':
        embed = discord.Embed(title="🎮 Games", color=0xff6b6b)
        embed.add_field(name="!rps [choice]", value="Rock Paper Scissors\n`!rps rock`", inline=False)
        embed.add_field(name="!guess [number]", value="Guess number 1-100\n`!guess 50`", inline=False)
        embed.add_field(name="!trivia", value="Answer trivia questions", inline=False)
        embed.add_field(name="Rewards", value="Win coins and XP by playing!", inline=False)
        await ctx.send(embed=embed)
        
    # Add other category help as needed...

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found! Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument! Use `!help` for command usage.")
    else:
        print(f"Error: {error}")
        await ctx.send("❌ Something went wrong! Please try again.")

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
