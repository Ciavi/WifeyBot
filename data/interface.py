import enum
import random
import string
from dataclasses import dataclass

import discord
import matplotlib.pyplot as plt
import networkx
import pydot

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


class NodeType(enum.IntEnum):
    SELF = 0
    PARENT = 1
    PARTNER = 2
    CHILD = 3


class EdgeType(enum.IntEnum):
    PARTNER = 0
    CHILD = 1


@dataclass(frozen=True)
class Node:
    label: str
    type: NodeType


@dataclass(frozen=True)
class Edge:
    f: str
    t: str
    type: EdgeType


async def u_graph(target: discord.User | discord.Member):
    node_table: dict[str, Node] = {}
    edge_table: dict[tuple[str, str], Edge] = {}

    def add_node(new: Node):
        existing = node_table.get(new.label)
        if not existing:
            node_table[new.label] = new
        else:
            if new.type < existing.type:
                node_table[new.label] = new

    def add_edge(new: Edge):
        existing = edge_table.get((new.f, new.t)) or edge_table.get((new.t, new.f))
        if not existing:
            edge_table[(new.f, new.t)] = new
        else:
            if new.type != existing.type:
                edge_table[(new.f, new.t)] = new

    d_target: User = await update_or_create_user(user_id=target.id, user_name=target.name)
    t_partners: list[User] = await d_target.partners.all()
    t_children: list[User] = await d_target.children.all()
    t_parent: User = await d_target.parent.single()

    add_node(Node(d_target.user_name, NodeType.SELF))

    if t_parent is not None:
        add_node(Node(t_parent.user_name, NodeType.PARENT))
        add_edge(Edge(d_target.user_name, t_parent.user_name, EdgeType.CHILD))

    for t_partner in t_partners:
        add_node(Node(t_partner.user_name, NodeType.PARTNER))
        add_edge(Edge(d_target.user_name, t_partner.user_name, EdgeType.PARTNER))

        tt_partners: list[User] = await t_partner.partners.all()
        tt_children: list[User] = await t_partner.children.all()

        for tt_partner in tt_partners:
            add_node(Node(tt_partner.user_name, NodeType.PARTNER))
            add_edge(Edge(t_partner.user_name, tt_partner.user_name, EdgeType.PARTNER))

        for tt_child in tt_children:
            add_node(Node(tt_child.user_name, NodeType.CHILD))
            add_edge(Edge(tt_child.user_name, t_partner.user_name, EdgeType.CHILD))

    for t_child in t_children:
        add_node(Node(t_child.user_name, NodeType.CHILD))
        add_edge(Edge(t_child.user_name, d_target.user_name, EdgeType.CHILD))

    graph = networkx.MultiDiGraph()
    for label, node in node_table.items():
        graph.add_node(label, type=node.type.name)
    for (f, t), edge in edge_table.items():
        graph.add_edge(f, t, type=edge.type.name)

    node_styles = {
        NodeType.SELF.name: { "fillcolor": "#ff6361", "fontcolor": "#fff" },
        NodeType.PARENT.name: { "fillcolor": "#58508d", "fontcolor": "#fff" },
        NodeType.PARTNER.name: { "fillcolor": "#bc5090", "fontcolor": "#fff" },
        NodeType.CHILD.name: { "fillcolor": "#ffa600", "fontcolor": "#fff" }
    }

    edge_styles = {
        EdgeType.PARTNER.name: { "color": "#bc5090", "fontcolor": "#bc5090" },
        EdgeType.CHILD.name: { "color": "#ffa600", "fontcolor": "#ffa600" }
    }

    pdot = networkx.drawing.nx_pydot.to_pydot(graph)

    pdot.set("dpi", 300)
    pdot.set("layout", "neato")
    pdot.set("mode", "hier")
    pdot.set("model", "subset")
    pdot.set("normalize", True)
    pdot.set("overlap", "prism")
    pdot.set("overlap_scaling", -4)
    pdot.set("splines", "curved")
    pdot.set("bgcolor", "#003f5c")

    for node in pdot.get_nodes():
        node_name = node.get_name().strip()
        node_type = graph.nodes[node_name].get("type", "SELF")
        style = node_styles.get(node_type)

        node.set("shape", "circle")
        node.set("regular", True)
        node.set("fixedsize", True)
        node.set("height", 0.25)
        node.set("width", 0.25)
        node.set("penwidth", 0.5)
        node.set("pencolor", "#ffffff")
        node.set("style", "filled")
        node.set("fillcolor", style.get("fillcolor"))
        node.set("fontname", "DejaVu Sans")
        node.set("fontcolor", style.get("fontcolor"))
        node.set("fontsize", 6.0)

    for edge in pdot.get_edges():
        edge_type = edge.get("type")
        style = edge_styles.get(edge_type)

        edge.set("dir", "both" if edge_type == EdgeType.PARTNER.name else "forward")
        edge.set("label", "m." if edge_type == EdgeType.PARTNER.name else "c.")
        edge.set("arrowsize", 0.25)
        edge.set("weight", 0.5)
        edge.set("color", style.get("color"))
        edge.set("fontname", "DejaVu Sans")
        edge.set("fontcolor", style.get("fontcolor"))
        edge.set("fontsize", 3.0)


    letters = string.ascii_lowercase
    uid = ''.join(random.choice(letters) for _ in range(12))

    pdot.write_png(f"tmp/{target.id}-{uid}.png")
    return uid