#pip install goatools
#find where you install goatools, replace its location with the "goatools_location" and run it in the terminal
# goatools_location/ncbi_gene_results_to_python.py -o genes_ncbi_mus_musculus_proteincoding.py gene_result.txt

#Make background gene set
#go to:
#https://www.ncbi.nlm.nih.gov/gene
#Type this line in the search box
#"10090"[Taxonomy ID] AND alive[property] AND genetype protein coding[Properties]
#human is 9606

#send to -> file -> create file (this will download the file "gene_results") -> Move it to your main directory

#you can move the created file to default import location so you dont have to make every time

###run this file one time to initialize###
from goatools.base import download_go_basic_obo

GODag(download_go_basic_obo())








