import logging
import os

import discord
import time
from discord import app_commands, Interaction, Member, Embed, Colour, File

from discord.ext import commands
from dotenv import load_dotenv
from os import environ as env

import system.configuration
import system.historian
from data.interface import u_marry, read_or_create_user, u_divorce, u_emancipate, u_abandon, u_adopt, u_are_related, \
    u_has_parent, u_graph, u_graph, u_relation_between
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

    interaction.message.edit(view=None)

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

    partner_count = int(len(partners) / 2)
    children_count = len(children)

    timestamp = int(time.time()) + 60

    embed = Embed(colour=Colour.random(), title=f"{target.nick if target.nick is not None else target.name}, {invoker.nick if invoker.nick is not None else invoker.name} longs for you.")
    embed.description = (f"Will you make them your partner? <:UwU_GT:1278010153806987317>\n"
                         f"They have {partner_count} partners and {children_count} children.")
    embed.add_field(name="Expires in", value=f"<t:{timestamp}:R>", inline=False)

    return embed, view


async def callback_adopt(interaction: Interaction):
    b_adopt: bool = True if str(interaction.data["custom_id"].split(":")[0]) == "yes" else False
    invoker_id: int = int(interaction.data["custom_id"].split(":")[1])
    invoker = bot.get_user(invoker_id)

    interaction.message.edit(view=None)

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

    partner_count = int(len(partners) / 2)
    children_count = len(children)

    timestamp = int(time.time()) + 60*5

    embed = Embed(colour=Colour.random(), title=f"{target.nick if target.nick is not None else target.name}, {invoker.nick if invoker.nick is not None else invoker.name} wants to adopt you.")
    embed.description = (f"Will you become their adopted child? <:UwU_GT:1278010153806987317>\n"
                         f"They have {partner_count} partners and {children_count} children.")
    embed.add_field(name="Expires in", value=f"<t:{timestamp}:R>", inline=False)

    return embed, view


async def embed_graph(invoker: Member, target: Member):
    graph_uid = await u_graph(target=target)
    filename = f"tmp/{target.id}-{graph_uid}.png"

    file = File(filename)

    embed = Embed(colour=Colour.random(), title=f"Here's the graph you requested, {invoker.nick if invoker.nick is not None else invoker.name}")
    embed.set_image(url=f"attachment://{target.id}-{graph_uid}.png")

    return embed, file


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name}#{bot.user.discriminator}")


@bot.tree.command(name="marry", description="Marry somebody")
@app_commands.describe(somebody="Your target :3")
async def marry(interaction: Interaction, somebody: Member):
    are_related, _ = await u_are_related(invoker=interaction.user, target=somebody)

    if are_related:
        await interaction.response.send_message(content=f"You're already related to {somebody.mention}.", ephemeral=True)
        return

    embed, view = await embed_marry(interaction.user, somebody)

    await interaction.response.send_message(content=f"{interaction.user.mention}, {somebody.mention}", embed=embed, view=view)


@bot.tree.command(name="adopt", description="Adopt somebody")
@app_commands.describe(somebody="Your target :3")
async def adopt(interaction: Interaction, somebody: Member):
    has_parent = await u_has_parent(target=somebody)
    are_related, _ = await u_are_related(invoker=interaction.user, target=somebody)

    if are_related:
        await interaction.response.send_message(content=f"You're already related to {somebody.mention}.", ephemeral=True)
        return

    if has_parent:
        await interaction.response.send_message(content=f"{somebody.mention} already has a parent! Are you trying to steal them away?", ephemeral=True)
        return

    embed, view = await embed_adopt(interaction.user, somebody)

    await interaction.response.send_message(content=f"{interaction.user.mention}, {somebody.mention}", embed=embed, view=view)


@bot.tree.command(name="divorce", description="Divorce one of your partners")
@app_commands.describe(partner="The partner you wanna take to court :3")
async def divorce(interaction: Interaction, partner: Member):
    await u_divorce(invoker=interaction.user, target=partner)

    await interaction.response.send_message(f"You're not partners with {partner.mention} anymore 💔.")


@bot.tree.command(name="emancipate", description="Run away from your parent")
async def emancipate(interaction: Interaction):
    await u_emancipate(invoker=interaction.user)

    await interaction.response.send_message(f"You ran away from your parent <:aquacry:1278013053270753374>.")


@bot.tree.command(name="abandon", description="Abandon one of your children")
@app_commands.describe(child="The child you wanna abandon :3")
async def abandon(interaction: Interaction, child: Member):
    await u_abandon(invoker=interaction.user, target=child)

    await interaction.response.send_message(f"You abandoned {child.mention}, you monster <:aquacry:1278013053270753374>.")


@bot.tree.command(name="graph", description="Get your or a user's family graph")
@app_commands.describe(user="Whose graph you want to see")
async def graph(interaction: Interaction, user: Member = None):
    # Command may take longer than 5 seconds
    await interaction.response.defer()

    embed, file = await embed_graph(invoker=interaction.user, target=interaction.user if user is None else user)

    await interaction.response.send_message(embed=embed, file=file)


@bot.tree.command(name="relate", description="Get how user_a (default = you) is related to user_b")
@app_commands.describe(user_a="First user")
@app_commands.describe(user_b="Second user")
async def relate(interaction: Interaction, user_b: Member, user_a: Member = None):
    # Command may take longer than 5 seconds
    await interaction.response.defer()

    if user_a is None:
        user_a = interaction.user

    path, relationship = await u_relation_between(invoker=user_a, target=user_b)

    await interaction.response.send_message(content=f"{user_a.nick if user_a.nick is not None else user_a.name} is {user_b.nick if user_b.nick is not None else user_b.name}'s {relationship[0].lower()}.\n-# {path}")

discord_logger = logging.getLogger('discord')
discord_logger.setLevel('DEBUG')
discord_logger.handlers.clear()
for s_logger in logger.loggers:
    discord_logger.addHandler(s_logger.handlers[0])


bot.run(env['DISCORD_TOKEN'], log_handler=None)