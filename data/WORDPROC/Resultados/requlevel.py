# %% [markdown]
# # Decision Space Analysis: Requirement Selection Frequency
# This script computes the selection frequency of each requirement across the 10 post-optimization strategy profiles.

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. Configuration of the 10 analysis profiles (Exact user-requested names)
file_profiles = {
    'Framed group': 'framed.csv',
    'Domain-specific': 'domain.csv',
    'Efficiency-Productivity-Squandering': 'efici-product-squan.csv',
    'HDBSCAN all values': 'hdbscan-todo.csv',
    'HDBSCAN objective': 'hdbscan-efsatimsmall2.csv',
    'K-Medioids g0 allvalues': 'kmedio-3-0todo.csv',
    'K-Medioids g2 allvalues': 'kmedio-3-2todo.csv',
    'K-Medioids 2-0 objective': 'kmedio-2-0effsattime.csv',
    'TOPSIS': 'topsis.csv',
    'Weighted sum': 'weight.csv'
}

# 2. Load and process the requirements mapping file (50 to 42 mapping)
mapping_file = 'requirements_mapping_50_to_42.csv'
if os.path.exists(mapping_file):
    df_map = pd.read_csv(mapping_file)
    # Drop duplicates on the destination 42-ID to get a 1-to-1 mapping dictionary
    df_map_unique = df_map.drop_duplicates(subset=['mapped_req_42']).sort_values('mapped_req_42')
    # Create name mapping: { 'req_1': 'New File', ... }
    req_name_mapping = {f"req_{int(row['mapped_req_42'])}": row['reduced_name'] for _, row in df_map_unique.iterrows()}
else:
    print(f"⚠️ Warning: Mapping file '{mapping_file}' not found. Using generic IDs.")
    req_name_mapping = {f"req_{i}": f"Requirement {i}" for i in range(1, 43)}

# 3. Compute selection frequencies per strategy group
profile_frequencies = {}
target_requirements = [f"req_{i}" for i in range(1, 43)]

print("Calculating decision space frequencies...")
for profile_name, file_path in file_profiles.items():
    if os.path.exists(file_path):
        df_temp = pd.read_csv(file_path)
        
        # Ensure target columns exist in the dataframe
        valid_reqs = [col for col in target_requirements if col in df_temp.columns]
        
        # The mean of a binary column (0 or 1) multiplied by 100 yields the selection percentage
        frequency_series = df_temp[valid_reqs].mean() * 100
        profile_frequencies[profile_name] = frequency_series
    else:
        print(f"⚠️ Missing profile file: {file_path}")

# Build the final Decision Space DataFrame
df_decision_space = pd.DataFrame(profile_frequencies)

# Map row indices to their short English names from the mapping file
df_decision_space.index = df_decision_space.index.map(req_name_mapping)

print("Data unbundled and translated. Plotting...")

# %%
# 4. VISUALIZATION: ACADEMIC-READY COMPARATIVE HEATMAP
plt.figure(figsize=(14, 12))
sns.set_theme(style="ticks")

# Using 'YlGnBu' palette for an elegant progression from 0% (light yellow) to 100% (deep blue)
sns.heatmap(
    df_decision_space, 
    cmap="YlGnBu", 
    annot=True, 
    fmt=".1f", 
    linewidths=.5, 
    cbar_kws={'label': '% of solutions in the group including the requirement'}
)

# Formal Academic Titles and Labels
plt.title("Decision Space Analysis: Requirement Selection Frequency by Strategy", fontsize=14, fontweight='bold', y=1.02)
plt.xlabel("Post-Optimization Strategies / Filters", fontsize=12, labelpad=10)
plt.ylabel("System Requirements (Mapped Names)", fontsize=12, labelpad=10)

# Rotate labels to ensure clean scannability
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.yticks(fontsize=10)
plt.tight_layout()

# Export high-resolution image for paper embedding
output_filename = "decision_space_requirements.png"
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
print(f"🎉 Plot successfully exported as: '{output_filename}'")
plt.show()
# %%
