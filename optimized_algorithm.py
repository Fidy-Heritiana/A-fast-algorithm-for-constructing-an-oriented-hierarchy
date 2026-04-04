import pandas as pd
import math as mt
import numpy as np
import time
from scipy.stats import poisson
import networkx as nx
import matplotlib.pyplot as plt

# Fonction pour calculer l'intensité d'implication
debut = time.perf_counter()

def intensite_implication(n_x, n_y, n_xy, n):
    lamb = n_x * (n - n_y) / n
    if n_x > n_y:
        return 0
    else:
        phi = 1 - poisson.cdf(n_xy, lamb)
        return phi


# Fonction pour générer la matrice d'implications x=1 ⇒ y=0
def matrice_implication(fichier_csv):
    #df = pd.read_csv(fichier_csv).astype(int)
    df = pd.read_csv(fichier_csv)
    n = len(df)
    attributs = df.columns
    taille = len(attributs)
    
    matrice = pd.DataFrame(np.zeros((taille, taille)), index=attributs, columns=attributs)

    for i, x in enumerate(attributs):
        for j, y in enumerate(attributs):
            n_x = df[x].sum()
            n_y = df[y].sum()
            n_xy = ((df[x] == 1) & (df[y] == 0)).sum()
            phi = intensite_implication(n_x, n_y, n_xy, n)
            matrice.iloc[i, j] = phi

    return matrice

# 1. Temps pour construire la matrice
mat = matrice_implication("animales_sec1.csv")

def graphe(matrice, alpha):
    """
    Construit et affiche le graphe orienté des implications où
    i → j si matrice.loc[i, j] > alpha
    """
    # Création du graphe orienté
    G = nx.DiGraph()

    # Ajouter les arêtes selon la matrice
    for i in matrice.index:
        for j in matrice.columns:
            if matrice.loc[i, j] > alpha:
                G.add_edge(i, j, weight=matrice.loc[i, j])

    # Mise en page du graphe (layout automatique)
    pos = nx.spring_layout(G, seed=42)  # positionnement des nœuds

    # Tracer les nœuds et les arêtes
    pos = nx.spring_layout(G, seed=42, k=1.5)  # k = facteur de répulsion entre nœuds
    plt.figure(figsize=(14, 12))              # augmente la taille de la figure

    #plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=700)
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True)
    nx.draw_networkx_labels(G, pos, font_size=12, font_family='sans-serif')

    # Ajouter les poids (valeurs de φ) sur les arêtes si tu veux
    edge_labels = {(u, v): f"{d['weight']:.2f}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

    plt.title("Graphe d'implication φ(i → j) > α")
    plt.axis('off')
    plt.show()

    return G  # tu peux utiliser ce graphe pour d'autres traitements

alpha = 0.7
G = graphe(mat, alpha)

def consequent(G):
    """
    À partir d'un graphe orienté G, retourne un dictionnaire des attributs impliqués
    par chaque sommet i (par transitivité).
    """
    resultats = {}
    for i in G.nodes:
        # Noeuds atteignables depuis i (sans inclure i lui-même)
        atteints = nx.descendants(G, i)
        resultats[i] = sorted(atteints)
        resultats[i].append(i)
    return resultats

import networkx as nx

def premisse(G):
    """
    Pour chaque sommet i, retourne les sommets x tels que x → i (transitivement).
    """
    G_transpose = G.reverse(copy=True)  # inverse toutes les arêtes
    resultats = {}
    for i in G.nodes:
        antécédents = nx.descendants(G_transpose, i)
        resultats[i] = sorted(antécédents)
        resultats[i].append(i)
    return resultats
    
#G = graphe(mat, alpha)
def treillis(G):
    conséquents = consequent(G)
    antécédents = premisse(G)
    list_antécédents = list(antécédents.values())
    list_conséquents = list(conséquents.values())
    concatenate= (list_antécédents + list_conséquents)
    for x in G.nodes:
        concatenate.append(x)
    #T = consequent(matrice, alpha)
    #for clas in premisse(matrice, alpha):
        #T.add(clas)
    return concatenate

def tri_topologique(resultats):
    from copy import deepcopy

    E_arcs = []
    resultats = [tuple(sorted(C)) for C in resultats]  # Tuples triés pour uniformiser
    resultats = list(set(resultats))  # Éliminer les doublons
    in_degre = {C: 0 for C in resultats}

    # Construction des arcs selon l'inclusion stricte
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
T = treillis(G)
heriarchi = tri_topologique(T)

def hierarchie_orientee(resultats):
    # Étape 1 : Copier la liste triée
    l = resultats
    retire = []
    for Ci in l:
        for Cj in l:
            if len(Ci)<len(Cj) and set(Ci)&set(Cj)!=set() and set(Ci)&set(Cj)!=set(Ci):
                retire.append(Cj)
    l = [classe for classe in l if classe not in retire]
    return l
#print("nous avons:", len(hierarchie_orientee(heriarchi)), "classes")
for i in hierarchie_orientee(heriarchi):
   print(i)
fin = time.perf_counter()
t = fin - debut
print(t)