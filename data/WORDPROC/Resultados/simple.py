# -*- coding: utf-8 -*-

# ============================================================
# Simplified Decision Space vs. Student MoSCoW Comparison
# ============================================================
#
# This script creates a publication-oriented figure comparing:
# 1. Structural requirement inclusion frequency by lens family.
# 2. Student MUST priority from MoSCoW.
# 3. Divergence between structural relevance and perceived human priority.
#
# Output files:
#   - requirement_structural_vs_student_priority_simplified.png
#   - requirement_structural_vs_student_priority_simplified.jpg
#
# Both files are saved in the same folder where this script is located.
# ============================================================

import os
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm


# ------------------------------------------------------------
# 0. PATH SETUP
# ------------------------------------------------------------

try:
    SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    SCRIPT_DIR = Path.cwd()

print("Current working directory:")
print(os.getcwd())

print("Script directory:")
print(SCRIPT_DIR)


# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------

file_profiles = {
    "Framed group": "framed.csv",
    "Domain-specific": "domain.csv",
    "Efficiency-Productivity-Squandering": "efici-product-squan.csv",
    "HDBSCAN all values": "hdbscan-todo.csv",
    "HDBSCAN objective": "hdbscan-efsatimsmall2.csv",
    "K-Medoids g0 allvalues": "kmedio-3-0todo.csv",
    "K-Medoids g2 allvalues": "kmedio-3-2todo.csv",
    "K-Medoids 2-0 objective": "kmedio-2-0effsattime.csv",
    "TOPSIS": "topsis.csv",
    "Weighted sum": "weight.csv"
}

mapping_file = SCRIPT_DIR / "requirements_mapping_50_to_42.csv"
moscow_file = SCRIPT_DIR / "moscow_students.csv"

target_requirements = [f"req_{i}" for i in range(1, 43)]

# Sorting options:
#   "original"   -> keeps the reduced 42-requirement order.
#   "delta"      -> sorts by absolute divergence between structural mean and student MUST.
#   "structural" -> sorts by average structural inclusion.
SORT_MODE = "original"

# If you want a smaller paper figure, set TOP_N = 25 or 20.
# If None, all 42 reduced requirements are shown.


TOP_N = None


#TOP_N = 20


# ------------------------------------------------------------
# 2. LOAD REQUIREMENT MAPPING
# ------------------------------------------------------------

req_name_mapping = {f"req_{i}": f"Requirement {i}" for i in range(1, 43)}
df_map = None

if mapping_file.exists():
    df_map = pd.read_csv(mapping_file)

    if {"mapped_req_42", "reduced_name"}.issubset(df_map.columns):
        df_map_unique = (
            df_map
            .drop_duplicates(subset=["mapped_req_42"])
            .sort_values("mapped_req_42")
        )

        req_name_mapping = {
            f"req_{int(row['mapped_req_42'])}": row["reduced_name"]
            for _, row in df_map_unique.iterrows()
        }

        print("Requirement mapping loaded correctly.")
    else:
        print(f"Warning: {mapping_file.name} does not contain 'mapped_req_42' and 'reduced_name'.")
        print("Generic requirement labels will be used.")
else:
    print(f"Warning: {mapping_file.name} not found.")
    print("Generic requirement labels will be used.")


# ------------------------------------------------------------
# 3. COMPUTE REQUIREMENT FREQUENCY BY STRATEGY
# ------------------------------------------------------------

profile_frequencies = {}

print("\nComputing requirement inclusion frequencies by strategy...")

for profile_name, file_name in file_profiles.items():
    file_path = SCRIPT_DIR / file_name

    if not file_path.exists():
        print(f"Warning: missing profile file: {file_name}")
        continue

    df_temp = pd.read_csv(file_path)
    valid_reqs = [col for col in target_requirements if col in df_temp.columns]

    if not valid_reqs:
        print(f"Warning: no valid requirement columns found in {file_name}")
        continue

    frequency_series = df_temp[valid_reqs].mean() * 100
    frequency_series = frequency_series.reindex(target_requirements)
    profile_frequencies[profile_name] = frequency_series

df_strategy = pd.DataFrame(profile_frequencies)
df_strategy = df_strategy.reindex(target_requirements)

if df_strategy.empty:
    raise ValueError(
        "No strategy profiles could be loaded. "
        "Check that the CSV files are in the same folder as this script."
    )

print("Strategy-level decision-space matrix created.")
print(f"Loaded strategy columns: {list(df_strategy.columns)}")


# ------------------------------------------------------------
# 4. AGGREGATE STRATEGIES INTO LENS FAMILIES
# ------------------------------------------------------------

def mean_existing_columns(df, cols):
    existing = [c for c in cols if c in df.columns]
    if not existing:
        return pd.Series(np.nan, index=df.index)
    return df[existing].mean(axis=1)


df_family = pd.DataFrame(index=df_strategy.index)

