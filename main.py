import re
import discord

with open('.token') as f:
    TOKEN = f.read().strip()

class RemBotClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = []

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

@client.register(['re:nick', 're:name'])
async def renick(client, command, message):
    if len(message.mentions) == 1:
        member = message.mentions[0]
        old_name = member.display_name
        print(message.content)
        mention = member.mention
        new_name = re.match(rf'{command}\s+<@!?\d+>\s*(.*)', message.content).group(1)
        try:
            await member.edit(nick=new_name)
        except discord.errors.HTTPException as e:
            await message.channel.send(str(e))
        else:
            await message.channel.send(f'{old_name} is now known as {new_name}')

client.run(TOKEN)
