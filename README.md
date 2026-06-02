# ReqDasboard


https://anrpdecision.streamlit.app/



✅ ✅ Functional Description of the Application
🧠 Overview
The Assisted Next Release Problem (ANRP) Dashboard is an interactive decision-support tool designed to help users explore, analyze, and compare candidate solutions for software release planning problems. The application integrates multi-objective optimization, multi-criteria decision-making (MCDM), clustering techniques, and interactive visualization to facilitate informed decision-making.

🎯 Purpose
The goal of the application is to support decision-makers in:

Evaluating trade-offs among competing objectives
Identifying high-quality solutions based on preferences
Discovering structural patterns (e.g., clusters) in the solution space
Comparing solutions across multiple dimensions (performance, stakeholders, requirements)
Narrowing down alternatives through interactive filtering and selection


📊 Data Input and Preparation
The system supports two data acquisition modes:


CSV Upload Mode
Users can upload precomputed datasets containing solutions and performance indicators.


Pipeline Mode
The application dynamically builds the dataset from a predefined problem configuration, computing selected indicators via an internal pipeline.


The dataset typically contains:

Optimization metrics (e.g., cost, effort)
Quality indicators (e.g., satisfaction, coverage)
Stakeholder coverage values (stcov_*)
Requirement inclusion (req_*)


⚙️ Core Functionalities
1. Filtering Mechanism
Users can filter the solution space using:

Numeric sliders for optimization metrics
Numeric sliders for quality indicators

Filtering dynamically updates all visualizations and subsequent analyses.

2. Selection Modes
The application provides multiple decision-support methods, grouped into conceptual categories:

🔵 Preference-based Methods (MCDM)
A unified multi-criteria decision-making module allows users to rank solutions using:

Weighted Sum Model
TOPSIS

Users can:

Select criteria to maximize or minimize
Rank solutions based on computed scores
Restrict the analysis to the top-N alternatives


🟢 Diversity-based Methods (Clustering)
The application supports clustering to explore structural diversity in the solution space:

K-Medoids (manual or silhouette-based selection of k)
HDBSCAN (density-based clustering with automatic detection of cluster structure)

Features:

Identification of natural solution groupings
Detection of noise (outliers) in HDBSCAN
Visualization of cluster sizes and structure


🟣 Efficiency-based Method
A ratio-based approach computes:
Efficiency = Benefit / Cost

Users can define:

Benefit metric (maximize)
Cost metric (minimize)


🟠 Ranking-based Method
Solutions are ranked based on their frequency of appearance in top-N sets across multiple criteria.

3. Interactive Visualization
📍 Trade-off Maps

Scatter plots displaying relationships between pairs of metrics
Optional point sizing using a third metric
Dynamic coloring based on the selected method

🎯 Selection Highlighting
Users can manually select solutions:

Selected solutions remain fully visible
Non-selected solutions are visually de-emphasized via reduced opacity
Supports both exploration and focused analysis


4. Focus Mode
An optional focus mode allows users to:

Restrict all analyses to the manually selected subset
Recompute rankings and clustering on the selected solutions

This enables deep inspection of specific regions of the solution space.

5. Comparative Analysis (Radar and Tabs)
A dedicated comparison view enables detailed analysis of selected solutions across four dimensions:

📊 Performance Radar

Customizable radar chart
User-defined metrics and optimization direction (maximize/minimize)
Normalized values for fair comparison


👥 Stakeholder Coverage

Radar visualization of stakeholder satisfaction
Users can manually select which stakeholders to analyze
Automatic normalization and scaling


📋 Requirements View

Heatmap showing which requirements are included in each solution
Binary encoding with high-contrast visualization


🔗 Stakeholder–Requirement Alignment

Matrix visualization linking stakeholders and requirements
Highlights:

requested vs included features
final release composition


Includes an additional summary row representing the selected solution


6. User Interaction and State Management
The application supports:

Persistent session state
Dynamic UI updates based on user actions
Manual solution selection across visualizations

A “Reset All” control allows users to restore the application to its initial state.

🎨 Visualization Features

Adaptive color schemes (continuous vs categorical)
Opacity-based highlighting for selection
Multi-layered plots preserving data context
Interactive Plotly charts with hover information


🧩 Extensibility
The architecture supports:

Additional MCDM methods (e.g., PROMETHEE, VIKOR)
Alternative clustering techniques
New indicators and problem configurations
Enhanced comparison metrics


✅ Summary
The ANRP Dashboard provides a comprehensive framework for analyzing complex release planning problems by combining:

Multi-objective optimization insights
Multi-criteria decision models
Clustering-based exploration
Rich, interactive visual analytics

The tool enables both global exploration and focused decision-making, making it suitable for research, teaching, and practical decision-support scenarios.
