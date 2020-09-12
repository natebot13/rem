import re
import discord
import upsidedown
import parsedatetime
from datetime import datetime
import asyncio
import random


with open('/usr/share/dict/words') as f:
    WORDS = [w.rstrip() for w in f.readlines() if len(w) < 7]


with open('.token') as f:
    TOKEN = f.read().strip()


async def do_reminder(secs, msg, message):
    try:
        await asyncio.sleep(secs)
    except asyncio.CancelledError:
        print(f'cancelled reminder {msg}')
        raise
    mentions = ' '.join([m.mention for m in message.mentions + message.role_mentions])
    await message.channel.send(f're:minder! {msg} {mentions}')


class RemBotClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cal = parsedatetime.Calendar()
        self.commands = []
        self.reminders = {}

    async def on_message(self, message):
        if message.author == client.user:
            return
        for command in self.commands:
            if message.content.startswith(command[0]):
                await command[1](self, command[0], message)

    def register(self, name):
        def register_command(func):
            if isinstance(name, list):
                for n in name:
                    self.commands.append((n,func))
            else:
                self.commands.append((name, func))
            return func
        return register_command

    async def on_ready(self):
        print('Logged on as', self.user)


client = RemBotClient()


@client.register('r/')
async def reddit(client, command, message):
    await message.channel.send(f'https://reddit.com/{message.content}')


@client.register('ping')
async def pong(client, command, message):
    await message.channel.send('pong')


@client.register(['flip', 'ban', 'yeet'])
async def flip(client, command, message):
    flipped = message.content[len(command):]
    for member in message.mentions:
        if '!' in member.mention:
            mention_with_bang = member.mention
            mention = member.mention.replace('!', '')
        else:
            mention_with_bang = member.mention.replace('@', '@!')
            mention = member.mention
        flipped = flipped.replace(mention, member.display_name)
        flipped = flipped.replace(mention_with_bang, member.display_name)
    flipped = upsidedown.transform(flipped)
    await message.channel.send(f'(╯°□°）╯︵ ┻━┻ {flipped}')


@client.register(['re:nick', 're:name'])
async def renick(client, command, message):
    if len(message.mentions) == 1:
        member = message.mentions[0]
        old_name = member.display_name
        print(message.content)
        mention = member.mention
        new_name = re.match(rf'{command}:?\s+<@!?\d+>\s*(.*)', message.content).group(1)
        try:
            await member.edit(nick=new_name)
        except discord.errors.HTTPException as e:
            await message.channel.send(str(e))
        else:
            await message.channel.send(f'{old_name} is now known as {new_name}')


@client.register(['re:mind'])
async def remind(client, command, message):
    # re:mind tomorrow "Unmute yourself"  @fmdfkja  @fgf  @fmdhjfkja
    
    if match := re.match(rf'{command}:?\s+(.*)\s+(?:\"(.*)\").*', message.content):
        time, msg = match.groups()
        time_struct, parse_status = client.cal.parse(time)
        delta = datetime(*time_struct[:6]) - datetime.now()
        secs = delta.total_seconds()
        key = random.choice(WORDS).lower()  # random word from the system wordlist
        if secs > 0:
            await message.channel.send(f're:mind-er set! use "re:mind:cancel {key}" to cancel this re:mind-er')
            client.reminders[key] = asyncio.create_task(do_reminder(secs, msg, message))
    elif match := re.match(rf'{command}:cancel (\w+)', message.content):
        key = match.group(1)
        if key in client.reminders:
            client.reminders[key].cancel()
            await message.channel.send(f're:minder {key} cancelled!')
        else:
            await message.channel.send(f'There is no re:mind-er {key}!')


client.run(TOKEN)
