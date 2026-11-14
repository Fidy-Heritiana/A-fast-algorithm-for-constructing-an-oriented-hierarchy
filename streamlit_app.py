import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

import hierarchy_algorithms as ha

DOSSIER = Path(__file__).resolve().parent
REPO_URL = "https://github.com/Fidy-Heritiana/A-fast-algorithm-for-constructing-an-oriented-hierarchy"
MAX_VARIABLES = 200
MAX_LIGNES = 5000
ALPHAS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]

OWN = "Each algorithm with its own convention (as in the scripts)"
COMMON_NEW = "Same for both: convention of new_algorithm.py (score 0 when n_y = n)"
COMMON_OPT = "Same for both: convention of optimized_algorithm.py (score 0 when n_x > n_y)"

st.set_page_config(page_title="Oriented hierarchies", page_icon="🌳", layout="wide")

st.title("Constructing oriented hierarchies")
st.markdown(
    "Two Python implementations for statistical implicative analysis: **new_algorithm** "
    "(heap and graph traversal) and **optimized_algorithm** (lattice and topological sort). "
    f"Interactive companion to the [GitHub repository]({REPO_URL})."
)

# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------


def noms_donnees():
    """CSV files of the repository: inside Data.zip, or next to the app."""
    archive = DOSSIER / "Data.zip"
    if archive.exists():
        with zipfile.ZipFile(archive) as z:
            noms = [n for n in z.namelist() if n.lower().endswith(".csv")]
    else:
        noms = [p.name for p in DOSSIER.glob("*.csv")]

    def cle(n):
        if n.startswith("simulation_"):
            return (1, int(n.split("_")[1].split(".")[0]))
        return (0, 0)

    return sorted(noms, key=cle)


@st.cache_data(show_spinner=False)
def charger(nom):
    archive = DOSSIER / "Data.zip"
    if archive.exists():
        with zipfile.ZipFile(archive) as z:
            with z.open(nom) as f:
                return pd.read_csv(f)
    return pd.read_csv(DOSSIER / nom)


def valider_csv(df):
    """Return an error message, or None if the table can be used."""
    if df.shape[1] < 2 or df.shape[1] > MAX_VARIABLES:
        return f"The table must have between 2 and {MAX_VARIABLES} columns (it has {df.shape[1]})."
    if df.shape[0] < 2 or df.shape[0] > MAX_LIGNES:
        return f"The table must have between 2 and {MAX_LIGNES} rows (it has {df.shape[0]})."
    if df.isnull().any().any():
        return "The table contains missing values."
    if not all(pd.api.types.is_numeric_dtype(t) or pd.api.types.is_bool_dtype(t) for t in df.dtypes):
        return "All columns must be numeric (0 or 1)."
    if not set(np.unique(df.values)).issubset({0, 1}):
        return "All values must be 0 or 1."
    if len(set(df.columns)) != df.shape[1]:
        return "Column names must be distinct."
    return None


def etiquette(nom, df):
    return f"{nom} ({df.shape[0]} observations, {df.shape[1]} variables)"


# ----------------------------------------------------------------------
# Computations (cached)
# ----------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def matrice(df, convention):
    return ha.matrice_implication_rapide(df, convention)


@st.cache_data(show_spinner=False)
def calcul_new(df, convention, alpha):
    mat = matrice(df, convention)
    classes, t = ha.chronometre(ha.new_algorithm, mat, alpha)
    return classes, t


@st.cache_data(show_spinner=False)
def calcul_opt(df, convention, alpha):
    mat = matrice(df, convention)
    (G, classes), t = ha.chronometre(ha.optimized_algorithm, mat, alpha)
    return G, [tuple(c) for c in classes], t


@st.cache_data(show_spinner=False)
def balayage_alpha(df, conv_new, conv_opt):
    lignes = []
    mn, mo = matrice(df, conv_new), matrice(df, conv_opt)
    for a in ALPHAS:
        cn = ha.new_algorithm(mn, a)
        _, co = ha.optimized_algorithm(mo, a)
        lignes.append(
            {
                "alpha": a,
                "new_algorithm": len([c for c in cn if len(c) >= 2]),
                "optimized_algorithm": len([c for c in co if len(c) >= 2]),
            }
        )
    return pd.DataFrame(lignes)


@st.cache_data(show_spinner=False)
def benchmark(n_max, alpha_new, alpha_opt):
    lignes = []
    for k in range(1, n_max + 1):
        d = charger(f"simulation_{k}.csv")
        mn, mo = matrice(d, "new"), matrice(d, "optimized")
        _, tn = ha.chronometre(ha.new_algorithm, mn, alpha_new)
        _, to = ha.chronometre(ha.optimized_algorithm, mo, alpha_opt)
        lignes.append({"variables": d.shape[1], "new_algorithm (s)": tn, "optimized_algorithm (s)": to})
    return pd.DataFrame(lignes)


