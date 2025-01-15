import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import concurrent.futures
import os

def filter_genes(df, cluster_col, gene_col, threshold_col, threshold_value):
    filtered = df[df[threshold_col] > threshold_value]
    gene_dict = {}
    for cluster in filtered[cluster_col].unique():
        genes = filtered[filtered[cluster_col] == cluster][gene_col].tolist()
        gene_dict[cluster] = genes
    return gene_dict

def query_go_api(genes, species="Mus musculus"):
    base_url = "http://api.geneontology.org/api/ontology/term/GO:0003677"
    payload = {
        "geneProductList": genes,  # Pass as a list, not a string
        "taxon": "10090",         # NCBI Taxonomy ID for Mus musculus
        "aspects": ["BP"]         # Biological Process
    }
    try:
        response = requests.post(base_url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {}

def visualize_go_results(cluster, go_results, output_dir):
    if not go_results:
        print(f"No GO terms found for cluster {cluster}")
        print(go_results)
        return

    terms = go_results.get("results", [])[:10]
    terms.sort(key=lambda x: x.get("pValue", 1))

    labels = [term["term"] for term in terms]
    values = [-1 * term.get("pValue", 1) for term in terms]
    colors = plt.cm.viridis(values)

    plt.figure(figsize=(10, 6))
    plt.barh(labels, values, color=colors)
    plt.xlabel("-log10(p-value)")
    plt.title(f"Top GO Terms for Cluster {cluster}")
    plt.tight_layout()

    output_path = os.path.join(output_dir, f"{cluster}_go_terms.png")
    plt.savefig(output_path)
    plt.close()

def save_gene_dict(gene_dict, output_file):
    writer = pd.ExcelWriter(output_file, engine='openpyxl')
    for cluster, genes in gene_dict.items():
        df = pd.DataFrame(genes, columns=["Genes"])
        df.to_excel(writer, sheet_name=cluster, index=False)
    writer.close()

def generate_summary_report(gene_dict, go_results, output_file):
    with PdfPages(output_file) as pdf:
        for cluster, genes in gene_dict.items():
            plt.figure(figsize=(8, 6))
            plt.text(0.1, 0.8, f"Cluster: {cluster}", fontsize=14, wrap=True) # Add cluster ID to the report
            plt.text(0.1, 0.6, f"Number of Genes: {len(genes)}", fontsize=12, wrap=True) # Add number of genes to the report
            plt.text(0.1, 0.4, f"Genes: {', '.join(genes)}", fontsize=11, wrap=True) # Add list of genes to the report
            plt.text(0.1, 0.2, f"GO Terms: {', '.join(go_results.get(cluster, {}).get('results', []))}", fontsize=11, wrap=True) # Add list of GO terms to the report
            plt.axis('off')
            pdf.savefig() 
            plt.close()

        for cluster, results in go_results.items():
            if results:
                terms = results.get("results", [])[:10]
                terms.sort(key=lambda x: x.get("pValue", 1))

                labels = [term["term"] for term in terms]
                values = [-1 * term.get("pValue", 1) for term in terms]
                colors = plt.cm.viridis(values)

                plt.figure(figsize=(10, 6))
                plt.barh(labels, values, color=colors)
                plt.xlabel("-log10(p-value)")
                plt.title(f"Top GO Terms for Cluster {cluster}")
                plt.tight_layout()
                pdf.savefig()
                plt.close()

# GUI Functions
def process_file():
    input_file = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if not input_file:
        return
#save the output file to the same directory as the input file
    output_dir = os.path.dirname(input_file)

    try:
        df = pd.read_excel(input_file)

        cluster_col = cluster_col_var.get()
        gene_col = gene_col_var.get()
        threshold_col = threshold_col_var.get()
        threshold_value = float(threshold_value_var.get())

        gene_dict = filter_genes(df, cluster_col, gene_col, threshold_col, threshold_value)

        save_gene_dict(gene_dict, os.path.join(output_dir, f"Differentiated_Gene_{os.path.basename(input_file)}"))

        go_results = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(query_go_api, genes): cluster
                for cluster, genes in gene_dict.items()
            }
            for future in concurrent.futures.as_completed(futures):
                cluster = futures[future]
                go_results[cluster] = future.result()

        for cluster, results in go_results.items():
            visualize_go_results(cluster, results, output_dir)

        generate_summary_report(gene_dict, go_results, os.path.join(output_dir, "Summary_Report.pdf"))

        messagebox.showinfo("Success", "Processing complete!")

    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI Setup
root = tk.Tk()
root.title("Automated Gene Ontology Analysis Tool")

tk.Label(root, text="Cluster Column:").grid(row=0, column=0, padx=10, pady=5)
cluster_col_var = tk.StringVar(value="cluster")
tk.Entry(root, textvariable=cluster_col_var).grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Gene Column:").grid(row=1, column=0, padx=10, pady=5)
gene_col_var = tk.StringVar(value="gene")
tk.Entry(root, textvariable=gene_col_var).grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Threshold Column:").grid(row=2, column=0, padx=10, pady=5)
threshold_col_var = tk.StringVar(value="avg_log2FC")
tk.Entry(root, textvariable=threshold_col_var).grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Threshold Value:").grid(row=3, column=0, padx=10, pady=5)
threshold_value_var = tk.StringVar(value="1.5")
tk.Entry(root, textvariable=threshold_value_var).grid(row=3, column=1, padx=10, pady=5)

tk.Button(root, text="Process File", command=process_file).grid(row=4, column=0, columnspan=2, pady=20)

root.mainloop()
