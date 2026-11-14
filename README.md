# Constructing oriented hierarchies: Python implementations

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Fidy-Heritiana/A-fast-algorithm-for-constructing-an-oriented-hierarchy/blob/main/demo.ipynb)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Fidy-Heritiana/A-fast-algorithm-for-constructing-an-oriented-hierarchy/main?labpath=demo.ipynb)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24227815.svg)](https://doi.org/10.5281/zenodo.24227815)

Python research code for constructing oriented hierarchies from binary data
in **Statistical Implicative Analysis (SIA)**.

The repository contains a method using a heap and graph traversal, together
with an optimized comparison method. It provides the scripts and example data
needed to inspect their outputs and study their computational behaviour.

## What the scripts do

| File | Purpose |
| --- | --- |
| `new_algorithm.py` | Computes an implication matrix, selects directed pairs with a heap, rejects cycles during graph construction and builds ordered classes. |
| `optimized_algorithm.py` | Builds a thresholded implication graph, computes reachability sets, orders candidate classes by inclusion and filters partially overlapping classes. It also displays the graph. |
| `Data.zip` | Contains `animales_sec1.csv` and 20 simulated datasets, named `simulation_1.csv` through `simulation_20.csv`. |
| `requirements.txt` | Records the Python package versions used for the execution checks. |

## Quick start

The scripts have been checked with **Python 3.12.14**. Python 3.12 is the
reference environment for the instructions below.

### 1. Get the repository

```bash
git clone https://github.com/Fidy-Heritiana/A-fast-algorithm-for-constructing-an-oriented-hierarchy.git
cd A-fast-algorithm-for-constructing-an-oriented-hierarchy
python -m venv .venv
```

Activate the environment with `source .venv/bin/activate` on Linux/macOS or
`.venv\Scripts\Activate.ps1` in Windows PowerShell.

### 2. Install the dependencies and unpack the data

```bash
python -m pip install -r requirements.txt
python -m zipfile -e Data.zip .
```

Run these commands from the repository folder. After extraction,
`animales_sec1.csv` must be alongside the two Python scripts.

### 3. Run the implementations

```bash
python new_algorithm.py
```

The script prints its ordered classes and then its elapsed time in seconds.

```bash
python optimized_algorithm.py
```

This script draws an implication graph, prints its retained classes and then
prints its elapsed time in seconds. When a graph window opens, close it to
allow execution to continue.

## Input data

Both scripts currently read **`animales_sec1.csv`**. The bundled example
contains **41 observations and 31 variables**.

The expected CSV format is:

- one observation per row;
- one variable per column, with a header giving its name;
- numeric binary values, `0` or `1`, in the data cells;
- only the variables to be analysed, without an identifier or text column.

To use another dataset, edit the filename in the call to
`matrice_implication(...)` in the script you want to run. For example, replace
`animales_sec1.csv` with `simulation_1.csv` after extracting `Data.zip`.

## Parameters and comparison conventions

The input filename and the threshold `alpha` are set directly in each script.
The current defaults are:

| Setting | `new_algorithm.py` | `optimized_algorithm.py` |
| --- | --- | --- |
| Input CSV | `animales_sec1.csv` | `animales_sec1.csv` |
| Threshold `alpha` | `0.5` | `0.7` |
| Threshold test | Score at least `alpha` | Score strictly greater than `alpha` |
| Explicit zero-score condition | `n_y == n` | `n_x > n_y` |
| Graph display | No | Yes |

Here, `n` is the number of observations, and `n_x` and `n_y` are the sums of
the two binary columns. The variable called `n_xy` in the scripts counts rows
where `x == 1` and `y == 0`.

For a controlled comparison, specify a common dataset, score convention and
threshold, and document how the resulting classes are compared. The defaults
above describe the current implementations and produce different outputs.

The printed elapsed time includes CSV loading, matrix construction and
console output. In `optimized_algorithm.py`, it also includes graph drawing
and potentially the time spent waiting for the plot window to close. For
performance experiments, time the computational stages separately from
visualisation and printing.

## Variable-name correction

In `optimized_algorithm.py`, singleton classes are stored with
`concatenate.append([x])`. Keeping each name inside a one-element list
preserves labels such as `column_12` when the subsequent sorting step converts
classes into tuples. The earlier `concatenate.append(x)` representation split
such labels into individual characters.

## Execution checks

The two scripts were executed with the bundled `animales_sec1.csv` and their
respective default thresholds. The graph was rendered with Matplotlib's
non-interactive `Agg` backend during these checks.

| Script | Returned classes | All output labels belong to the input columns |
| --- | ---: | --- |
| `new_algorithm.py` | 31 | Yes |
| `optimized_algorithm.py`, with the variable-name correction | 45 | Yes |

The variable-name check found seven unexpected labels in the earlier
comparison script and none after the correction. These checks establish
successful execution on this example and correct preservation of its variable
names. Algorithmic correctness and performance rankings require their own
mathematical and experimental analysis.

When reporting an experiment, record the commit, dataset, threshold, score
conventions, Python environment and timing procedure.

## Citation

If you use this software or its data, please cite the archived release:

> Andrianarivony, Fidy Heritiana. (2026). *Constructing oriented hierarchies:
> Python implementations* (Version 1.0.0) [Computer software]. Zenodo.
> https://doi.org/10.5281/zenodo.24227815

This DOI identifies version `v1.0.0`. Citation metadata are also provided in
[`CITATION.cff`](CITATION.cff). For reproducibility, record the version or commit
used in your experiments.

## License

This project is distributed under the [MIT License](LICENSE).
