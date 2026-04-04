import itertools
import math
from scipy.stats import poisson
import pandas as pd
import math as mt
import numpy as np
import heapq
import time
debut = time.perf_counter()
def intensite_implication(n_x, n_y, n_xy, n):
    lamb = n_x * (n - n_y) / n
    if n_y == n:
        return 0
    else:
        phi = 1 - poisson.cdf(n_xy, lamb)
        return phi

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

def tri_matrice(M):
    n = len(M)

    H = []

    ligne_supprimee = [False] * n
    colonne_supprimee = [False] * n

    lignes = M.index.tolist()
    colonnes = M.columns.tolist()

    # Prétraitement symétrique + heap
    for i in range(n):
        for j in range(i+1, n):
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

    # Sélection gloutonne
    while H and len(C) < n:
        neg_v, i, j = heapq.heappop(H)

        if ligne_supprimee[i] or colonne_supprimee[j]:
            continue

        # Conversion en lettres
        C.append((lignes[i], colonnes[j]))

        ligne_supprimee[i] = True
        colonne_supprimee[j] = True

    return C
    
mat = matrice_implication('animales_sec1.csv')

from collections import defaultdict

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

    G = defaultdict(list)

    Classes_list = []   # ordre conservé
    Classes_set  = set() # pour éviter doublons

    for (u, v) in L:

        # Rejet si cycle
        if existe_chemin(G, v, u):
            continue

        # Ajout arête
        G[u].append(v)

        # Classe d’ordre 2
        if (u, v) not in Classes_set:
            Classes_list.append((u, v))
            Classes_set.add((u, v))

        nouvelles = []

        # C finissant par u
        for C in Classes_list:
            if C[-1] == u:
                Cn = C + (v,)
                if Cn not in Classes_set:
                    nouvelles.append(Cn)
                    Classes_set.add(Cn)

        # C commençant par v
        for C in Classes_list:
            if C[0] == v:
                Cn = (u,) + C
                if Cn not in Classes_set:
                    nouvelles.append(Cn)
                    Classes_set.add(Cn)

        # Ajout après balayage
        Classes_list.extend(nouvelles)

    return Classes_list
alpha = 0.5
T=tri_matrice(mat)
resultat = construire_classes(T)
for cls in resultat:
    print(cls)
fin = time.perf_counter()
t = fin - debut
print(t)