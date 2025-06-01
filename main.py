import os
import interactions
import random
import string
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

bot = interactions.Client(
    token=os.getenv("DISCORD_TOKEN"),
    intents=interactions.Intents.DEFAULT | interactions.Intents.GUILD_MESSAGES | interactions.Intents.MESSAGE_CONTENT
)

APOLOGY_TEXT = (
    "I’m utterly mortified by my pathetic behavior and can’t believe I stooped so low. "
    "I completely failed everyone’s expectations, including my own, and I’m deeply ashamed of the person I showed myself to be. "
    "I don’t deserve forgiveness, but I’ll waste no effort trying to earn it by being better — because right now, I’m nothing but a disappointment."
)

apologize_sessions = {}
echo_targets = {}
copy_text_sessions = {}  # Track users who must type exact text from image

@interactions.slash_command(name="apologize_loop", description="Force a user to apologize before they can talk again")
async def apologize_loop(ctx: interactions.SlashContext):
    target = ctx.kwargs.get("target")
    if not target:
        await ctx.send("You must specify a user to punish.", ephemeral=True)
        return

    user_id = target.id
    if user_id in apologize_sessions:
        await ctx.send(f"{target.mention} is already in the Apologize Loop.")
        return

    apologize_sessions[user_id] = 0
    await ctx.send(
        f"{target.mention} has been cursed by the Dungeon Warden.\n"
        f"You must type the following apology message **5 times exactly** before you can speak again.\n\n"
        f"```\n{APOLOGY_TEXT}\n```"
    )

apologize_loop.options = [
    {"name": "target", "description": "The user to force into apology", "type": 6, "required": True}
]

@interactions.slash_command(name="bot_echo", description="Echo a user's messages with humiliation for 15 seconds")
async def bot_echo(ctx: interactions.SlashContext):
    target = ctx.kwargs.get("target")
    if not target:
        await ctx.send("You must specify a user.", ephemeral=True)
        return

    user_id = target.id
    echo_targets[user_id] = datetime.utcnow() + timedelta(seconds=15)
    await ctx.send(f"{target.mention} will now speak only as a humble footstool for the next 15 seconds. 🙇")

bot_echo.options = [
    {"name": "target", "description": "The user whose messages will be echoed and shamed", "type": 6, "required": True}
]

@interactions.slash_command(name="copy_text", description="Give a user a line they must type manually, without copy/paste")
async def copy_text(ctx: interactions.SlashContext):
    target = ctx.kwargs.get("target")
    if not target:
        await ctx.send("You must specify a user.", ephemeral=True)
        return

    chars = string.ascii_letters  # Only letters (uppercase and lowercase)
    random_text = ''.join(random.choices(chars, k=10))

    img = Image.new('RGB', (600, 100), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((10, 40), random_text, font=font, fill=(255, 255, 255))

    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    copy_text_sessions[target.id] = random_text  # Save expected text

    await ctx.send(
        f"{target.mention}, type the text shown in the image manually — you cannot copy it loser 😏🤣",
        files=[interactions.File(file=img_bytes, file_name="challenge.png")]
    )

copy_text.options = [
    {"name": "target", "description": "The user who must type the text manually", "type": 6, "required": True}
]

@bot.listen()
async def on_message_create(event: interactions.api.events.MessageCreate):
    message = event.message
    author_id = message.author.id

    if message.author.bot:
        return

    # Check copy_text_sessions first
    if author_id in copy_text_sessions:
        expected = copy_text_sessions[author_id]
        if message.content != expected:
            try:
                await message.delete()
            except Exception as e:
                print(f"Failed to delete message: {e}")
            await message.channel.send(
                f"{message.author.mention} Invalid input, you failed to type the line correctly! Bow down to your failure! 🙇"
            )
            return
        else:
            # Correct text typed, remove session
            del copy_text_sessions[author_id]
            # Allow message normally below

    if author_id in apologize_sessions:
        if message.content != APOLOGY_TEXT:
            try:
                await message.delete()
            except Exception as e:
                print(f"Failed to delete incorrect apology: {e}")
            await message.channel.send(f"{message.author.mention} That’s not the correct apology. Try again, and type it exactly as instructed.")
            return

        apologize_sessions[author_id] += 1
        if apologize_sessions[author_id] >= 5:
            del apologize_sessions[author_id]
            await message.channel.send(f"✅ {message.author.mention} has completed the Apologize Loop. You may now speak... but remember your shame.")
        else:
            await message.channel.send(f"{message.author.mention} Apology {apologize_sessions[author_id]}/5 accepted. Keep going.")
        return

    if author_id in echo_targets and datetime.utcnow() < echo_targets[author_id]:
        try:
            await message.delete()
            await message.channel.send(f"**{message.author.display_name}**: {message.content} — but i mainly want to serve as a footstool and be stepped on like a peasant 🙇")
        except Exception as e:
            print(f"Failed to delete or send echo: {e}")
    elif author_id in echo_targets:
        del echo_targets[author_id]

@bot.listen()
async def on_ready():
    user = getattr(bot, "user", None) or getattr(bot._connection, "user", None)
    print(f"Logged in as {user.username}" if user else "Logged in, but bot user info not found")

bot.start()
