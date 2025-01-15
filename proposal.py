import pandas as pd
import requests

#from scRNA_seq excel file, generate dictionary of culsteres as keys and list of genes as values:
def read_excel_file(file_path):
    data = pd.read_excel(file_path)
    return data

#extract genes with log2foldchange > 1.5:
def extract_significant_genes(data, avg_log2FC_threshold=1.5, column="avg_log2FC"):
    significant_genes = data[data[column] > avg_log2FC_threshold]
    return significant_genes

#create dictionary of clusters and genes:
def create_cluster_gene_dict(data):
    cluster_gene_dict = {}
    for cluster in data['cluster'].unique():
        genes = data[data['cluster'] == cluster]['gene'].tolist()
        cluster_gene_dict[cluster] = genes
    return cluster_gene_dict

#send significant genes list of each cluster to GO API: http://api.geneontology.org/api/bioentity/function/GO:0006915
def query_go_api(cluster_gene_dict):
    GO_API_URL = "http://api.geneontology.org/api/bioentity/function/GO:0006915"  # Base API URL
    results = {}
    for cluster, genes in cluster_gene_dict.items():
        try:
            response = requests.get(f"{GO_API_URL}/{genes}")
            if response.status_code == 200:
                go_terms = response.json().get('results', [])
                results[cluster] = go_terms
            else:
                print(f"API request failed for {cluster}: {response.status_code}")
        except Exception as e:
            print(f"Error querying API for cluster {cluster}: {e}")
    return results

#save dictionary of clusters and GO terms to a text file
def save_results(results, output_file):
    with open(output_file, 'w') as file:
        for cluster, terms in results.items():
            file.write(f"{cluster}: {', '.join(terms)}\n")

def __main__():
    file_path = r"C:\Users\osher.WISMAIN\Python_programming_course_2024.11\scRNA_to_GO_generator\new_cluster_ids_markers.xlsx"
    output_file = "GO_terms.txt"
    data = read_excel_file(file_path)
    significant_genes = extract_significant_genes(data)
    cluster_gene_dict = create_cluster_gene_dict(significant_genes)
    results = query_go_api(cluster_gene_dict)
    save_results(results, output_file)

if __name__ == "__main__":
    __main__()