from typing import Optional, Any, Tuple, Callable
import discord
import os
import dotenv
import time


def log(message: str) -> bool:
    try:
        if not os.path.exists('log.txt'):
            open('log.txt', 'w').close()
        with open('log.txt', 'a') as f:
            f.write(f"{time.time()}: {message}\n")
        return True
    except:
        return False

class Counter:
    def __init__(self, data_folder: str, count_file: str, leaderboard_file: str, starting_value: Optional[int] = None):
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        self.data_folder = data_folder
        self.count_file = os.path.join(data_folder, count_file)
        self.leaderboard_file = os.path.join(data_folder, leaderboard_file)
        self.last_uid = "0"
        if starting_value is not None:
            self.value = starting_value
            self.save()
        self.value: int = self.read()
        self.leaderboard_message: discord.Message|None = None
        
    def get_people_leaderboard(self, guild) -> str:
        return os.path.join(self.data_folder, f"guilds/leaderboard_{guild.id}.txt")

    def has_leaderboard_message_saved(self) -> bool:
        with open(self.leaderboard_file, 'r') as f:
            try:
                return len(f.read().strip().split("|")) > 1
            except:
                return False
    def set_leaderboard_message(self, msg: Optional[discord.Message] = None, channel: Optional[discord.TextChannel] = None):
        if msg is None:
            log("Leaderboard message not provided, trying to read from file")
            with open(self.leaderboard_file, 'r') as f:
                msg_id = f.read().strip().split("|")[1]
            if channel is None:
                raise ValueError("Channel must be provided if message is None")
            self.leaderboard_message = channel.get_partial_message(int(msg_id)) # type: ignore
        else:
            log("Leaderboard message provided")
            self.leaderboard_message = msg
        best = self.get_best()
        with open(self.leaderboard_file, 'w') as f:
            if self.leaderboard_message is not None:
                f.write(str(best) + "|" + str(self.leaderboard_message.id))

    def read(self) -> int:
        if not os.path.exists(self.count_file):
            return 0
        with open(self.count_file, 'r') as f:
            return int(f.read().strip())

    def save(self):
        with open(self.count_file, 'w') as f:
            f.write(str(self.value))

    def increment(self):
        self.value += 1
        self.save()

    def mess_up(self):
        self.value = 0
        self.last_uid = "0"
        self.save()

    def person_counted(self, uid: str):
        if not os.path.exists(self.leaderboard_file):
            with open(self.leaderboard_file, 'w') as f:
                f.write("0")
    def process_number(self, num: str) -> int:
        idx = num.find("-")
        if idx == -1:
            return int(num)
        else:
            return int(num[:idx])

    def new_number(self, num: str, uid: str) -> Tuple[bool, int]:
        try:
            n_int = int(num)
            if n_int == 1:
                # Exclude 1 from all rules
                self.last_uid = uid
                self.value = 1
                self.save()
                return (True, 1)
            if uid == self.last_uid:
                self.mess_up()
                return (False, 0)
            if n_int == self.value + 1:
                self.last_uid = uid
                self.increment()
                self.person_counted(uid)
                return (True, n_int)
            else:
                self.mess_up()
                return (False, 0)
        except ValueError:
            self.mess_up()
            return (False, 0)

    def reset_leaderboard(self):
        with open(self.leaderboard_file, 'w') as f: f.write("0|")

    def get_best(self) -> int:
        if not os.path.exists(self.leaderboard_file):
            self.reset_leaderboard()
            return 0
        with open(self.leaderboard_file, 'r') as f:
            try:
                val = int(f.read().split("|")[0])
            except:
                log("Leaderboard file is corrupted")
                self.reset_leaderboard()
                return self.get_best()
        return val

    def get_person_leaderboard(self, guild) -> str:
        if guild is None:
            log("Guild not found")
            return ""
        if not os.path.exists(self.get_people_leaderboard(guild)):
            os.makedirs(os.path.dirname(self.get_people_leaderboard(guild)), exist_ok=True)
            open(self.get_people_leaderboard(guild), 'w').close()
        o = ""
        with open(self.get_people_leaderboard(guild), 'r') as file:
            lines = file.read().strip().split("\n")
            for i in sorted(lines, key=lambda x: int(x.split("|")[1]), reverse=True):
                i = i.strip()
                id = int(i.split("|")[0])
                member = f"<@{id}>"
                if member is None:
                    log(f"Member not found: {i.split('|')[0]}")
                    continue
                o += f"\t{member}: {i.split('|')[1]}\n"
        return o


    async def update_leaderboard(self, force: bool = False):
        if self.leaderboard_message is None:
            log("Leaderboard message not set")
            return

        best = self.get_best()
        log(f"Updating leaderboard (id={self.leaderboard_message.id})")

        if not force and self.value >= best:
            with open(self.leaderboard_file, 'w') as f:
                f.write(str(self.value) + "|" + str(self.leaderboard_message.id))
        board = f"**Best Score: {best}**\n"
        
        board += "**Leaderboard:**\n"
        board += self.get_person_leaderboard(self.leaderboard_message.guild)
        
        await self.leaderboard_message.edit(content=board)

