"""
Constructing oriented hierarchies in statistical implicative analysis (SIA).

This module gathers, as functions, the code of the two scripts of the repository:

* new_algorithm.py        -> new_algorithm        (heap and graph traversal)
* optimized_algorithm.py  -> optimized_algorithm  (lattice and topological sort)

The logic is the one of the scripts, which remain the reference. Two score
conventions are used by the scripts for the implication intensity:

* convention "new"       : the score is 0 when n_y == n      (new_algorithm.py)
* convention "optimized" : the score is 0 when n_x > n_y     (optimized_algorithm.py)

where n is the number of observations and n_x, n_y are the sums of two columns.
Thresholds also differ: new_algorithm keeps scores >= alpha, optimized_algorithm
keeps scores > alpha.
"""

import heapq
import time
from collections import defaultdict

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import poisson


# ----------------------------------------------------------------------
# Implication matrix
# ----------------------------------------------------------------------

def intensite_implication(n_x, n_y, n_xy, n, convention="optimized"):
    """Implication intensity of x => y (Poisson model)."""
    lamb = n_x * (n - n_y) / n
    if convention == "new":
        if n_y == n:
            return 0
    else:
        if n_x > n_y:
            return 0
    return 1 - poisson.cdf(n_xy, lamb)


def matrice_implication(donnees, convention="optimized"):
    """
    Implication matrix, computed as in the scripts (one pair at a time).
    `donnees` is the path of a CSV file or a DataFrame of 0/1 columns.
    """
    df = pd.read_csv(donnees) if isinstance(donnees, str) else donnees
    n = len(df)
    attributs = df.columns
    taille = len(attributs)

    matrice = pd.DataFrame(np.zeros((taille, taille)), index=attributs, columns=attributs)

    for i, x in enumerate(attributs):
        for j, y in enumerate(attributs):
            n_x = df[x].sum()
            n_y = df[y].sum()
            n_xy = ((df[x] == 1) & (df[y] == 0)).sum()
            matrice.iloc[i, j] = intensite_implication(n_x, n_y, n_xy, n, convention)
    return matrice


def matrice_implication_rapide(donnees, convention="optimized"):
    """
    Same matrix as matrice_implication for a table of 0/1 values, computed for all
    pairs at once. It is much faster on tables with many columns.
    """
    df = pd.read_csv(donnees) if isinstance(donnees, str) else donnees
    n = len(df)
    X = df.values
    n_x = X.sum(axis=0)
    n_xy = (X == 1).T.astype(np.int64) @ (X == 0).astype(np.int64)  # x == 1 and y == 0
    lamb = n_x[:, None] * (n - n_x[None, :]) / n
    phi = 1 - poisson.cdf(n_xy, lamb)
    if convention == "new":
        phi = np.where((n_x[None, :] == n), 0, phi)      # n_y == n
    else:
        phi = np.where(n_x[:, None] > n_x[None, :], 0, phi)  # n_x > n_y
    return pd.DataFrame(phi.astype(float), index=df.columns, columns=df.columns)


# ----------------------------------------------------------------------
# new_algorithm.py : heap and graph traversal
# ----------------------------------------------------------------------

def tri_matrice(M, alpha):
    """Select, with a heap, one directed pair per row and per column."""
    n = len(M)

    H = []

    ligne_supprimee = [False] * n
    colonne_supprimee = [False] * n

    lignes = M.index.tolist()
    colonnes = M.columns.tolist()

    for i in range(n):
        for j in range(i + 1, n):
            if M.iloc[i, j] >= M.iloc[j, i]:
                v = M.iloc[i, j]
                ii, jj = i, j
            else:
                v = M.iloc[j, i]
                ii, jj = j, i

            if v < alpha:
                continue

            heapq.heappush(H, (-v, ii, jj))

    C = []

    while H and len(C) < n:
        neg_v, i, j = heapq.heappop(H)

        if ligne_supprimee[i] or colonne_supprimee[j]:
            continue

        C.append((lignes[i], colonnes[j]))

        ligne_supprimee[i] = True
        colonne_supprimee[j] = True

    return C


def existe_chemin(G, start, target):
    stack = [start]
    visited = set()

    while stack:
        x = stack.pop()
        if x == target:
            return True
        if x in visited:
            continue
        visited.add(x)
        for y in G[x]:
            stack.append(y)

    return False