def tableau(classes, nom, fleche):
    lignes = [
        {"algorithm": nom, "size": len(c), "class": fleche.join(str(v) for v in c)}
        for c in classes
        if len(c) >= 2
    ]
    return pd.DataFrame(lignes, columns=["algorithm", "size", "class"])


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------

st.sidebar.header("Data")
source = st.sidebar.radio("Dataset", ["Bundled dataset", "My own CSV file"])

if source == "Bundled dataset":
    noms = noms_donnees()
    if not noms:
        st.error("No data file found next to the app.")
        st.stop()
    choix = st.sidebar.selectbox("File", noms, index=0)
    df = charger(choix)
    nom_donnees = etiquette(choix, df)
else:
    fichier = st.sidebar.file_uploader("CSV file with 0/1 columns", type="csv")
    st.sidebar.caption(
        f"One row per observation, one column per variable with a header, values 0 or 1. "
        f"At most {MAX_VARIABLES} variables and {MAX_LIGNES} rows."
    )
    if fichier is None:
        st.info("Upload a CSV file in the sidebar, or switch to a bundled dataset.")
        st.stop()
    try:
        df = pd.read_csv(fichier)
    except Exception:
        st.error("This file could not be read as a CSV table.")
        st.stop()
    erreur = valider_csv(df)
    if erreur:
        st.error(erreur)
        st.stop()
    nom_donnees = etiquette(fichier.name, df)

st.sidebar.header("Score convention")
convention = st.sidebar.radio(
    "Implication intensity", [OWN, COMMON_NEW, COMMON_OPT], label_visibility="collapsed"
)
if convention == OWN:
    conv_new, conv_opt = "new", "optimized"
elif convention == COMMON_NEW:
    conv_new = conv_opt = "new"
else:
    conv_new = conv_opt = "optimized"

st.sidebar.header("Thresholds")
meme_seuil = st.sidebar.checkbox("Use the same threshold for both", value=False)
if meme_seuil:
    alpha_new = alpha_opt = st.sidebar.slider("alpha", 0.50, 0.99, 0.70, 0.01)
else:
    alpha_new = st.sidebar.slider("alpha, new_algorithm (score >= alpha)", 0.50, 0.99, 0.50, 0.01)
    alpha_opt = st.sidebar.slider("alpha, optimized_algorithm (score > alpha)", 0.50, 0.99, 0.70, 0.01)

# ----------------------------------------------------------------------
# Run
# ----------------------------------------------------------------------

with st.spinner("Computing..."):
    classes_new, t_new = calcul_new(df, conv_new, alpha_new)
    G, classes_opt, t_opt = calcul_opt(df, conv_opt, alpha_opt)

tab_res, tab_graph, tab_alpha, tab_time = st.tabs(
    ["Results", "Graph and matrix", "Sensitivity to alpha", "Runtime"]
)

with tab_res:
    st.subheader(nom_donnees)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("new_algorithm: classes", len(classes_new))
    c2.metric("optimized_algorithm: classes", len(classes_opt))
    ens_new = ha.classes_comme_ensembles(classes_new)
    ens_opt = ha.classes_comme_ensembles(classes_opt)
    union = ens_new | ens_opt
    c3.metric("Same sets of variables", len(ens_new & ens_opt))
    c4.metric("Overlap (Jaccard)", f"{len(ens_new & ens_opt) / len(union):.2f}" if union else "-")

    st.write(
        f"Running time of the algorithms alone (without the implication matrix): "
        f"**new_algorithm {t_new:.3f} s**, **optimized_algorithm {t_opt:.3f} s**."
    )
    st.caption(
        "Classes returned: new_algorithm returns ordered classes of at least two variables; "
        "optimized_algorithm also returns the classes made of a single variable. "
        "Overlap compares the classes with at least two variables as sets of variables (order ignored)."
    )

    tn = tableau(classes_new, "new_algorithm", " → ")
    to = tableau(classes_opt, "optimized_algorithm", ", ")
    left, right = st.columns(2)
    with left:
        st.markdown(f"**new_algorithm**: {len(tn)} classes with at least 2 variables")
        st.dataframe(tn[["size", "class"]], hide_index=True)
    with right:
        st.markdown(f"**optimized_algorithm**: {len(to)} classes with at least 2 variables")
        st.dataframe(to[["size", "class"]], hide_index=True)

    st.download_button(
        "Download the classes (CSV)",
        pd.concat([tn, to]).to_csv(index=False).encode("utf-8"),
        file_name="classes.csv",
        mime="text/csv",
    )
    if convention == OWN:
        st.caption(
            "With each algorithm's own convention and threshold the two outputs are not meant to be "
            "identical. For a controlled comparison choose a common convention and a common threshold "
            "in the sidebar."
        )

