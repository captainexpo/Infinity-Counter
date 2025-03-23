from typing import Optional, Any, Tuple
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
    expression.replace("\\*", "*").replace(")(", ")*(").replace("i", "j")
    allowed = "0123456789+-*%/().^j "
    if all(c in allowed for c in expression):
        expression.replace("√", "sqrt").replace("π", "3.1415926535897325").replace("e", "2.718281828459045")
        try:
            res = eval(expression)
            log(str(res))
            if not isinstance(res, int) and not isinstance(res, float) and not isinstance(res, complex):
                raise ValueError("Invalid expression")
            return res
        except:
            raise ValueError("Invalid expression")
    raise ValueError("Invalid expression")

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
            with open(self.leaderboard_file, 'w') as f:
                f.write("0")

    def new_number(self, num: str, uid: str) -> Tuple[bool, int]:
        try:
            n_int = safe_eval(num)
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

    def get_best(self) -> int:
        if not os.path.exists(self.leaderboard_file):
            with open(self.leaderboard_file, 'w') as f: f.write("0")
            return 200
        with open(self.leaderboard_file, 'r') as f:
            val = int(f.read())
        return val

    async def update_leaderboard(self, force: bool = False):
        best = self.get_best()
        log(f"Best: {best}, Current: {self.value}")
        is_new_best = self.value > best
        if is_new_best or force:
            if not force:
                with open(self.leaderboard_file, 'w') as f:
                    f.write(str(self.value))
            if self.leaderboard_message is not None:
                board = f"**Best Score: {self.get_best()}**"
                await self.leaderboard_message.edit(content=board)
            else:
                log("Leaderboard message not set")

class CounterClient(discord.Client):
    def set_counter(self, counter: Counter):
        self.counter = counter

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        await self.init_leaderboard(client.get_channel(int(os.environ["BOT_CHANNEL"]))) # type: ignore
        self.is_best_run = False

    async def init_leaderboard(self, chan: discord.TextChannel):
        msg = await chan.send("Best Score:")
        self.counter.set_leaderboard_message(msg)
        await self.counter.update_leaderboard(force=True)

    async def on_message(self, message: discord.Message):
        if message.author.bot: return
        if message.channel.id == int(os.environ["COUNTER_CHANNEL"]):
            if (f:=self.counter.new_number(message.content, str(message.author.id)))[0]:
                await self.counter.update_leaderboard()
                log(f"{message.author.id} counted {f[1]}, said {message.content}")
                if not self.is_best_run and f[1] > self.counter.get_best():
                    self.is_best_run = True
                    await message.add_reaction('🎉')
                pass
            else:
                log(f"{message.author.id} messed up, said {message.content}")
                await message.add_reaction('❌')
            return

if __name__ == "__main__":
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
