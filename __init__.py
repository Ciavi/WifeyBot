import enum
import logging
import os
import platform
from datetime import datetime
from itertools import groupby

import discord
import time
from discord import app_commands, Interaction, Member, Embed, Colour, File, Permissions

from discord.ext import commands
from dotenv import load_dotenv
from os import environ as env

import system.configuration
import system.historian
from data.interface import u_marry, read_or_create_user, u_divorce, u_emancipate, u_abandon, u_adopt, u_are_related, \
    u_has_parent, u_graph, u_graph, u_relation_between, update_or_create_user, delete_user
from discord.views import MarryView

load_dotenv()

start_time = datetime.now()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

configuration = system.configuration.Configuration('conf.json')
logger = system.historian.Logging(configuration)

bot = commands.Bot(command_prefix='$', intents=intents)

async def setup_hook():
    await bot.tree.sync()
    await bot.add_cog(AdminGroup(bot))

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

    timestamp = int(time.time()) + 60*5

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


async def embed_info(target: Member):
    u_target = await read_or_create_user(user_id=target.id)
    parent = await u_target.parent.single()
    partners = [k for k, v in groupby(sorted(await u_target.partners.all(), key=lambda x: x.user_id))]
    children = [k for k, v in groupby(sorted(await u_target.children.all(), key=lambda x: x.user_id))]

    partner_count = len(partners)
    children_count = len(children)

    embed = Embed(colour=Colour.random(), title=f"{target.nick if target.nick is not None else target.name}")
    embed.description = f"Has {partner_count} partners and {children_count} children.\n{"Has a parent." if parent is not None else "Is orphan."}"
    embed.set_thumbnail(url=target.avatar.url)

    if u_target.user_omega and u_target.user_otype:
        embed.add_field(name="Type", value=f"{u_target.user_otype} ({u_target.user_osub or "N/A"})")

    lines = []
    if parent is not None:
        lines.append(f"**Parent:** `{parent.user_name}`.")

        siblings = [k for k, v in groupby(sorted(await parent.children.all(), key=lambda x: x.user_id))]
        siblings = filter(lambda x: x.user_id != target.id, siblings)
        siblings = [f"`{x.user_name}`" for x in siblings]

        lines.append(f"**Siblings:** {', '.join(siblings)}.")

    if partner_count > 0:
        partners = [f"`{x.user_name}`" for x in partners]
        lines.append(f"**Partners:** {', '.join(partners)}.")

    if children_count > 0:
        children = [f"`{x.user_name}`" for x in children]
        lines.append(f"**Children:** {', '.join(children)}.")

    return embed, '\n'.join(lines)


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

    await interaction.edit_original_response(embed=embed, attachments=[file])


@bot.tree.command(name="relate", description="Get how user_a (default = you) is related to user_b")
@app_commands.describe(user_a="First user")
@app_commands.describe(user_b="Second user")
async def relate(interaction: Interaction, user_b: Member, user_a: Member = None):
    # Command may take longer than 5 seconds
    await interaction.response.defer()

    if user_a is None:
        user_a = interaction.user

    path, relationship = await u_relation_between(invoker=user_a, target=user_b)

    if path == "UNRELATED":
        await interaction.edit_original_response(content=f"{user_a.nick if user_a.nick is not None else user_a.name} and {user_b.nick if user_b.nick is not None else user_b.name} are {relationship[0].lower()}.\n-# {path}")
        return

    await interaction.edit_original_response(content=f"{user_a.nick if user_a.nick is not None else user_a.name} is {user_b.nick if user_b.nick is not None else user_b.name}'s {relationship[0].lower()}.\n-# {path}")


@bot.tree.command(name="info", description="Show a your or user's information, including immediate family (parent, partners, children)")
@app_commands.describe(user="The user you wanna see")
async def info(interaction: Interaction, user: Member = None):
    #Command may take longer than 5 seconds
    await interaction.response.defer()

    if user is None:
        user = interaction.user

    embed, message = await embed_info(user)

    await interaction.edit_original_response(embed=embed)

    if len(message) > 1:
        await interaction.followup.send(message)


class OmegaType(enum.Enum):
    Alpha = "Alpha"
    Beta = "Beta"
    Omega = "Omega"


@bot.tree.command(name="omegaverse", description="A brainrot enhancement. Pheromone-based™. One time use, be truthful UwU.")
@app_commands.describe(otype="Are you an alpha, a beta or an omega? OwO")
@app_commands.describe(subtype="Subtype, if available.")
async def omega(interaction: Interaction, otype: OmegaType, subtype: str = ""):
    user = await read_or_create_user(user_id=interaction.user.id)

    if user.user_omega is False or None:
        await interaction.response.send_message(f"This is your first time running this command. Do [this test](https://www.quotev.com/quiz/15192538/Accurate-Omegaverse-Quiz-100-Guarantee) and then run this command. Be honest OwO")
        await update_or_create_user(user_id=interaction.user.id, user_omega=True)
        return

    await update_or_create_user(user_id=interaction.user.id, user_otype=otype.value, user_osub=subtype)
    await interaction.response.send_message(f"Updated. Welcome to the brainrot, ***{otype.value}***.")


# Owner section :D, Owner only

class UserAttribute(enum.Enum):
    Name = "user_name"
    Omega = "user_omega"
    OmegaverseType = "user_otype"
    OmegaverseSub = "user_osub"


async def is_bot_owner(interaction: Interaction):
    return await bot.is_owner(interaction.user)


class AdminGroup(commands.GroupCog, name="admin", description="Administrative commands"):
    def __init__(self, client: commands.Bot):
        self.bot = client

    @app_commands.command(name="stats", description="Show bot statistics and status")
    @app_commands.check(is_bot_owner)
    async def stats(self, interaction: Interaction):
        uptime = datetime.now() - start_time

        embed = Embed(title="Statistics", colour=discord.Colour.random())
        embed.add_field(name="Uptime", value=f"{str(uptime)}")
        embed.add_field(name="System", value=f"{platform.platform()}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="set_user", description="Set a user's attribute")
    @app_commands.check(is_bot_owner)
    @app_commands.describe(user="The user you wanna edit")
    @app_commands.describe(attribute="The attribute you wanna change")
    @app_commands.describe(value="The new value")
    async def set_user(self, interaction: Interaction, user: Member, attribute: UserAttribute, value: str):
        kwargs = { f"{attribute}": value }
        await update_or_create_user(user_id=user.id, kwargs=kwargs)

        await interaction.response.send_message(f"Set {attribute} to {value} for user {user.mention}.", ephemeral=True)

    @app_commands.command(name="del_user", description="Delete a user")
    @app_commands.check(is_bot_owner)
    @app_commands.describe(user="The user you wanna delete")
    async def del_user(self, interaction: Interaction, user: Member):
        await delete_user(user_id=user.id)

        await interaction.response.send_message(f"Deleted {user.mention} from database.")


discord_logger = logging.getLogger('discord')
discord_logger.setLevel('DEBUG')
discord_logger.handlers.clear()
for s_logger in logger.loggers:
    discord_logger.addHandler(s_logger.handlers[0])


bot.run(env['DISCORD_TOKEN'], log_handler=None)