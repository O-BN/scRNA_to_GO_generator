### Automated Gene Ontology Analysis Tool for scRNA Data

#### Objective
The goal of this project is to develop a Python-based tool that automates the analysis of single-cell RNA sequencing (scRNA-seq) clusters for their gene ontology (GO) classifications. This tool enables researchers to extract significant genes from scRNA-seq data, analyze their biological functions using the Gene Ontology framework, and visualize the results. By simplifying this process, the tool offers an efficient way to interpret gene functions within cellular clusters.

---

#### Features and Workflow

##### 1. **Input Processing:**
- The tool begins by reading an Excel file containing scRNA-seq results. 
- Users can specify:
  - The column that identifies clusters (default: `"cluster"`).
  - The column containing gene names (default: `"gene"`).
  - A column for a numeric threshold (default: `"avg_log2FC"`), used to filter significant genes.
  - A threshold value (default: `1.5`) to identify genes of interest.
- The tool dynamically filters and organizes the data, extracting genes associated with each cluster.

##### 2. **Gene List Extraction:**
- For each cluster, the program compiles a list of significantly differentiated genes that meet the user's threshold criteria.
- The output is organized into a dictionary:
  - **Keys**: Cluster identifiers.
  - **Values**: Lists of significant genes for each cluster.
- This data is stored in an Excel file for further use.

##### 3. **Gene Ontology Analysis:**
- Using the Gene Ontology tools (`goatools`), the tool maps the significant genes to their corresponding Gene Ontology terms.
- It focuses on three GO namespaces:
  - **Biological Process (BP)**
  - **Cellular Component (CC)**
  - **Molecular Function (MF)**
- The tool identifies significant GO terms based on adjusted p-values (`p_fdr_bh`) and selects the top 10 terms for each cluster.

##### 4. **Visualization:**
- **Bar Charts**:
  - A vertical bar chart is generated for each cluster, showing the top GO terms ranked by the number of genes associated with each term.
  - The bars are color-coded based on the significance of the terms, using a continuous color gradient.
- **Label Management**:
  - Term labels are wrapped to avoid overlapping, ensuring readability.
  - The visualization includes a color bar that dynamically scales with the range of significance values.
- Each chart is saved as a PNG file with a filename that includes the cluster identifier.

##### 5. **Output:**
- **Excel File**:
  - Saves the filtered gene lists for each cluster in a single Excel file named `Differentiated_Genes.xlsx`.
- **GO Analysis Results**:
  - Includes details such as GO terms, p-values, adjusted p-values, and associated genes.
- **Summary Report**:
  - Generates a PDF report summarizing:
    - The number of significant genes per cluster.
    - The top GO terms for each cluster, along with visualizations.

##### 6. **Graphical User Interface (GUI):**
- A simple GUI is implemented using **Tkinter**, allowing users to:
  - Select the input file.
  - Specify column names and threshold values.
  - Execute the analysis with minimal effort.
- The GUI ensures accessibility for users with limited programming experience.

---

#### Note
Before using the main script, **`RNAtoGO.py`**, to analyze RNA results, users must first execute the setup script, **`setup_GO_terms_locally.py`**. This setup script ensures that all necessary Gene Ontology data is downloaded and configured locally, enabling the tool to perform efficient and accurate analysis. Follow the instructions provided in **`setup_GO_terms_locally.py`** carefully to avoid errors during execution.

---

#### Technologies and Libraries
- **Data Handling**: `pandas`, `openpyxl`.
- **Gene Ontology Analysis**: `goatools`.
- **Visualization**: `matplotlib`, `seaborn`.
- **User Interface**: `Tkinter`.
- **Additional Libraries**: `os`, `textwrap`, `tkinter.messagebox`.

---

#### Summary
This project represents a robust pipeline for analyzing scRNA-seq data. It automates the identification of significant genes, maps them to their biological functions, and generates insightful visualizations. Designed with user-friendliness in mind, the tool allows researchers to streamline their analysis process, providing clarity and focus in the study of gene ontology.