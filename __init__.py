import logging

import discord

from discord.ext import commands
from dotenv import load_dotenv
from os import environ as env

import system.configuration
import system.historian

load_dotenv()

intents = discord.Intents.default()
intents.members = True

configuration = system.configuration.Configuration('conf.json')
logger = system.historian.Logging(configuration)

bot = commands.Bot(command_prefix='$', intents=intents)

async def setup_hook():
    await bot.tree.sync()

bot.setup_hook = setup_hook


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}#{bot.user.discriminator}')


discord_logger = logging.getLogger('discord')
discord_logger.setLevel('DEBUG')
discord_logger.handlers.clear()
for s_logger in logger.loggers:
    discord_logger.addHandler(s_logger.handlers[0])


bot.run(env['DISCORD_TOKEN'], log_handler=None)