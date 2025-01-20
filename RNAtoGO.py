import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import cm
from matplotlib.colors import Normalize
import seaborn as sns
import textwrap
from genes_ncbi_mus_musculus_proteincoding import GENEID2NT as GeneID2nt_mus
from goatools.base import download_go_basic_obo
from goatools.base import download_ncbi_associations
from goatools.obo_parser import GODag
from goatools.anno.genetogo_reader import Gene2GoReader
from goatools.goea.go_enrichment_ns import GOEnrichmentStudyNS

# Initialize the Gene Ontology tools
obodag = GODag("go-basic.obo")
fin_gene2go = download_ncbi_associations()

mapper = {}
for key in GeneID2nt_mus:
    mapper[GeneID2nt_mus[key].Symbol] = GeneID2nt_mus[key].GeneID

inv_map = {v: k for k, v in mapper.items()}

objanno = Gene2GoReader(fin_gene2go, taxids=[10090])
ns2assoc = objanno.get_ns2assc()

goeaobj = GOEnrichmentStudyNS(
    GeneID2nt_mus.keys(),
    ns2assoc,
    obodag,
    propagate_counts=False,
    alpha=0.05,
    methods=['fdr_bh']
)

GO_items = []
for ns in ['BP', 'CC', 'MF']:
    temp = goeaobj.ns2objgoea[ns].assoc
    for item in temp:
        GO_items += temp[item]


def filter_genes(df, cluster_col, gene_col, threshold_col, threshold_value):
    filtered = df[df[threshold_col] > threshold_value]
    gene_dict = {}
    for cluster in filtered[cluster_col].unique():
        genes = filtered[filtered[cluster_col] == cluster][gene_col].tolist()
        gene_dict[cluster] = genes
    return gene_dict


def go_it(test_cluster):
    print(f'Cluster: {test_cluster.cluster} input genes: {len(test_cluster.test_genes)}')

    mapped_genes = []
    for gene in test_cluster.test_genes:
        try:
            mapped_genes.append(mapper[gene])
        except KeyError:
            pass
    print(f'mapped genes: {len(mapped_genes)}')

    goea_results_all = goeaobj.run_study(mapped_genes)
    goea_results_sig = [r for r in goea_results_all if r.p_fdr_bh < 0.05]
    GO = pd.DataFrame(list(map(lambda x: [x.GO, x.goterm.name, x.goterm.namespace, x.p_uncorrected, x.p_fdr_bh,
                                           x.ratio_in_study[0], x.ratio_in_study[1], GO_items.count(x.GO),
                                           list(map(lambda y: inv_map[y], x.study_items))],
                                goea_results_sig)),
                      columns=['GO', 'term', 'class', 'p', 'p_corr', 'n_genes', 'n_study', 'n_go', 'study_genes'])

    GO = GO[GO.n_genes > 1]
    GO = GO.sort_values('p_corr').head(10)  # Limit to top 10 GO terms
    return GO


def save_gene_list(gene_list, output_file):
    writer = pd.ExcelWriter(output_file, engine='openpyxl')
    for cluster, genes in gene_list.items():
        df = pd.DataFrame(genes, columns=["Genes"])
        df.to_excel(writer, sheet_name=str(cluster), index=False)
    writer.close()


