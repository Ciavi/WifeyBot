import random
import string

import discord
import matplotlib.pyplot as plt
import networkx

from data.models import User


async def read_or_create_user(user_id: int, **kwargs):
    dict_param = { 'user_id': user_id }
    dict_param.update(kwargs)

    record: list[User] = await User.get_or_create(dict_param)

    return record[0]


async def update_or_create_user(user_id: int, **kwargs):
    dict_param = {'user_id': user_id }
    dict_param.update(kwargs)

    record: list[User] = await User.create_or_update(dict_param)

    return record[0]


async def delete_user(user_id: int):
    await User.nodes.delete(user_id=user_id)


async def u_are_related(invoker: discord.User | discord.Member, target: discord.User | discord.Member):
    d_invoker: User = await update_or_create_user(user_id=invoker.id, user_name=invoker.name)
    d_target: User = await update_or_create_user(user_id=target.id, user_name=target.name)

    are_married: bool = await d_invoker.partners.is_connected(d_target) or await d_target.partners.is_connected(d_invoker)
    are_relatives: bool = await d_invoker.children.is_connected(d_target) or await d_target.children.is_connected(d_invoker)

    return are_married or are_relatives, "PARTNERS" if are_married else "RELATIVES"


async def u_marry(invoker: discord.User | discord.Member, target: discord.User | discord.Member):
    d_invoker: User = await update_or_create_user(user_id=invoker.id, user_name=invoker.name)
    d_target: User = await update_or_create_user(user_id=target.id, user_name=target.name)

    if await d_invoker.partners.is_connected(d_target) or await d_target.partners.is_connected(d_invoker):
        return

    await d_invoker.partners.connect(d_target)
    await d_target.partners.connect(d_invoker)


async def u_divorce(invoker: discord.User | discord.Member, target: discord.User | discord.Member):
    d_invoker: User = await update_or_create_user(user_id=invoker.id, user_name=invoker.name)
    d_target: User = await update_or_create_user(user_id=target.id, user_name=target.name)

    await d_invoker.partners.disconnect(d_target)
    await d_target.partners.disconnect(d_invoker)


async def u_has_parent(target: discord.User | discord.Member):
    d_target: User = await update_or_create_user(user_id=target.id, user_name=target.name)

    return True if await d_target.parent.get_len() > 0 else False


async def u_adopt(invoker: discord.User | discord.Member, target: discord.User | discord.Member):
    d_invoker: User = await update_or_create_user(user_id=invoker.id, user_name=invoker.name)
    d_target: User = await update_or_create_user(user_id=target.id, user_name=target.name)

    if await d_invoker.children.is_connected(d_target) or await d_target.parent.is_connected(d_invoker):
        return

    await d_invoker.children.connect(d_target)
    await d_target.parent.connect(d_invoker)


async def u_abandon(invoker: discord.User | discord.Member, target: discord.User | discord.Member):
    d_invoker: User = await update_or_create_user(user_id=invoker.id, user_name=invoker.name)
    d_target: User = await update_or_create_user(user_id=target.id, user_name=target.name)

    await d_invoker.children.disconnect(d_target)
    await d_target.parent.disconnect(d_invoker)


async def u_emancipate(invoker: discord.User | discord.Member):
    d_invoker: User = await update_or_create_user(user_id=invoker.id, user_name=invoker.name)
    d_target: User = await d_invoker.parent.end_node()

    await d_invoker.children.disconnect(d_target)
    await d_target.parent.disconnect(d_invoker)


async def u_graph(target: discord.User | discord.Member):
    d_target: User = await update_or_create_user(user_id=target.id, user_name=target.name)
    t_partners: list[User] = await d_target.partners.all()
    t_children: list[User] = await d_target.children.all()
    t_parent: User = await d_target.parent.single()

    graph = networkx.MultiDiGraph()
    graph.add_node(d_target.user_name, color="#8E7DBE", label_color="#E8E5F2")

    if t_parent is not None:
        graph.add_node(t_parent.user_name, color="#A6D6D6", label_color="#84ABAB")
        graph.add_edge(
            d_target.user_name,
            t_parent.user_name,
            relationship="Is child of",
            color="#A6D6D6",
            label_color="#84ABAB"
        )

    for t_partner in t_partners:
        graph.add_node(t_partner.user_name, color="#F7CFD8", label_color="#C5A5AC")
        graph.add_edge(
            d_target.user_name,
            t_partner.user_name,
            relationship="Is married to",
            color="#F7CFD8",
            label_color="#C5A5AC"
        )

        partners: list[User] = await t_partner.partners.all()
        children: list[User] = await t_partner.children.all()

        for partner in partners:
            graph.add_node(partner.user_name, color="#F7CFD8", label_color="#C5A5AC")
            graph.add_edge(
                t_partner.user_name,
                partner.user_name,
                relationship="Is married to",
                color="#F7CFD8",
                label_color="#C5A5AC"
            )

        for child in children:
            graph.add_node(child.user_name, color="#F4F8D3", label_color="#C3C6A8")
            graph.add_edge(
                child.user_name,
                t_partner.user_name,
                relationship="Is child of",
                color="#F4F8D3",
                label_color="#C3C6A8"
            )

    for t_child in t_children:
        graph.add_node(t_child.user_name, color="#F4F8D3", label_color="#C3C6A8")
        graph.add_edge(
            t_child.user_name,
            d_target.user_name,
            relationship="Is child of",
            color="#F4F8D3",
            label_color="#C3C6A8"
        )

    node_colors = list(networkx.get_node_attributes(graph, "color").values())
    node_colors_label = list(networkx.get_node_attributes(graph, "label_color").values())
    edge_colors = list(networkx.get_edge_attributes(graph, "color").values())
    edge_colors_label = list(networkx.get_edge_attributes(graph, "label_color").values())

    pos = networkx.spring_layout(graph)
    networkx.draw(graph, pos, with_labels=True, node_color=node_colors, edge_color=edge_colors, font_color=node_colors_label)
    edge_labels = networkx.get_edge_attributes(graph, "relationship")
    networkx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_color="#FFFFFF", bbox={ "fc": "#1F2644", "ec": "#1F2644" })

    letters = string.ascii_lowercase
    uid = ''.join(random.choice(letters) for _ in range(12))

    plt.savefig(f"tmp/{target.id}-{uid}.png", format="png", dpi=300, bbox_inches="tight", facecolor="#1F2644")
    plt.close("all")
    return uid