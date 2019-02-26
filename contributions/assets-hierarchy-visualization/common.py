"""

DON'T BE SCARED

You can don't dig into details here

"""
from itertools import islice
from typing import Dict, Iterable

import networkx as nx
import pandas as pd
import plotly.graph_objs as go


def sliding_window(seq: Iterable, n: int = 2):
    """

    Generate an overlapping windows with variable size from iterator

    Args:
        seq:
        n:

    Returns:

    """
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


def make_assets_tree(df: pd.DataFrame) -> nx.DiGraph:
    """

    Generates directional graph of assets from a given dataframe
    
    Args:
        df:

    Returns:

    """

    G = nx.DiGraph()
    for path in df["path"].values:
        for parent_id, child_id in sliding_window(path, n=2):
            G.add_edge(parent_id, child_id)

    return G


def hierarchy_pos(
    graph: nx.DiGraph,
    root: str = None,
    width: float = 10000.0,
    vert_gap: float = 0.2,
    vert_loc: float = 0.0,
    x_center=0.5,
):
    """
    If the graph is a tree this will return the positions to plot this in a
    hierarchical layout.

    G: the graph (must be a tree)

    root: the root node of current branch
    - if the tree is directed and this is not given, the root will be found and used
    - if the tree is directed and this is given, then the positions will be just for the descendants of this node.
    - if the tree is undirected and not given, then a random choice will be used.

    width: horizontal space allocated for this branch - avoids overlap with other branches

    vert_gap: gap between levels of hierarchy

    vert_loc: vertical location of root

    xcenter: horizontal location of root
    """
    if not nx.is_tree(graph):
        raise TypeError("cannot use hierarchy_pos on a graph that is not a tree")

    def _hierarchy_pos(
        graph: nx.DiGraph,
        root: str,
        width: float = 1.0,
        vert_gap: float = 0.2,
        vert_loc: float = 0.0,
        x_center: float = 0.5,
        pos: Dict = None,
        parent: str = None,
    ):
        """
        see hierarchy_pos docstring for most arguments

        pos: a dict saying where all nodes go if they have been assigned
        parent: parent of this branch. - only affects it if non-directed

        """

        if pos is None:
            pos = {root: (x_center, vert_loc)}
        else:
            pos[root] = (x_center, vert_loc)
        children = list(graph.neighbors(root))
        if not isinstance(graph, nx.DiGraph) and parent is not None:
            children.remove(parent)
        if len(children) != 0:
            dx = width / len(children)
            next_x = x_center - width / 2 - dx / 2
            for child in children:
                next_x += dx
                pos = _hierarchy_pos(
                    graph,
                    child,
                    width=dx,
                    vert_gap=vert_gap,
                    vert_loc=vert_loc - vert_gap,
                    x_center=next_x,
                    pos=pos,
                    parent=root,
                )
        return pos

    return _hierarchy_pos(graph, root, width, vert_gap, vert_loc, x_center)


def get_label(id_, client=None):
    """ Get asset's name by given asset id """
    asset_info = client.assets.get_asset(id_)
    return asset_info.to_json()["name"]


def make_assets_tree_plot(df: pd.DataFrame, root_id: int = None, max_depth: int = None) -> go.Figure:
    """

    Generates assets plots from Assets dataframe

    Args:
        df:
        root_id:
        max_depth:

    Returns:

    """
    assets_tree = make_assets_tree(df)

    if root_id is None:
        root_id = next(iter(nx.topological_sort(assets_tree)))  # allows back compatibility with nx version 1.11

    assets_tree = nx.dfs_tree(assets_tree, source=root_id, depth_limit=max_depth)
    pos = hierarchy_pos(assets_tree, root=root_id)

    # extract node coordinates and labels
    Xn = [pos[i][0] for i in pos.keys()]
    Yn = [pos[i][1] for i in pos.keys()]
    labels = [get_label(id_) for id_ in pos.keys()]

    # extract edges from tree
    Xe = list()
    Ye = list()
    for e in assets_tree.edges():
        Xe.extend([pos[e[0]][0], pos[e[1]][0], None])
        Ye.extend([pos[e[0]][1], pos[e[1]][1], None])

    # make plotly traces
    trace_nodes = dict(
        type="scatter",
        x=Xn,
        y=Yn,
        mode="markers",
        marker=dict(size=20, color="rgb(0, 0, 204)"),
        text=labels,
        hoverinfo="text",
    )
    trace_edges = dict(
        type="scatter", mode="lines", x=Xe, y=Ye, line=dict(width=1, color="rgb(25,25,25)"), hoverinfo="none"
    )

    # some pretty details
    axis = dict(
        showline=False,  # hide axis line, grid, ticklabels and  title
        zeroline=False,
        showgrid=False,
        showticklabels=False,
        title="",
    )

    layout = go.Layout(autosize=True, showlegend=False, xaxis=axis, yaxis=axis, hovermode="closest")
    fig = go.Figure(data=[trace_edges, trace_nodes], layout=layout)
    return fig


def configure_plotly_browser_state():
    """

    Resolves an issue with plotly in google colab

    Returns:

    """
    from IPython.core.display import display, HTML

    display(
        HTML(
            """
        <script src="/static/components/requirejs/require.js"></script>
        <script>
          requirejs.config({
            paths: {
              base: '/static/base',
              plotly: 'https://cdn.plot.ly/plotly-latest.min.js?noext',
            },
          });
        </script>
        """
        )
    )