def generate_summary_report(gene_dict, go_results, output_file):
    with PdfPages(output_file) as pdf:
        # First page with summary table
        plt.figure(figsize=(8, 6))
        plt.axis('off')
        plt.text(0.1, 1.0, "Clusters Summary", fontsize=14)

        # Add vertical spacing between each line
        y_position = 0.8  # Start position for text
        line_spacing = 0.05  # Spacing between lines

        for cluster, genes in gene_dict.items():
            plt.text(0.1, y_position, f"Cluster {cluster}: {len(genes)} genes", fontsize=11)
            y_position -= line_spacing

        pdf.savefig()
        plt.close()

        # GO terms for each cluster on a new page
        for cluster, go_data in go_results.items():
            plt.figure(figsize=(8, 6))
            plt.axis('off')
            plt.text(0.1, 1.0, f"Cluster: {cluster}", fontsize=12)

            # Wrap GO terms text and add spacing
            y_position = 0.8
            wrapped_terms = textwrap.wrap(", ".join(go_data['term'].tolist()), width=80)
            for line in wrapped_terms:
                if y_position <= 0.1:  # If text goes out of bounds, save page and start a new one
                    pdf.savefig()
                    plt.close()
                    plt.figure(figsize=(8, 6))
                    plt.axis('off')
                    plt.text(0.1, 1.0, f"Cluster: {cluster} (continued)", fontsize=12)
                    y_position = 0.8
                plt.text(0.1, y_position, line, fontsize=10)
                y_position -= line_spacing

            pdf.savefig()
            plt.close()


def visualize_go_terms(cluster, go_data, output_dir):
    if not go_data.empty:
        # Normalize p_corr values for colormap
        norm = Normalize(vmin=go_data['n_genes'].min(), vmax=go_data['n_genes'].max())
        colormap = cm.ScalarMappable(norm=norm, cmap='viridis')

        # Sort GO terms in descending order for y-axis
        go_data = go_data.sort_values('n_genes', ascending=False)

        fig, ax = plt.subplots(figsize=(6, 6))
        
        # Bar plot with colormap applied to 'n_genes'
        bar_colors = [colormap.to_rgba(n) for n in go_data['n_genes']]
        sns.barplot(
            data=go_data,
            x='n_genes',
            y='term',
            palette=bar_colors,
            ax=ax
        )

        # Wrap term labels and set axes titles
        ax.set_yticklabels([textwrap.fill(term, 30) for term in go_data['term']], fontsize=10)
        ax.set_title(f"GO Terms for Cluster {cluster}", fontsize=12, pad=20)
        ax.set_xlabel("Number of Genes", fontsize=11)
        ax.set_ylabel("GO Term", fontsize=11)

        # Add color bar at the lower right corner
        cbar_ax = ax.inset_axes([1.05, 0.1, 0.03, 0.8])  # x, y, width, height
        fig.colorbar(colormap, cax=cbar_ax, orientation='vertical', label=f"le-{int(go_data['n_genes'].min())} to {int(go_data['n_genes'].max())}")
        
        # Display only the highest and lowest values on the scale
        cbar_ax.set_yticks([go_data['n_genes'].min(), go_data['n_genes'].max()])
        cbar_ax.set_yticklabels([f"{int(go_data['n_genes'].min())}", f"{int(go_data['n_genes'].max())}"])

        # Save the plot
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, f"GO_Terms_{cluster}.png")
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()


# GUI Functions
def process_file():
    input_file = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if not input_file:
        return

    output_dir = os.path.join(os.path.dirname(input_file), "output_files")
    os.makedirs(output_dir, exist_ok=True)

    png_dir = os.path.join(output_dir, "png_files")
    os.makedirs(png_dir, exist_ok=True)

    try:
        df = pd.read_excel(input_file)

        cluster_col = cluster_col_var.get()
        gene_col = gene_col_var.get()
        threshold_col = threshold_col_var.get()
        threshold_value = float(threshold_value_var.get())

        gene_dict = filter_genes(df, cluster_col, gene_col, threshold_col, threshold_value)
        save_gene_list(gene_dict, os.path.join(output_dir, "Differentiated_Genes.xlsx"))

        go_results = {}
        for cluster, genes in gene_dict.items():
            go_results[cluster] = go_it(pd.Series({"cluster": cluster, "test_genes": genes}))

        for cluster, go_data in go_results.items():
            visualize_go_terms(cluster, go_data, png_dir)

        summary_report_file = os.path.join(output_dir, "Summary_Report.pdf")
        generate_summary_report(gene_dict, go_results, summary_report_file)

        messagebox.showinfo("Success", f"Processing complete!\nOutput saved to {output_dir}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


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
