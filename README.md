# 🚀 ANRP Decision Space Explorer

[Streamlit App](https://anrpdecision.streamlit.app/)

##  Overview
The **Assisted Next Release Problem (ANRP) Decision Space Explorer** is an interactive decision-support dashboard designed to help software engineers, product managers, and stakeholders explore, analyze, and compare candidate solutions for software release planning. 

By integrating multi-objective optimization insights, multi-criteria decision-making (MCDM), clustering techniques, and rich interactive visualizations, the application facilitates informed and strategic decision-making in complex requirement selection scenarios.

## 🎯 Purpose
The primary goal of this application is to support decision-makers in:
* **Evaluating trade-offs** among competing objectives (e.g., maximizing satisfaction vs. minimizing cost).
* **Identifying high-quality solutions** based on specific business preferences or domain rules.
* **Discovering structural patterns** and taxonomies in the solution space through clustering.
* **Comparing alternatives** across multiple dimensions (performance, stakeholder coverage, and requirement alignment).
* **Narrowing down the decision space** through interactive filtering and focused analysis.

---

## 🏷️ Data Input, Preparation & Enrichment
The system provides a robust foundational pipeline with two main data acquisition modes and a dynamic enrichment engine:

### 1. Data Source Selection
* **📥 Build from NRP instance:** Parses a raw literature benchmark dataset (e.g., Bagnall, MSLite) and prepares it dynamically for custom indicator generation.
* **📂 Load enriched solution set:** Directly loads an already processed and structured CSV file containing pre-calculated metrics.

### 2. 🎨 Semantic Enrichment
Allows users to dynamically inject computed software engineering proxy metrics into the current dataset. Only attributes with a recognized calculation method based on the loaded data are displayed.
* **🔵 Quality indicators:** Select attributes to calculate derived quality metrics dynamically.

---

## 🔍 Analytical Lenses (Decision-Support Methods)
The application moves away from basic filtering to offer advanced "Lenses" that structure the solution space according to different analytical needs:

* **Exploratory view:** The baseline mode for manual exploration and threshold-based filtering.
* **👁️ Preference lens (MCDA):** A multi-criteria decision-making module (Weighted Sum Model, TOPSIS) that allows users to rank solutions by weighing specific criteria to maximize or minimize.
* **✨ Diversity lens (Clustering):** Explores structural diversity to find natural solution groupings or taxonomies using K-Medoids or HDBSCAN (density-based clustering with noise detection).
* **⚡ Efficiency lens:** A ratio-based approach computing Return on Investment (ROI) by defining a specific Benefit metric to maximize and a Cost metric to minimize.
* **💡 Domain-specific lens:** Ranks solutions based on their frequency of appearance in top-N sets across multiple individual criteria (expert-rule heuristics).

---

## 📊 Interactive Visual Analytics
### 📍 Trade-off Maps (Scatter Plots)
* 2D relationships between user-selected optimization metrics.
* Optional point sizing utilizing a third metric (e.g., effort or cost).
* Dynamic coloring representing the active Analytical Lens (e.g., clusters, MCDA scores).

### 🎯 Selection & Focus Mode
* **Selection Highlighting:** Users can manually select specific solutions. Selected points remain fully visible, while non-selected solutions fade via reduced opacity to preserve global context.
* **Focus Mode:** Restricts all subsequent analyses, ranking algorithms, and clustering **only** to the manually selected subset, enabling deep, localized inspection.

---

## 🆚 Detailed Comparison View
A dedicated comparison layout enables an in-depth analysis of the filtered or selected solutions (Toggle between *All current solutions* or *☑️ Pick solutions to compare*).

* **📊 Performance Radar:** A customizable normalized radar chart evaluating user-defined metrics and optimization directions.
* **👥 Stakeholder Coverage:** Radar visualization analyzing stakeholder satisfaction, automatically normalized for fair comparison.
* **📋 Requirements View:** A binary-encoded heatmap displaying the exact composition of included vs. excluded requirements across candidate solutions.
* **🤝 Stakeholder–Requirement Alignment:** A matrix visualization linking stakeholders' requested features with the final release composition, acting as a traceability matrix.

---

## 🛠️ Extensibility & Architecture
Designed with scalability in mind, the architecture easily supports the integration of:
* Additional MCDA algorithms (e.g., PROMETHEE, VIKOR).
* Alternative unsupervised learning techniques.
* Custom problem configurations and new Semantic Enrichment indicators.

## 💻 Running Locally

To run this dashboard on your local machine:

1. Clone the repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