class CounterClient(discord.Client):
    def set_counter(self, counter: Counter):
        self.counter = counter

    #async def get_rule(self):
    #    self.rule = lambda s: False
    #    guild = client.get_guild(int(os.environ["GUILD_ID"]))
    #    if guild is None:
    #        log("Guild not found")
    #        return
    #    if guild.get_channel(int(os.environ["RULE_CHANNEL"])) is None:
    #        log("Rule channel not found")
    #        c = await guild.create_text_channel(
    #            "secret-rule-2", 
    #            category=[i for i in guild.categories if i.id == int(os.environ["TEXT_CHANNELS_CATEGORY"])][0],
    #            topic="Try and guess the secret rule! (Ezra please don't delete this 🥺)"
    #        )
    #        log("Rule channel created")
    #        os.environ["RULE_CHANNEL"] = str(c.id)
    #    self.rule: Callable[[str], bool] = __import__('_NOINCLUDE_rule').rule
            

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        await self.init_leaderboard(client.get_channel(int(os.environ["BOT_CHANNEL"]))) # type: ignore
        self.is_best_run = False

        #await self.get_rule()

    async def init_leaderboard(self, chan: discord.TextChannel):
        if os.path.exists(self.counter.get_people_leaderboard(chan.guild)):
            open(self.counter.get_people_leaderboard(chan.guild), 'a').close()
        if not self.counter.has_leaderboard_message_saved():
            msg = await chan.send("Best Score:")
            self.counter.set_leaderboard_message(msg=msg)
        else:
            self.counter.set_leaderboard_message(channel=chan)
        await self.counter.update_leaderboard(force=True)


    async def on_message(self, message: discord.Message):
        if message.channel.id == int(os.environ["BOT_CHANNEL"]):
            pass
        if message.author.bot: 
            return
        log(f"{message.author.id} said {message.content} in {message.channel.id} ({message.channel.name})") # type: ignore

        if message.channel.id == int(os.environ["COUNTER_CHANNEL"]) and os.environ.get("ENABLE_COUNTING", "1") != "0":
            c = self.counter.value
            if (f:=self.counter.new_number(message.content, str(message.author.id)))[0]:
                if message.guild is None:
                    log("Guild not found")
                    return
                if not os.path.exists(self.counter.get_people_leaderboard(message.guild)):
                    os.makedirs(os.path.dirname(self.counter.get_people_leaderboard(message.guild)), exist_ok=True)
                    open(self.counter.get_people_leaderboard(message.guild), 'w').close()
                print("Writing to leaderboard")
                if f[1] > c and f[1] > 1:
                    with open(self.counter.get_people_leaderboard(message.guild), 'r+') as file:
                        lines = file.readlines()
                        if str(message.author.id) not in [i.split("|")[0] for i in lines]:
                            file.write(f"{message.author.id}|1|{message.content}\n")
                        else:
                            file.seek(0)
                            file.truncate()
                            for i in lines:
                                if str(message.author.id) in i:
                                    file.write(f"{message.author.id}|{int(i.split('|')[1]) + 1}|{message.content}\n")
                                else:
                                    file.write(i)
                await self.counter.update_leaderboard()
                log(f"{message.author.id} counted {f[1]}, said {message.content}")
                if not self.is_best_run and f[1] > self.counter.get_best():
                    self.is_best_run = True
                    await message.add_reaction('🎉')
                pass
                if f[1] == 69:
                    await message.add_reaction(':pregnant_man:')
            else:
                self.is_best_run = False
                log(f"{message.author.id} messed up, said {message.content}")
                if c >= 50: await message.reply("Damn that's embarrassing") 
                if c >= 100: await message.reply("Slert :pensive:")
                await message.add_reaction('❌')
            return

if __name__ == "__main__":
    dotenv.load_dotenv(override=True)
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guild_messages = True
    intents.guilds = True

    client = CounterClient(intents=intents)

    client.set_counter(
        Counter(
            './data',
            'counter.txt',
            'leaderboard.txt',
        )
    )
    client.run(os.environ["BOT_TOKEN"])
