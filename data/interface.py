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
    graph.add_node(d_target.user_name, color="#F7374F", label_color="#FFF")

    if t_parent is not None:
        graph.add_node(t_parent.user_name, color="#547b59", label_color="#FFF")
        graph.add_edge(
            d_target.user_name,
            t_parent.user_name,
            relationship="c.",
            color="#55cfe2",
            label_color="#55cfe2"
        )

    for t_partner in t_partners:
        if t_partner.user_name == d_target.user_name:
            graph.add_edge(
                d_target.user_name,
                t_partner.user_name,
                relationship="m.",
                color="#8ccd95",
                label_color="#8ccd95"
            )
            continue

        graph.add_node(t_partner.user_name, color="#547b59", label_color="#FFF")
        graph.add_edge(
            d_target.user_name,
            t_partner.user_name,
            relationship="m.",
            color="#8ccd95",
            label_color="#8ccd95"
        )

        partners: list[User] = await t_partner.partners.all()
        children: list[User] = await t_partner.children.all()

        for partner in partners:
            if partner.user_name == d_target.user_name:
                graph.add_edge(
                    t_partner.user_name,
                    d_target.user_name,
                    relationship="m.",
                    color="#8ccd95",
                    label_color="#8ccd95"
                )
                continue

            if t_parent is not None and partner.user_name == t_parent.user_name:
                graph.add_edge(
                    t_partner.user_name,
                    partner.user_name,
                    relationship="m.",
                    color="#8ccd95",
                    label_color="#8ccd95"
                )
                continue

            graph.add_node(partner.user_name, color="#547b59", label_color="#FFF")
            graph.add_edge(
                t_partner.user_name,
                partner.user_name,
                relationship="m.",
                color="#8ccd95",
                label_color="#8ccd95"
            )

        for child in children:
            graph.add_node(child.user_name, color="#8d6c79", label_color="#FFF")
            graph.add_edge(
                child.user_name,
                t_partner.user_name,
                relationship="c.",
                color="#ecb5ca",
                label_color="#ecb5ca"
            )

    for t_child in t_children:
        graph.add_node(t_child.user_name, color="#8d6c79", label_color="#FFF")
        graph.add_edge(
            t_child.user_name,
            d_target.user_name,
            relationship="c.",
            color="#ecb5ca",
            label_color="#ecb5ca"
        )

    node_colors = list(networkx.get_node_attributes(graph, "color").values())
    node_colors_label = list(networkx.get_node_attributes(graph, "label_color").values())
    edge_colors = list(networkx.get_edge_attributes(graph, "color").values())
    edge_colors_label = list(networkx.get_edge_attributes(graph, "label_color").values())

    pos = networkx.spring_layout(G=graph, k=3, scale=7.50, seed=42)

    ax = plt.gca()
    ax.set_facecolor("#00000000")
    ax.set_frame_on(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

    for i, node in enumerate(graph.nodes()):
        networkx.draw_networkx_nodes(graph, pos, nodelist=[node], node_color=node_colors[i])
        networkx.draw_networkx_labels(graph, pos, labels={node:node}, font_color=node_colors_label[i], font_size=8)

    i = 0
    for u, v, data in graph.edges(data=True):
        rel = data.get("relationship", "")
        networkx.draw_networkx_edges(graph, pos, edgelist=[(u, v)], connectionstyle="arc3,rad=0.075", width=0.5, arrowstyle="->", arrowsize=7, edge_color=edge_colors[i])
        networkx.draw_networkx_edge_labels(graph, pos, edge_labels={(u, v): rel}, font_color=edge_colors_label[i], font_size=4, bbox={ "fc": "#00000000", "ec": "#00000000", "boxstyle": "circle" })
        i += 1

    letters = string.ascii_lowercase
    uid = ''.join(random.choice(letters) for _ in range(12))

    plt.savefig(f"tmp/{target.id}-{uid}.png", format="png", dpi=300, bbox_inches="tight", facecolor="#00000000")
    plt.close("all")
    return uid

