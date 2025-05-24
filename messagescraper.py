import discord
import asyncio
import dotenv
import os
from collections import defaultdict
from typing import Optional

dotenv.load_dotenv(override=True)

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.guilds = True

users: defaultdict = defaultdict(lambda: [0, 0])  # [yes_count, no_count]

class C(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        channel_id: int = int(os.environ.get("COUNTER_CHANNEL", 0))  # Set your channel ID in .env
        if channel_id == 0:
            print("Channel ID not set in .env file.")
            await self.close()
            return
        channel = self.get_channel(channel_id)
        if channel is None:
            print("Channel not found.")
            await self.close()
            return

        i = 0
        if not isinstance(channel, discord.TextChannel):
            print("Channel is not a text channel.")
            await self.close()
            return
        async for message in channel.history(limit=None, oldest_first=True):
            if message.author.bot:
                continue
            if not message.content.isdigit():
                continue
            if len(message.reactions) > 0:
                for reaction in message.reactions:
                    if reaction.emoji == "❌":
                        users[message.author.id][1] += 1
                        break
                else:
                    users[message.author.id][0] += 1
            else:
                users[message.author.id][0] += 1
            i += 1
            print(i, "\r", end="")
        print()
            
        for user_id, (yes_count, no_count) in users.items():
            print(f"{user_id}|{yes_count}|{no_count}")
            
        await self.close()

client = C(intents=intents)
client.run(os.environ["BOT_TOKEN"])