with tab_graph:
    left, right = st.columns(2)
    with left:
        st.markdown("**Implication matrix** (convention of optimized_algorithm)")
        mat_opt = matrice(df, conv_opt)
        fig, ax = plt.subplots(figsize=(5.5, 4.8))
        im = ax.imshow(mat_opt.values, cmap="viridis", vmin=0, vmax=1)
        if mat_opt.shape[0] <= 35:
            ax.set_xticks(range(mat_opt.shape[0]), mat_opt.columns, rotation=90, fontsize=6)
            ax.set_yticks(range(mat_opt.shape[0]), mat_opt.index, fontsize=6)
        fig.colorbar(im, ax=ax, label="implication intensity")
        st.pyplot(fig)
        plt.close(fig)
    with right:
        st.markdown(f"**Implication graph** (arrow i → j when score > {alpha_opt})")
        n_noeuds = G.number_of_nodes()
        if n_noeuds == 0:
            st.info("No arrow for this threshold: try a smaller alpha.")
        elif n_noeuds > 40:
            st.info(f"The graph has {n_noeuds} vertices: too many to draw. Choose a smaller dataset.")
        else:
            fig, ax = plt.subplots(figsize=(6.5, 5.5))
            ha.dessiner_graphe(
                G,
                ax=ax,
                taille_noeuds=700 if n_noeuds <= 20 else 350,
                taille_police=10 if n_noeuds <= 20 else 7,
                poids=G.number_of_edges() <= 30,
            )
            st.pyplot(fig)
            plt.close(fig)
        st.caption(f"{n_noeuds} vertices, {G.number_of_edges()} arrows.")

with tab_alpha:
    st.write(
        "Number of classes with at least two variables, for thresholds from 0.50 to 0.95, "
        "with the score convention chosen in the sidebar."
    )
    cle_balayage = (nom_donnees, conv_new, conv_opt)
    if df.shape[1] > 60:
        st.caption("This takes a few seconds on large datasets.")
        if st.button("Run the sweep"):
            st.session_state["balayage"] = cle_balayage
        afficher_balayage = st.session_state.get("balayage") == cle_balayage
    else:
        afficher_balayage = True

    if afficher_balayage:
        with st.spinner("Running..."):
            sweep = balayage_alpha(df, conv_new, conv_opt)
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(sweep["alpha"], sweep["new_algorithm"], marker="o", label="new_algorithm")
        ax.plot(sweep["alpha"], sweep["optimized_algorithm"], marker="s", label="optimized_algorithm")
        ax.set_xlabel("alpha")
        ax.set_ylabel("classes with at least 2 variables")
        ax.legend()
        ax.grid(alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)
        st.dataframe(sweep, hide_index=True)

with tab_time:
    st.write(
        "Running time of the algorithms alone (the implication matrix is not included) on the "
        "simulated datasets `simulation_1.csv` to `simulation_k.csv`, each algorithm with its own "
        "convention and the thresholds chosen in the sidebar."
    )
    if (DOSSIER / "Data.zip").exists() or (DOSSIER / "simulation_20.csv").exists():
        n_max = st.slider("Largest dataset k", 3, 20, 10)
        loglog = st.checkbox("Log-log scale", value=True)
        if st.button("Run the benchmark"):
            st.session_state["bench"] = (n_max, alpha_new, alpha_opt)
        if "bench" in st.session_state:
            nm, an, ao = st.session_state["bench"]
            with st.spinner("Running..."):
                temps = benchmark(nm, an, ao)
            fig, ax = plt.subplots(figsize=(6.5, 4))
            ax.plot(temps["variables"], temps["new_algorithm (s)"], marker="o", label="new_algorithm")
            ax.plot(temps["variables"], temps["optimized_algorithm (s)"], marker="s", label="optimized_algorithm")
            if loglog:
                ax.set_xscale("log")
                ax.set_yscale("log")
            ax.set_xlabel("number of variables")
            ax.set_ylabel("time (s)")
            ax.legend()
            ax.grid(alpha=0.3)
            st.pyplot(fig)
            plt.close(fig)
            if len(temps) >= 4:
                x = np.log(temps["variables"].values[2:])
                pentes = {
                    c: np.polyfit(x, np.log(np.maximum(temps[c].values[2:], 1e-9)), 1)[0]
                    for c in ("new_algorithm (s)", "optimized_algorithm (s)")
                }
                st.write(
                    "Fitted exponent k in T(n) ~ n^k (log-log fit, datasets from the third one): "
                    f"new_algorithm k = {pentes['new_algorithm (s)']:.2f}, "
                    f"optimized_algorithm k = {pentes['optimized_algorithm (s)']:.2f}."
                )
            st.dataframe(temps.round(4), hide_index=True)
    else:
        st.info("The simulated datasets are not available next to the app.")

st.divider()
st.caption(f"Source code and data: {REPO_URL}")