df_family["Framed"] = mean_existing_columns(
    df_strategy,
    ["Framed group"]
)

df_family["Domain"] = mean_existing_columns(
    df_strategy,
    ["Domain-specific"]
)

df_family["Efficiency"] = mean_existing_columns(
    df_strategy,
    ["Efficiency-Productivity-Squandering"]
)

df_family["Diversity"] = mean_existing_columns(
    df_strategy,
    [
        "HDBSCAN all values",
        "HDBSCAN objective",
        "K-Medoids g0 allvalues",
        "K-Medoids g2 allvalues",
        "K-Medoids 2-0 objective"
    ]
)

df_family["Preference"] = mean_existing_columns(
    df_strategy,
    ["TOPSIS", "Weighted sum"]
)

df_family["Structural mean"] = df_family[
    ["Framed", "Domain", "Efficiency", "Diversity", "Preference"]
].mean(axis=1)

print("Lens-family aggregation created.")


# ------------------------------------------------------------
# 5. LOAD STUDENT MOSCOW PRIORITIZATION
# ------------------------------------------------------------

def detect_merge_column(df_mapping, df_moscow):
    candidate_pairs = [
        ("original_id", "original_id"),
        ("req_50", "original_id"),
        ("source_id", "original_id"),
        ("requirement_id_50", "original_id"),
        ("name_en", "name_en"),
        ("name_es", "name_es")
    ]

    for left_col, right_col in candidate_pairs:
        if left_col in df_mapping.columns and right_col in df_moscow.columns:
            return left_col, right_col

    return None, None


if not moscow_file.exists():
    raise FileNotFoundError(
        f"{moscow_file.name} not found in {SCRIPT_DIR}. "
        "Put moscow_students.csv in the same folder as this script."
    )

df_moscow = pd.read_csv(moscow_file)

if "total_m" not in df_moscow.columns:
    raise ValueError(f"{moscow_file.name} must contain a 'total_m' column.")

student_cols = [c for c in df_moscow.columns if c.startswith("al")]
n_students = len(student_cols)

if n_students == 0:
    raise ValueError("No student columns found. Expected columns such as al1, al2, ...")

df_moscow["must_pct"] = (df_moscow["total_m"] / n_students) * 100

if df_map is None or "mapped_req_42" not in df_map.columns:
    raise ValueError(
        "A valid mapping file is required to project MoSCoW data "
        "into the reduced 42-requirement space."
    )

left_col, right_col = detect_merge_column(df_map, df_moscow)

if left_col is None:
    raise ValueError(
        "No compatible merge column found between mapping and MoSCoW files. "
        "Check columns such as original_id, req_50, source_id, requirement_id_50, name_en, or name_es."
    )

df_moscow_merge = df_moscow.merge(
    df_map,
    left_on=right_col,
    right_on=left_col,
    how="left"
)

df_moscow_merge = df_moscow_merge.dropna(subset=["mapped_req_42"]).copy()
df_moscow_merge["mapped_req_42"] = df_moscow_merge["mapped_req_42"].astype(int)
df_moscow_merge["req_id_42"] = df_moscow_merge["mapped_req_42"].apply(lambda x: f"req_{x}")

# If several original requirements map into one reduced requirement,
# average the MUST percentage to keep a 0-100 scale.
df_must_42 = (
    df_moscow_merge
    .groupby("req_id_42", as_index=False)["must_pct"]
    .mean()
    .set_index("req_id_42")
    .rename(columns={"must_pct": "Student MUST"})
)

df_must_42 = df_must_42.reindex(df_family.index)

print("Student MoSCoW MUST percentages loaded and mapped to the 42-requirement space.")


# ------------------------------------------------------------
# 6. BUILD COMPARISON MATRIX
# ------------------------------------------------------------

df_compare = df_family.copy()
df_compare["Student MUST"] = df_must_42["Student MUST"]
df_compare["Delta"] = df_compare["Structural mean"] - df_compare["Student MUST"]

df_compare["Requirement label"] = [
    req_name_mapping.get(req, req) for req in df_compare.index
]

# Sorting
if SORT_MODE == "delta":
    df_compare = df_compare.reindex(
        df_compare["Delta"].abs().sort_values(ascending=False).index
    )
elif SORT_MODE == "structural":
    df_compare = df_compare.sort_values("Structural mean", ascending=False)
elif SORT_MODE == "original":
    df_compare = df_compare.reindex(target_requirements)
else:
    raise ValueError("SORT_MODE must be one of: original, delta, structural.")

if TOP_N is not None:
    df_compare = df_compare.head(TOP_N)

summary_file = SCRIPT_DIR / "requirement_structural_vs_student_priority_summary.csv"
df_compare.to_csv(summary_file, encoding="utf-8-sig")

print("\nSummary exported:")
print(summary_file)


# ------------------------------------------------------------
# 7. PLOT WITHOUT SEABORN
# ------------------------------------------------------------

