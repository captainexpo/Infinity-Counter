
from typing import Optional
import discord
import os

__import__('dotenv').load_dotenv()

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
            n_int = int(num)
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


class MyClient(discord.Client):

    def set_counter(self, counter: Counter):
        self.counter = counter

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: discord.Message):
        if message.author.bot: return
        if message.channel.id == int(os.environ["COUNTER_CHANNEL"]):
            if self.counter.new_number(message.content, str(message.author.id)):
                pass
            else:
                await message.add_reaction('❌')

            return
        print(f'Message from {message.author}: {message.content}')

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.set_counter(
    Counter(
        './data',
        'counter.txt',
        'leaderboard.txt',
    )
)
client.run(os.environ["BOT_TOKEN"])
