# -*- coding: utf-8 -*-

# ============================================================
# Single-Lens Requirement Comparison:
# Domain-specific structural relevance vs Student MoSCoW MUST
# ============================================================
#
# Output files:
#   - requirement_domain_vs_student_must.png
#   - requirement_domain_vs_student_must.jpg
#   - requirement_domain_vs_student_must_summary.csv
#
# Put this script in the same folder as:
#   - domain.csv
#   - requirements_mapping_50_to_42.csv
#   - moscow_students.csv
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

# Recommended single lens for the paper:
# Domain-specific gives a domain-oriented structural relevance profile.
SELECTED_PROFILE_NAME = "Domain-specific"
SELECTED_PROFILE_FILE = "domain.csv"

mapping_file = SCRIPT_DIR / "requirements_mapping_50_to_42.csv"
moscow_file = SCRIPT_DIR / "moscow_students.csv"
profile_file = SCRIPT_DIR / SELECTED_PROFILE_FILE

target_requirements = [f"req_{i}" for i in range(1, 43)]

# Sorting options:
#   "original" -> keeps the reduced 42-requirement order.
#   "delta"    -> sorts by absolute difference between selected lens and Student MUST.
#   "lens"     -> sorts by selected lens inclusion frequency.
#   "must"     -> sorts by Student MUST percentage.
SORT_MODE = "original"

# Keep all 42 requirements for traceability.
TOP_N = None

# If True, creates a transposed version.
# Recommendation for paper: keep False.
TRANSPOSE = False


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
# 3. COMPUTE REQUIREMENT FREQUENCY FOR SELECTED PROFILE
# ------------------------------------------------------------

if not profile_file.exists():
    raise FileNotFoundError(
        f"{SELECTED_PROFILE_FILE} not found in {SCRIPT_DIR}. "
        "Put the selected profile CSV in the same folder as this script."
    )

df_profile = pd.read_csv(profile_file)

valid_reqs = [col for col in target_requirements if col in df_profile.columns]

if not valid_reqs:
    raise ValueError(
        f"No valid requirement columns found in {SELECTED_PROFILE_FILE}. "
        "Expected columns req_1, req_2, ..., req_42."
    )

lens_frequency = df_profile[valid_reqs].mean() * 100
lens_frequency = lens_frequency.reindex(target_requirements)
lens_frequency.name = SELECTED_PROFILE_NAME

print(f"Requirement inclusion frequency computed for profile: {SELECTED_PROFILE_NAME}")


# ------------------------------------------------------------
# 4. LOAD STUDENT MOSCOW PRIORITIZATION
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
# average the MUST percentage to keep the 0-100 scale.
df_must_42 = (
    df_moscow_merge
    .groupby("req_id_42", as_index=False)["must_pct"]
    .mean()
    .set_index("req_id_42")
    .rename(columns={"must_pct": "Student MUST"})
)

df_must_42 = df_must_42.reindex(target_requirements)

print("Student MoSCoW MUST percentages loaded and mapped to the 42-requirement space.")


# ------------------------------------------------------------
# 5. BUILD COMPARISON MATRIX
# ------------------------------------------------------------

df_compare = pd.DataFrame(index=target_requirements)
df_compare[SELECTED_PROFILE_NAME] = lens_frequency
df_compare["Student MUST"] = df_must_42["Student MUST"]
df_compare["Delta"] = df_compare[SELECTED_PROFILE_NAME] - df_compare["Student MUST"]

df_compare["Requirement label"] = [
    req_name_mapping.get(req, req) for req in df_compare.index
]

# Sorting
if SORT_MODE == "delta":
    df_compare = df_compare.reindex(
        df_compare["Delta"].abs().sort_values(ascending=False).index
    )
elif SORT_MODE == "lens":
    df_compare = df_compare.sort_values(SELECTED_PROFILE_NAME, ascending=False)
elif SORT_MODE == "must":
    df_compare = df_compare.sort_values("Student MUST", ascending=False)
elif SORT_MODE == "original":
    df_compare = df_compare.reindex(target_requirements)
else:
    raise ValueError("SORT_MODE must be one of: original, delta, lens, must.")

if TOP_N is not None:
    df_compare = df_compare.head(TOP_N)

summary_file = SCRIPT_DIR / "requirement_domain_vs_student_must_summary.csv"
df_compare.to_csv(summary_file, encoding="utf-8-sig")

print("\nSummary exported:")
print(summary_file)


# ------------------------------------------------------------
# 6. TRANSPOSED PLOT: TWO MAIN BANDS + SMALL DIVERGENCE STRIP
# ------------------------------------------------------------

row_labels = df_compare["Requirement label"].tolist()
n_cols = len(df_compare)

data_lens = df_compare[[SELECTED_PROFILE_NAME]].to_numpy(dtype=float).T
data_must = df_compare[["Student MUST"]].to_numpy(dtype=float).T
data_delta = df_compare[["Delta"]].to_numpy(dtype=float).T