family_cols = ["Framed", "Domain", "Efficiency", "Diversity", "Preference"]

family_data = df_compare[family_cols].to_numpy(dtype=float)
student_data = df_compare[["Student MUST"]].to_numpy(dtype=float)
delta_data = df_compare[["Delta"]].to_numpy(dtype=float)

row_labels = df_compare["Requirement label"].tolist()

n_rows = len(df_compare)
fig_height = max(8, 0.32 * n_rows)

fig, axes = plt.subplots(
    1,
    3,
    figsize=(16, fig_height),
    gridspec_kw={"width_ratios": [4.2, 1.05, 1.15]}
)

# ------------------------------------------------------------
# Panel A: Structural inclusion by lens family
# ------------------------------------------------------------

im0 = axes[0].imshow(
    family_data,
    aspect="auto",
    cmap="YlGnBu",
    vmin=0,
    vmax=100
)

axes[0].set_title(
    "A. Structural inclusion by lens family",
    fontsize=13,
    fontweight="bold",
    pad=12
)

axes[0].set_xticks(np.arange(len(family_cols)))
axes[0].set_xticklabels(family_cols, rotation=35, ha="right", fontsize=10)
axes[0].set_yticks(np.arange(n_rows))
axes[0].set_yticklabels(row_labels, fontsize=9)
axes[0].set_ylabel("Requirement", fontsize=11)
axes[0].set_xlabel("Post-optimization lens family", fontsize=11)

cbar0 = fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.02)
cbar0.set_label("Inclusion frequency (%)")

axes[0].set_xticks(np.arange(-0.5, len(family_cols), 1), minor=True)
axes[0].set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
axes[0].grid(which="minor", color="white", linestyle="-", linewidth=0.6)
axes[0].tick_params(which="minor", bottom=False, left=False)


# ------------------------------------------------------------
# Panel B: Student MUST
# ------------------------------------------------------------

im1 = axes[1].imshow(
    student_data,
    aspect="auto",
    cmap="OrRd",
    vmin=0,
    vmax=100
)

axes[1].set_title(
    "B. Student\nMUST",
    fontsize=13,
    fontweight="bold",
    pad=12
)

axes[1].set_xticks([0])
axes[1].set_xticklabels(["MUST"], fontsize=10)
axes[1].set_yticks([])

cbar1 = fig.colorbar(im1, ax=axes[1], fraction=0.18, pad=0.05)
cbar1.set_label("MUST priority (%)")

axes[1].set_xticks(np.arange(-0.5, 1, 1), minor=True)
axes[1].set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
axes[1].grid(which="minor", color="white", linestyle="-", linewidth=0.6)
axes[1].tick_params(which="minor", bottom=False, left=False)

for i in range(n_rows):
    val = student_data[i, 0]
    if not np.isnan(val):
        axes[1].text(
            0,
            i,
            f"{val:.0f}",
            ha="center",
            va="center",
            fontsize=8,
            color="black" if val < 70 else "white"
        )


# ------------------------------------------------------------
# Panel C: Divergence
# ------------------------------------------------------------

norm_delta = TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100)

im2 = axes[2].imshow(
    delta_data,
    aspect="auto",
    cmap="coolwarm",
    norm=norm_delta
)

axes[2].set_title(
    "C. Divergence",
    fontsize=13,
    fontweight="bold",
    pad=12
)

axes[2].set_xticks([0])
axes[2].set_xticklabels(["Delta"], fontsize=10)
axes[2].set_yticks([])

cbar2 = fig.colorbar(im2, ax=axes[2], fraction=0.18, pad=0.05)
cbar2.set_label("Structural mean - MUST (%)")

axes[2].set_xticks(np.arange(-0.5, 1, 1), minor=True)
axes[2].set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
axes[2].grid(which="minor", color="white", linestyle="-", linewidth=0.6)
axes[2].tick_params(which="minor", bottom=False, left=False)

for i in range(n_rows):
    val = delta_data[i, 0]
    if not np.isnan(val):
        axes[2].text(
            0,
            i,
            f"{val:+.0f}",
            ha="center",
            va="center",
            fontsize=8,
            color="black" if abs(val) < 55 else "white"
        )


# ------------------------------------------------------------
# 8. SAVE FIGURE
# ------------------------------------------------------------

fig.suptitle(
    "Requirement-level comparison between structural relevance and human MoSCoW prioritization",
    fontsize=15,
    fontweight="bold",
    y=1.01
)

plt.tight_layout()

output_png = SCRIPT_DIR / "requirement_structural_vs_student_priority_simplified.png"
output_jpg = SCRIPT_DIR / "requirement_structural_vs_student_priority_simplified.jpg"

fig.savefig(output_png, dpi=300, bbox_inches="tight")
fig.savefig(output_jpg, dpi=300, bbox_inches="tight", format="jpg")

print("\nFIGURE SAVED:")
print(output_png)
print(output_jpg)

plt.close(fig)

print("\nDone.")