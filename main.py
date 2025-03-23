

from typing import Optional, Any
import discord
import os
import dotenv
import time

dotenv.load_dotenv()


def log(message: str) -> bool:
    try:
        if not os.path.exists('log.txt'):
            open('log.txt', 'w').close()
        with open('log.txt', 'a') as f:
            f.write(f"{time.time()}: {message}\n")
        return True
    except:
        return False

def safe_eval(expression: str) -> Any:
    allowed_chars = "0123456789+-*/(). "
    if not all(char in allowed_chars for char in expression):
        raise ValueError("Invalid character in expression")
    return eval(expression)

class Counter:
    def __init__(self, data_folder: str, count_file: str, leaderboard_file: str, starting_value: Optional[int] = None):
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)

        self.count_file = os.path.join(data_folder, count_file)
        self.leaderboard_file = os.path.join(data_folder, leaderboard_file)
        self.last_uid = "0"
        if starting_value is not None:
            self.value = starting_value
            self.save()
        self.value: int = self.read()
        self.leaderboard_message: discord.Message|None = None

    def set_leaderboard_message(self, msg: discord.Message):
        self.leaderboard_message = msg

    def read(self) -> int:
        if not os.path.exists(self.count_file):
            return 0
        with open(self.count_file, 'r') as f:
            return int(f.read())

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
            open(self.leaderboard_file, 'w').close()
        with open(self.leaderboard_file, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.startswith(uid):
                lines[i] = f"{uid}:{int(line.split(':')[1]) + 1}\n"
                break
        else:
            lines.append(f"{uid}:1\n")

        with open(self.leaderboard_file, 'w') as f:
            f.writelines(lines)

    def new_number(self, num: str, uid: str):
        try:
            n_int = safe_eval(num)
            if n_int == 1:
                # Exclude 1 from all rules
                self.last_uid = uid
                self.value = 1
                self.save()
                return True

            if uid == self.last_uid:
                self.mess_up()
                return False

            if n_int == self.value + 1:
                self.last_uid = uid
                self.increment()
                self.person_counted(uid)
                return True
            else:
                self.mess_up()
                return False
        except ValueError:
            self.mess_up()
            return False

    def get_leaderboard(self):
        if not os.path.exists(self.leaderboard_file):
            open(self.leaderboard_file, 'w').close()
        with open(self.leaderboard_file, 'r') as f:
            lines = f.readlines()

        lines.sort(key=lambda x: int(x.split(':')[1]), reverse=True)

        return lines

    async def update_leaderboard(self):
        if self.leaderboard_message is not None:
            leaderboard = self.get_leaderboard()
            board = "Leaderboard:\n"
            for i, line in enumerate(leaderboard):
                uid, count = line.split(':')
                if self.leaderboard_message.guild is not None:
                    member = await self.leaderboard_message.guild.fetch_member(int(uid))
                    board += f"{i + 1}. {member.display_name}: {count}\n"
            await self.leaderboard_message.edit(content=board)

class CounterClient(discord.Client):

    def set_counter(self, counter: Counter):
        self.counter = counter

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        await self.init_leaderboard(client.get_channel(int(os.environ["BOT_CHANNEL"]))) # type: ignore

    async def init_leaderboard(self, chan: discord.TextChannel):
        msg = await chan.send("Leaderboard:")
        self.counter.set_leaderboard_message(msg)

    async def on_message(self, message: discord.Message):
        if message.author.bot: return
        if message.channel.id == int(os.environ["COUNTER_CHANNEL"]):
            if self.counter.new_number(message.content, str(message.author.id)):
                log(f"{message.author.id} counted, said {message.content}")
                await self.counter.update_leaderboard()
                pass
            else:
                log(f"{message.author.id} messed up, said {message.content}")
                await message.add_reaction('❌')
            return

intents = discord.Intents.default()
intents.message_content = True

client = CounterClient(intents=intents)

client.set_counter(
    Counter(
        './data',
        'counter.txt',
        'leaderboard.txt',
    )
)
client.run(os.environ["BOT_TOKEN"])
