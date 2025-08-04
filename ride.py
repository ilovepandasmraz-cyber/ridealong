import os
import discord
from discord.ext import commands

# keep_alive.py
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

from discord import app_commands
import datetime
import time  # <-- Required for time tracking

# 🔁 REPLACE THESE with your actual Discord channel IDs
TOKEN = os.getenv('TOKEN')
REQUEST_CHANNEL_ID = 1386308426321100900
NOTIFY_CHANNEL_ID = 1386308042890543235

RIDEALONG_IMAGE_URL = (
    "https://media.discordapp.net/attachments/1386306729167552633/1400967644500463636/"
    "NoBlurDPSRedGlow.png?ex=688e904b&is=688d3ecb&hm=e41dd32cd28ec8a3a7033dce103b9f399dbc4c6aed2523677803770e180948f2"
    "&=&format=webp&quality=lossless&width=1418&height=781"
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Cooldown tracker
cooldowns = {}  # {user_id: timestamp_of_last_use}

COOLDOWN_SECONDS = 1200  # 20 minutes

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot is ready. Logged in as {bot.user}")

@bot.tree.command(name="request-ridealong", description="Request a ride-along")
@app_commands.checks.has_role(1386680467301863465)
async def request_ridealong(interaction: discord.Interaction):
    requester = interaction.user

    # Cooldown check
    now = time.time()
    last_used = cooldowns.get(requester.id, 0)
    remaining = COOLDOWN_SECONDS - (now - last_used)

    if remaining > 0:
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        await interaction.response.send_message(
            f"⏳ You must wait **{minutes}m {seconds}s** before requesting another ride-along.",
            ephemeral=True
        )
        return  # <--- Add this to prevent further execution

    # Save new timestamp
    cooldowns[requester.id] = now


    class AcceptButton(discord.ui.View):
        def __init__(self):
            super().__init__()

        @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
        async def accept(self, interaction_button: discord.Interaction, button: discord.ui.Button):
            accepter = interaction_button.user
            button.disabled = True
            await interaction_button.response.edit_message(view=self)

            notify_embed = discord.Embed(
                title="✅ Ride-Along Accepted!",
                description=(
                    f"{accepter.mention} accepted {requester.mention}'s ride-along request!\n"
                    "\n"
                    "<@&1386682330537787452> Please wait 25~30 seconds per mod call."
                ),
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            notify_embed.set_image(url=RIDEALONG_IMAGE_URL)

            notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
            if notify_channel:
                await notify_channel.send(embed=notify_embed)

    request_embed = discord.Embed(
        title="🚨 Ride-Along Request",
        description=(
            f"{requester.mention} is requesting a ride-along! Do not accept under 35 players.\n"
            "\n"
            "Pings: <@&1386679589782421597> <@&1386686213527961641> <@&1386679658271084635>"
        ),
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    request_embed.set_image(url=RIDEALONG_IMAGE_URL)

    request_channel = bot.get_channel(REQUEST_CHANNEL_ID)
    if request_channel:
        await request_channel.send(embed=request_embed, view=AcceptButton())

    await interaction.response.send_message("📨 Your ride-along request has been sent!", ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message(
            "🚫 You do not have permission to use this command.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"⚠️ Unexpected error:\n```{error}```", ephemeral=True
        )

from keep_alive import keep_alive

keep_alive()

bot.run(TOKEN)
