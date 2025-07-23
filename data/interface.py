import enum
import random
import string
from dataclasses import dataclass

import discord
import matplotlib.pyplot as plt
import networkx
import pydot
from neomodel import adb

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


def classify_relationship(path: list[str]):
    match path:
        case ["HAS_CHILD"]:
            return "Parent", "Child"
        case ["←HAS_CHILD"]:
            return "Child", "Parent"
        case ["HAS_CHILD", "HAS_CHILD"]:
            return "Grandparent", "Grandchild"
        case ["←HAS_CHILD", "←HAS_CHILD"]:
            return "Grandchild", "Grandparent"
        case ["HAS_CHILD", "HAS_CHILD", "HAS_CHILD"]:
            return "Great-grandparent", "Great-grandchild"
        case ["←HAS_CHILD", "←HAS_CHILD", "←HAS_CHILD"]:
            return "Great-grandchild", "Great-grandparent"

        case ["IS_PARTNER_WITH"] | ["←IS_PARTNER_WITH"]:
            return "Partner", "Partner"
        case ["HAS_CHILD", "IS_PARTNER_WITH"] | ["HAS_CHILD", "←IS_PARTNER_WITH"]:
            return "Parent-in-law", "Child-in-law"
        case ["IS_PARTNER_WITH", "←HAS_CHILD"] | ["←IS_PARTNER_WITH", "←HAS_CHILD"]:
            return "Child-in-law", "Parent-in-law"
        case ["IS_PARTNER_WITH", "HAS_CHILD"] | ["←IS_PARTNER_WITH", "HAS_CHILD"]:
            return "Step-parent", "Step-child"
        case ["←HAS_CHILD", "IS_PARTNER_WITH"] | ["←HAS_CHILD", "←IS_PARTNER_WITH"]:
            return "Step-child", "Step-parent"

        case ["HAS_CHILD", "HAS_CHILD", "IS_PARTNER_WITH"] | ["HAS_CHILD", "HAS_CHILD", "←IS_PARTNER_WITH"]:
            return "Grandparent-in-law", "Grandchild-in-law"
        case ["IS_PARTNER_WITH", "←HAS_CHILD", "←HAS_CHILD"] | ["←IS_PARTNER_WITH", "←HAS_CHILD", "←HAS_CHILD"]:
            return "Grandchild-in-law", "Grandparent-in-law"
        case ["IS_PARTNER_WITH", "HAS_CHILD", "HAS_CHILD"] | ["←IS_PARTNER_WITH", "HAS_CHILD", "HAS_CHILD"]:
            return "Step-grandparent", "Step-grandchild"
        case ["←HAS_CHILD", "←HAS_CHILD", "IS_PARTNER_WITH"] | ["←HAS_CHILD", "←HAS_CHILD", "←IS_PARTNER_WITH"]:
            return "Step-grandchild", "Step-grandparent"

        case ["←HAS_CHILD", "HAS_CHILD"]:
            return "Sibling", "Sibling"
        case ["←HAS_CHILD", "IS_PARTNER_WITH", "HAS_CHILD"] | ["←HAS_CHILD", "←IS_PARTNER_WITH", "HAS_CHILD"]:
            return "Step-sibling", "Step-sibling"

        case ["←HAS_CHILD", "HAS_CHILD", "HAS_CHILD"]:
            return "Aunt/Uncle", "Niece/Nephew"
        case ["←HAS_CHILD", "←HAS_CHILD", "HAS_CHILD"]:
            return "Niece/Nephew", "Aunt/Uncle"
        case ["←HAS_CHILD", "HAS_CHILD", "HAS_CHILD", "HAS_CHILD"]:
            return "Great-Aunt/Uncle", "Grandniece/Nephew"
        case ["←HAS_CHILD", "←HAS_CHILD", "←HAS_CHILD", "HAS_CHILD"]:
            return "Grandniece/Nephew", "Great-Aunt/Uncle"

        case ["←HAS_CHILD", "←HAS_CHILD", "HAS_CHILD", "HAS_CHILD"]:
            return "Cousin", "Cousin"

        case []:
            return "Not related", "Not related"

        case _:
            return "Distant relative", "Distant relative"


