import discord
import asyncio
import dotenv
import os

dotenv.load_dotenv(override=True)

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.guilds = True

class C(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        c = self.get_channel(1353220695890460682)
        guild = c.guild
        # make channel public
        for i in await guild.fetch_roles():
            if i.id == 1348190699379757096:
                await c.set_permissions(i, send_messages=False)
        
        while True:
            await c.send(input())
client = C(intents=intents)
client.run(os.environ["BOT_TOKEN"])