def construire_classes(L):
    """Build the ordered classes from the selected pairs, rejecting cycles."""
    G = defaultdict(list)

    Classes_list = []   # order kept
    Classes_set = set()  # to avoid duplicates

    for (u, v) in L:

        if existe_chemin(G, v, u):
            continue

        G[u].append(v)

        if (u, v) not in Classes_set:
            Classes_list.append((u, v))
            Classes_set.add((u, v))

        nouvelles = []

        for C in Classes_list:
            if C[-1] == u:
                Cn = C + (v,)
                if Cn not in Classes_set:
                    nouvelles.append(Cn)
                    Classes_set.add(Cn)

        for C in Classes_list:
            if C[0] == v:
                Cn = (u,) + C
                if Cn not in Classes_set:
                    nouvelles.append(Cn)
                    Classes_set.add(Cn)

        Classes_list.extend(nouvelles)

    return Classes_list


def new_algorithm(mat, alpha=0.5):
    """Heap and graph traversal. Returns the list of ordered classes (tuples)."""
    return construire_classes(tri_matrice(mat, alpha))


# ----------------------------------------------------------------------
# optimized_algorithm.py : lattice and topological sort
# ----------------------------------------------------------------------

def graphe_implication(matrice, alpha):
    """Directed graph of implications: i -> j if matrice.loc[i, j] > alpha."""
    G = nx.DiGraph()
    for i in matrice.index:
        for j in matrice.columns:
            if matrice.loc[i, j] > alpha:
                G.add_edge(i, j, weight=matrice.loc[i, j])
    return G


def dessiner_graphe(G, ax=None, taille_noeuds=700, taille_police=12, poids=True):
    """Draw the implication graph (same layout as in optimized_algorithm.py)."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42, k=1.5)
    nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=taille_noeuds, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=taille_police, font_family="sans-serif", ax=ax)
    if poids:
        edge_labels = {(u, v): f"{d['weight']:.2f}" for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10, ax=ax)
    ax.set_title("Implication graph: phi(i -> j) > alpha")
    ax.axis("off")
    return ax


def consequent(G):
    resultats = {}
    for i in G.nodes:
        atteints = nx.descendants(G, i)
        resultats[i] = sorted(atteints)
        resultats[i].append(i)
    return resultats


def premisse(G):
    G_transpose = G.reverse(copy=True)
    resultats = {}
    for i in G.nodes:
        antecedents = nx.descendants(G_transpose, i)
        resultats[i] = sorted(antecedents)
        resultats[i].append(i)
    return resultats


def treillis(G):
    consequents = consequent(G)
    antecedents = premisse(G)
    concatenate = list(antecedents.values()) + list(consequents.values())
    for x in G.nodes:
        concatenate.append([x])
    return concatenate


def tri_topologique(resultats):
    E_arcs = []
    resultats = [tuple(sorted(C)) for C in resultats]
    resultats = list(set(resultats))
    in_degre = {C: 0 for C in resultats}

    for Ci in resultats:
        for Cj in resultats:
            if Ci != Cj and set(Ci).issubset(set(Cj)) and len(Ci) < len(Cj):
                E_arcs.append((Ci, Cj))
                in_degre[Cj] += 1

    S = sorted([C for C in resultats if in_degre[C] == 0], key=len)
    L = []

    while S:
        Ci = S.pop(0)
        L.append(Ci)
        for arc in E_arcs[:]:
            if arc[0] == Ci:
                Cj = arc[1]
                E_arcs.remove(arc)
                in_degre[Cj] -= 1
                if in_degre[Cj] == 0:
                    S.append(Cj)
        S = sorted(S, key=len)

    return [list(C) for C in L]


def hierarchie_orientee(resultats):
    l = resultats
    retire = []
    for Ci in l:
        for Cj in l:
            if len(Ci) < len(Cj) and set(Ci) & set(Cj) != set() and set(Ci) & set(Cj) != set(Ci):
                retire.append(Cj)
    return [classe for classe in l if classe not in retire]


def optimized_algorithm(mat, alpha=0.7):
    """Lattice and topological sort. Returns (graph G, list of classes)."""
    G = graphe_implication(mat, alpha)
    return G, hierarchie_orientee(tri_topologique(treillis(G)))


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def chronometre(f, *args, **kwargs):
    """Return (result, elapsed seconds)."""
    t0 = time.perf_counter()
    res = f(*args, **kwargs)
    return res, time.perf_counter() - t0


def classes_comme_ensembles(classes):
    """Classes with at least two variables, as sets of variables (order ignored)."""
    return {frozenset(c) for c in classes if len(c) >= 2}