async def u_relation_between(invoker: discord.User | discord.Member, target: discord.User | discord.Member):
    query = f"""
    MATCH path=shortestPath((a:User {{ user_id: {invoker.id} }})-[r*..6]-(b:User {{ user_id: {target.id} }}))
    WHERE all(rel IN r WHERE type(rel) <> 'IS_PARENT_OF')
    RETURN
        nodes(path) as node_objs,
        [rel in relationships(path) | {{type: type(rel), from: startNode(rel), to: endNode(rel)}}] as rel_objs
    """

    results, _ = await adb.cypher_query(query=query)

    if not results:
        return "UNRELATED", ("Not related", "Not related")

    node_objs, rel_objs = results[0]

    node_names = [n["user_name"] for n in node_objs]

    steps = []
    rel_types = []

    for i in range(len(rel_objs)):
        start_id = rel_objs[i]["from"]["user_id"]
        end_id = rel_objs[i]["to"]["user_id"]
        rel_type = rel_objs[i]["type"]

        if node_objs[i]["user_id"] == start_id and node_objs[i + 1]["user_id"] == end_id:
            direction = "→"
            rel_types.append(rel_type)
        else:
            direction = "←"
            rel_types.append(f"←{rel_type}")

        steps.append(node_names[i])
        steps.append(f"{direction}{rel_type}")

    steps.append(node_names[-1])
    path_trace = " ".join(steps)
    relationship = classify_relationship(rel_types)

    return path_trace, relationship


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
    otype: str = None


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

    add_node(Node(d_target.user_name, NodeType.SELF, d_target.user_otype))

    if t_parent is not None:
        add_node(Node(t_parent.user_name, NodeType.PARENT, t_parent.user_otype))
        add_edge(Edge(d_target.user_name, t_parent.user_name, EdgeType.CHILD))

        tt_partners: list[User] = await t_parent.partners.all()
        tt_children: list[User] = await t_parent.children.all()

        for tt_partner in tt_partners:
            add_node(Node(tt_partner.user_name, NodeType.PARTNER, tt_partner.user_otype))
            add_edge(Edge(t_parent.user_name, tt_partner.user_name, EdgeType.PARTNER))

        for tt_child in tt_children:
            add_node(Node(tt_child.user_name, NodeType.CHILD, tt_child.user_otype))
            add_edge(Edge(tt_child.user_name, t_parent.user_name, EdgeType.CHILD))

    for t_partner in t_partners:
        add_node(Node(t_partner.user_name, NodeType.PARTNER, t_partner.user_otype))
        add_edge(Edge(d_target.user_name, t_partner.user_name, EdgeType.PARTNER))

        tt_partners: list[User] = await t_partner.partners.all()
        tt_children: list[User] = await t_partner.children.all()

        for tt_partner in tt_partners:
            add_node(Node(tt_partner.user_name, NodeType.PARTNER, tt_partner.user_otype))
            add_edge(Edge(t_partner.user_name, tt_partner.user_name, EdgeType.PARTNER))

        for tt_child in tt_children:
            add_node(Node(tt_child.user_name, NodeType.CHILD, tt_child.user_otype))
            add_edge(Edge(tt_child.user_name, t_partner.user_name, EdgeType.CHILD))

    for t_child in t_children:
        add_node(Node(t_child.user_name, NodeType.CHILD, t_child.user_otype))
        add_edge(Edge(t_child.user_name, d_target.user_name, EdgeType.CHILD))

    graph = networkx.MultiDiGraph()
    for label, node in node_table.items():
        otype: str = "A" if node.otype == "Alpha" else "Β" if node.otype == "Beta" else "Ω" if node.type == "Omega" else None
        graph.add_node(f"{otype + ": " if otype is not None else ""}{label}", type=node.type.name, otype=otype)
    for (f, t), edge in edge_table.items():
        graph.add_edge(f, t, type=edge.type.name)

    node_styles = {
        NodeType.SELF.name: { "fillcolor": "#ff6361", "fontcolor": "#ffdfdf" },
        NodeType.PARENT.name: { "fillcolor": "#58508d", "fontcolor": "#dddce8" },
        NodeType.PARTNER.name: { "fillcolor": "#bc5090", "fontcolor": "#25101c" },
        NodeType.CHILD.name: { "fillcolor": "#ffa600", "fontcolor": "#332100" }
    }

    edge_styles = {
        EdgeType.PARTNER.name: { "color": "#e4b9d2", "fontcolor": "#e4b9d2" },
        EdgeType.CHILD.name: { "color": "#ffdb99", "fontcolor": "#ffdb99" }
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
    pdot.set("bgcolor", "#001924")

    for node in pdot.get_nodes():
        node_name = node.get_name().strip()
        node_type = graph.nodes[node_name].get("type", "SELF")
        style = node_styles.get(node_type)

        node.set("shape", "circle")
        node.set("penwidth", 2.0)
        node.set("color", "#ffffff80")
        node.set("style", "filled")
        node.set("fillcolor", style.get("fillcolor"))
        node.set("fontname", "DejaVu Sans")
        node.set("fontcolor", style.get("fontcolor"))
        node.set("fontsize", 14.0)

    for edge in pdot.get_edges():
        edge_type = edge.get("type")
        style = edge_styles.get(edge_type)

        edge.set("dir", "both" if edge_type == EdgeType.PARTNER.name else "forward")
        edge.set("label", "is married to" if edge_type == EdgeType.PARTNER.name else "is child of")
        edge.set("arrowsize", 0.25)
        edge.set("weight", 0.5)
        edge.set("color", style.get("color"))
        edge.set("fontname", "DejaVu Sans")
        edge.set("fontcolor", style.get("fontcolor"))
        edge.set("fontsize", 10.0)


    letters = string.ascii_lowercase
    uid = ''.join(random.choice(letters) for _ in range(12))

    pdot.write_png(f"tmp/{target.id}-{uid}.png")
    return uid