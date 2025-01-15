import pandas as pd
import requests
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import networkx as nx
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
from fpdf import FPDF

# Constants
GO_API_URL = "http://api.geneontology.org/api/bioentity/function/GO:0006915"  # Base API URL

# Function: Read Excel file
def read_excel_file(file_path):
    try:
        data = pd.read_excel(file_path)
        return data
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

# Function: Extract significant genes
def extract_significant_genes(data, avg_log2FC_threshold=1.5, column="avg_log2FC"):
    significant_genes = data[data[column] > avg_log2FC_threshold]
    return significant_genes

# Function: Query GO API
def query_go_api(gene_list):
    results = {}
    for gene in gene_list:
        try:
            response = requests.get(f"{GO_API_URL}/search/entity?q={gene}&rows=10")
            if response.status_code == 200:
                response_data = response.json()
                go_terms = [entry['id'] for entry in response_data.get('results', [])]
                results[gene] = go_terms
            else:
                print(f"API request failed for {gene}: {response.status_code}")
        except Exception as e:
            print(f"Error querying API for gene {gene}: {e}")
    return results

# Visualization: Bar Chart (Static)
def create_bar_chart(data, output_file):
    terms, counts = zip(*data.items())
    plt.figure(figsize=(10, 6))
    plt.bar(terms, counts, color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

# Visualization: Interactive Plotly
def create_interactive_chart(data, output_file):
    terms, counts = zip(*data.items())
    fig = go.Figure(data=[go.Bar(x=terms, y=counts)])
    fig.update_layout(title="Gene Ontology Terms", xaxis_title="GO Term", yaxis_title="Frequency")
    fig.write_html(output_file)

# Visualization: Network Diagram
def create_network_diagram(go_terms, output_file):
    G = nx.Graph()
    for gene, terms in go_terms.items():
        for term in terms:
            G.add_edge(gene, term)
    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray', font_size=8)
    plt.savefig(output_file)
    plt.close()

# GUI Functionality
def run_gui():
    root = tk.Tk()
    root.title("Automated GO Analysis Tool")

    def browse_file():
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            entry_file_path.delete(0, tk.END)
            entry_file_path.insert(0, file_path)

    def process_file():
        file_path = entry_file_path.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a file")
            return

        data = read_excel_file(file_path)
        if data is not None:
            significant_genes = extract_significant_genes(data)
            gene_list = significant_genes['gene'].tolist()
            go_results = query_go_api(gene_list)

            # Create visualizations
            bar_chart_file = os.path.join(os.path.dirname(file_path), "bar_chart.png")
            interactive_file = os.path.join(os.path.dirname(file_path), "interactive_chart.html")
            network_file = os.path.join(os.path.dirname(file_path), "network_diagram.png")

            term_counts = {}
            for terms in go_results.values():
                for term in terms:
                    term_counts[term] = term_counts.get(term, 0) + 1

            create_bar_chart(term_counts, bar_chart_file)
            create_interactive_chart(term_counts, interactive_file)
            create_network_diagram(go_results, network_file)

            messagebox.showinfo("Success", "GO Analysis and visualizations created.")

    # GUI Layout
    tk.Label(root, text="Select Excel File:").grid(row=0, column=0, padx=10, pady=10)
    entry_file_path = tk.Entry(root, width=50)
    entry_file_path.grid(row=0, column=1, padx=10, pady=10)
    tk.Button(root, text="Browse", command=browse_file).grid(row=0, column=2, padx=10, pady=10)
    tk.Button(root, text="Process", command=process_file).grid(row=1, column=1, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    run_gui()