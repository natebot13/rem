import re
import discord
import upsidedown
import parsedatetime
from datetime import datetime
import asyncio
import random
import json

from string import ascii_lowercase
from string import ascii_uppercase

# shamelessly stolen from the OCF ircbot ocf.io/gh/ircbot
WIDETEXT_MAP = {i: i + 0xFEE0 for i in range(0x21, 0x7F)}

# the space character has unique mapping to become a unicode ideographic space
WIDE_SPACE_VALUE = 0x3000
WIDE_SPACE_CHAR = chr(WIDE_SPACE_VALUE)
SPACE_VALUE = ord(' ')
WIDETEXT_MAP[SPACE_VALUE] = WIDE_SPACE_VALUE

# As seen in Samurai Jack
THICC = '卂乃匚刀乇下厶卄工丁长乚从几口尸㔿尺丂丅凵リ山乂丫乙'


# Little hack, because translation tables are just dicts
LOWER_THICC = {k: v for k, v in str.maketrans(ascii_lowercase, THICC).items() if v is not None}
UPPER_THICC = {k: v for k, v in str.maketrans(ascii_uppercase, THICC).items() if v is not None}
THICC_MAP = {
    **LOWER_THICC,
    **UPPER_THICC,
    SPACE_VALUE: WIDE_SPACE_VALUE,
}

def change_text(text, translation, width=0):
    return ''.join((c.translate(translation) + WIDE_SPACE_CHAR * width for c in text))


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
        time_struct, status = client.cal.parse(time)
        if status == 0:
            await message.channel.send(f'Failed to set the re:mind-er. Could not understand the time you specified.')
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

@client.register(['re:thiccen', 'thiccen'])
async def wide(client, command, message):
    if match := re.match(rf'{command}:?\s+(.*)', message.content):
        await message.channel.send(f'{change_text(match.group(1), THICC_MAP, 0)}')

@client.register(['re:wide', '!w'])
async def thiccen(client, command, message):
    if match := re.match(rf'{command}(\d?):?\s+(.*)', message.content):
        if match.group(1) != '':
            width = int(match.group(1)) - 1
        else:
            width = 0
        await message.channel.send(f'{change_text(match.group(2), WIDETEXT_MAP, width)}')

# @client.register('re:tz', 'tz')
# async def tz(client, command, message):
#     # {userid: tz, user2: tz}
#     if match := re.match(rf'{command}:?\s*(.*)'):
#         with open('timezones.json', 'r+') as tz_json:
#             user_tz = json.read(tz_json.read())
#             user_tz[message.author.id] = match.group(1)
#             tz_json.write(json.dump(user_tz))


# @client.register('')
# async def detect_time(client, command, message):
#     time_struct, status = client.cal.parse(message.content)
#     if (status == 0):
#       return
#     dt = datetime(*time_struct[:6])
#     with open('timezones.json', 'r') as tz_json:
#         user_tz = json.read(tz_json.read())
#         tz = user_tz[message.author.id]
#     await message.channel.send(f"That's:\n")
    

client.run(TOKEN)
