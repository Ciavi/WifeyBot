import logging

import discord
from discord import app_commands, Interaction, Member, Embed, Colour

from discord.ext import commands
from dotenv import load_dotenv
from os import environ as env

import system.configuration
import system.historian
from data.interface import u_marry, read_or_create_user, u_divorce, u_emancipate, u_abandon, u_adopt
from discord.views import MarryView

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

configuration = system.configuration.Configuration('conf.json')
logger = system.historian.Logging(configuration)

bot = commands.Bot(command_prefix='$', intents=intents)

async def setup_hook():
    await bot.tree.sync()

bot.setup_hook = setup_hook


async def callback_marry(interaction: Interaction):
    b_marry: bool = True if str(interaction.data["custom_id"].split(":")[0]) == "yes" else False
    invoker_id: int = int(interaction.data["custom_id"].split(":")[1])
    invoker = bot.get_user(invoker_id)

    if b_marry:
        await u_marry(invoker=invoker, target=interaction.user)
        await interaction.response.send_message(content=f"Congratulations to {invoker.mention} and {interaction.user.mention} on their marriage!")
    else:
        await interaction.response.send_message(content=f"Ouch. It's a no.")


async def embed_marry(invoker: Member, target: Member):
    u_invoker = await read_or_create_user(user_id=invoker.id)
    partners = await u_invoker.partners.all()
    children = await u_invoker.children.all()

    view = MarryView(user=target, invoker=invoker, callback=callback_marry)

    embed = Embed(colour=Colour.random(), title=f"{target.nick}, {invoker.nick} longs for you.")
    embed.description = (f"Will you make them your partner? <:UwU_GT:1278010153806987317>\n"
                         f"They have {len(partners)} partners and {len(children)} children.")

    return embed, view


async def callback_adopt(interaction: Interaction):
    b_adopt: bool = True if str(interaction.data["custom_id"].split(":")[0]) == "yes" else False
    invoker_id: int = int(interaction.data["custom_id"].split(":")[1])
    invoker = bot.get_user(invoker_id)

    if b_adopt:
        await u_adopt(invoker=invoker, target=interaction.user)
        await interaction.response.send_message(content=f"Congratulations to {invoker.mention} and {interaction.user.mention} on the adoption!")
    else:
        await interaction.response.send_message(content=f"Ouch. It's a no.")


async def embed_adopt(invoker: Member, target: Member):
    u_invoker = await read_or_create_user(user_id=invoker.id)
    partners = await u_invoker.partners.all()
    children = await u_invoker.children.all()

    view = MarryView(user=target, invoker=invoker, callback=callback_adopt)

    embed = Embed(colour=Colour.random(), title=f"{target.nick}, {invoker.nick} wants to adopt you.")
    embed.description = (f"Will you become their adopted child? <:UwU_GT:1278010153806987317>\n"
                         f"They have {len(partners)} partners and {len(children)} children.")

    return embed, view


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name}#{bot.user.discriminator}")


@bot.tree.command(name="marry", description="Marry somebody")
@app_commands.describe(somebody="Your target :3")
async def marry(interaction: Interaction, somebody: Member):
    embed, view = await embed_marry(interaction.user, somebody)

    await interaction.response.send_message(content=f"{interaction.user.mention}, {somebody.mention}", embed=embed, view=view)


@bot.tree.command(name="adopt", description="Adopt somebody")
@app_commands.describe(somebody="Your target :3")
async def adopt(interaction: Interaction, somebody: Member):
    embed, view = await embed_adopt(interaction.user, somebody)

    await interaction.response.send_message(content=f"{interaction.user.mention}, {somebody.mention}", embed=embed, view=view)


@bot.tree.command(name="divorce", description="Divorce one of your partners")
@app_commands.describe(partner="The partner you wanna take to court :3")
async def divorce(interaction: Interaction, partner: Member):
    await u_divorce(invoker_id=interaction.user.id, target_id=partner.id)

    await interaction.response.send_message(f"You're not partners with {partner.mention} anymore 💔.")


@bot.tree.command(name="emancipate", description="Run away from your parent")
async def emancipate(interaction: Interaction):
    await u_emancipate(invoker_id=interaction.user.id)

    await interaction.response.send_message(f"You ran away from your parent <:aquacry:1278013053270753374>.")


@bot.tree.command(name="abandon", description="Abandon one of your children")
@app_commands.describe(child="The child you wanna abandon :3")
async def abandon(interaction: Interaction, child: Member):
    await u_abandon(invoker_id=interaction.user.id, target_id=child.id)

    await interaction.response.send_message(f"You abandoned {child.mention}, you monster <:aquacry:1278013053270753374>.")


discord_logger = logging.getLogger('discord')
discord_logger.setLevel('DEBUG')
discord_logger.handlers.clear()
for s_logger in logger.loggers:
    discord_logger.addHandler(s_logger.handlers[0])


bot.run(env['DISCORD_TOKEN'], log_handler=None)