fig_width = max(16, 0.42 * n_cols)
fig_height = 5.4

fig, axes = plt.subplots(
    3,
    1,
    figsize=(fig_width, fig_height),
    gridspec_kw={"height_ratios": [1, 1, 0.42]},
    sharex=True
)

# ------------------------------------------------------------
# Panel A: Domain-specific inclusion
# ------------------------------------------------------------

im0 = axes[0].imshow(
    data_lens,
    aspect="auto",
    cmap="YlGnBu",
    vmin=0,
    vmax=100
)

axes[0].set_title(
    "A. Domain-specific structural inclusion",
    fontsize=12,
    fontweight="bold",
    loc="left",
    pad=8
)

axes[0].set_yticks([0])
axes[0].set_yticklabels(["Domain"], fontsize=10)
axes[0].set_xticks(np.arange(n_cols))
axes[0].set_xticklabels([])

cbar0 = fig.colorbar(im0, ax=axes[0], fraction=0.015, pad=0.01)
cbar0.set_label("Inclusion (%)", fontsize=9)

axes[0].set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
axes[0].set_yticks(np.arange(-0.5, 1, 1), minor=True)
axes[0].grid(which="minor", color="white", linestyle="-", linewidth=0.6)
axes[0].tick_params(which="minor", bottom=False, left=False)

for j in range(n_cols):
    val = data_lens[0, j]
    if not np.isnan(val):
        axes[0].text(
            j,
            0,
            f"{val:.0f}",
            ha="center",
            va="center",
            fontsize=7,
            color="black" if val < 70 else "white"
        )

# ------------------------------------------------------------
# Panel B: Student MUST
# ------------------------------------------------------------

im1 = axes[1].imshow(
    data_must,
    aspect="auto",
    cmap="OrRd",
    vmin=0,
    vmax=100
)

axes[1].set_title(
    "B. Human MoSCoW priority",
    fontsize=12,
    fontweight="bold",
    loc="left",
    pad=8
)

axes[1].set_yticks([0])
axes[1].set_yticklabels(["MUST"], fontsize=10)
axes[1].set_xticks(np.arange(n_cols))
axes[1].set_xticklabels([])

cbar1 = fig.colorbar(im1, ax=axes[1], fraction=0.015, pad=0.01)
cbar1.set_label("MUST (%)", fontsize=9)

axes[1].set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
axes[1].set_yticks(np.arange(-0.5, 1, 1), minor=True)
axes[1].grid(which="minor", color="white", linestyle="-", linewidth=0.6)
axes[1].tick_params(which="minor", bottom=False, left=False)

for j in range(n_cols):
    val = data_must[0, j]
    if not np.isnan(val):
        axes[1].text(
            j,
            0,
            f"{val:.0f}",
            ha="center",
            va="center",
            fontsize=7,
            color="black" if val < 70 else "white"
        )

# ------------------------------------------------------------
# Panel C: Small divergence strip
# ------------------------------------------------------------

norm_delta = TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100)

im2 = axes[2].imshow(
    data_delta,
    aspect="auto",
    cmap="coolwarm",
    norm=norm_delta
)

axes[2].set_title(
    "C. Divergence signal: domain-specific inclusion minus student MUST",
    fontsize=11,
    fontweight="bold",
    loc="left",
    pad=6
)

axes[2].set_yticks([0])
axes[2].set_yticklabels(["Delta"], fontsize=9)

axes[2].set_xticks(np.arange(n_cols))
axes[2].set_xticklabels(row_labels, rotation=65, ha="right", fontsize=8)

cbar2 = fig.colorbar(im2, ax=axes[2], fraction=0.015, pad=0.01)
cbar2.set_label("Difference", fontsize=9)

axes[2].set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
axes[2].set_yticks(np.arange(-0.5, 1, 1), minor=True)
axes[2].grid(which="minor", color="white", linestyle="-", linewidth=0.6)
axes[2].tick_params(which="minor", bottom=False, left=False)

# No numerical annotation in divergence strip.
# It is intended only as a visual signal of disagreement.

# ------------------------------------------------------------
# 7. FINAL TITLE AND SAVE
# ------------------------------------------------------------

fig.suptitle(
    "Requirement-level comparison between domain-specific structural relevance and human MoSCoW priority",
    fontsize=14,
    fontweight="bold",
    y=1.03
)

plt.tight_layout()

output_png = SCRIPT_DIR / "requirement_domain_vs_student_must_with_delta_strip.png"
output_jpg = SCRIPT_DIR / "requirement_domain_vs_student_must_with_delta_strip.jpg"

fig.savefig(output_png, dpi=300, bbox_inches="tight")
fig.savefig(output_jpg, dpi=300, bbox_inches="tight", format="jpg")

print("\nFIGURE SAVED:")
print(output_png)
print(output_jpg)

plt.close(fig)

print("\nDone.")