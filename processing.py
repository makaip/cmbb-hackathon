import pandas as pd
from io import BytesIO
import requests
from typing import Dict
import time

ensg_to_ncbi_df = pd.read_excel('mart_export.xlsx') 
def get_data(file_stream: BytesIO, filename: str) -> pd.DataFrame:
    """
    Reads the uploaded file and returns a Pandas DataFrame.

    :param file_stream: In-memory file object
    :param filename: Name of the uploaded file
    :return: Pandas DataFrame containing the file data
    """
    print(f"Reading file: {filename}")
    df = pd.read_excel(file_stream)
    print(f"{filename} has beeen loaded into memory")
    print(f"Dropping rows after 50 for time purposes..")
    df = df.iloc[:50]
    remove_low_counts(df, 1)
    gene_data = get_gene_info(df)
    normalize_read_counts(df, gene_data)
    get_top_genes(df,df.columns.tolist()[1],20)
    add_gene_columns_to_df(df)
    for index, row in df.iterrows():
        # Process current row
        df.loc[index] = add_gene_info(row)
        time.sleep(0.3333)
    print("Gene data acquired!")
    print("Returning gene data as JSON...")
    return df

def get_local_data(filename: str) -> pd.DataFrame:
    """
    Reads a local Excel file, removes low counts, fetches gene info, normalizes read counts,
    and adds the gene biotype to the DataFrame.

    :param filename: Path to the Excel file
    :return: Processed Pandas DataFrame
    """
    print(f"Reading file: {filename}")
    df = pd.read_excel(filename)
    print(f"{filename} has beeen loaded into memory")
    print(f"Dropping rows after 50 for time purposes..")
    df = df.iloc[:50]
    remove_low_counts(df, 1)
    gene_data = get_gene_info(df)
    normalize_read_counts(df, gene_data)
    get_top_genes(df,df.columns.tolist()[1],20)
    add_gene_columns_to_df(df)
    for index, row in df.iterrows():
        # Process current row
        df.loc[index] = add_gene_info(row)
        time.sleep(0.3333)
    print("Gene data acquired!")
    
    return df

def normalize_read_counts(df: pd.DataFrame, gene_info: Dict[str, Dict[str, float]]) -> None:
    """
    Normalizes read counts based on gene lengths.

    :param df: DataFrame containing gene read counts
    :param gene_info: Dictionary containing gene length information
    """
    if 'Geneid' not in df.columns:
        raise ValueError("Missing 'Geneid' column in DataFrame")
    
    for index, row in df.iterrows():
        gene_id = row['Geneid']
        if gene_id in gene_info:
            gene_length = float(gene_info[gene_id]['end']) - float(gene_info[gene_id]['start']) + 1
            df.loc[index, df.columns[1:]] = row[1:] / gene_length

    
    print("Read counts normalized!")

def remove_low_counts(df: pd.DataFrame, threshold: int) -> None:
    """
    Removes rows where all counts are below the threshold.

    :param df: DataFrame containing gene read counts
    :param threshold: Minimum count threshold
    """
    print(f"Removing low read counts below {threshold}")
    df.drop(df[(df.iloc[:, 1:] <= threshold).all(axis=1)].index, inplace=True)
    print("Low read counts removed!")

def get_gene_info(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Fetches gene information from Ensembl API.

    :param df: DataFrame containing 'Geneid' column
    :return: Dictionary mapping Gene IDs to their genomic positions and other info
    """
    gene_data = {}
    
    if 'Geneid' not in df.columns:
        raise ValueError("Missing 'Geneid' column in DataFrame")
    
    # Counter to limit the number of API calls
    i = 0
    for gene_id in df['Geneid'].unique():
        # If you only want to fetch data for a subset of genes, limit to first 500.
        if i > 500:
            break
        
        # Make sure to replace the URL with one that uses the current gene_id.
        url = f"https://rest.ensembl.org/lookup/id/{gene_id}"
        response = requests.get(url, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            gene_data[gene_id] = response.json()
            print(f"Data for {gene_id} fetched!")
            
            i += 1
            time.sleep(0.065)   
        else:
            print(f"Warning: Failed to fetch data for Gene ID {gene_id}")
    
    return gene_data

def get_top_genes(df, column, num_genes):
    print(f"Ranking the top {num_genes} genes...")
    return df.nlargest(num_genes, column)


def convert_ensg_to_ncbi(ensg_id) -> str:
    print("Converting ENSG ID to NCBI ID...")
    # Load the spreadsheet into a DataFrame
    df = ensg_to_ncbi_df
    # Ensure column names are stripped of leading/trailing spaces
    df.columns = df.columns.str.strip()

    # Filter out rows where "Gene descriptor" is "novel transcript"
    df_filtered = df[df["Gene descriptor"] != "novel transcript"]

    # Create a mapping from ENSG (Gene stable ID) to NCBI Gene ID
    ensg_to_ncbi = df_filtered.set_index("Gene stable ID")["NCBI gene (formerly Entrezgene) ID"].dropna()

    # Return the corresponding NCBI Gene ID for the given ENSG ID (if exists)
    return ensg_to_ncbi.get(ensg_id, "NCBI ID not found")
# Example usage:
# ncbi_id = convert_ensg_to_ncbi("genes_data.xlsx", "ENSG00000209")
# print(ncbi_id)


def fetch_gene_data(ncbi_id):
    '''
    Fetches gene data from NCBI
    :param ncbi_id: a gene's NCBI id
    '''
    url = f"https://api.ncbi.nlm.nih.gov/datasets/v2/gene/id/{ncbi_id}"
    print("Fetching gene data from NCBI...")
    if ncbi_id == "NCBI ID not found":
        print("This gene does not have an NCBI id")
        return {"error": "NNI"} # no ncbi id error
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        return response.json()  # Return JSON response
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
def add_gene_columns_to_df(df):
    """
    Adds predefined gene-related columns to the given dataframe.

    :param df: Pandas DataFrame to which the gene columns will be added
    :return: DataFrame with the new gene-related columns added
    """
    # Define the new columns with default values
    gene_columns = {
        'gene_id': '',
        'symbol': '',
        'description': '',
        'tax_id': '',
        'taxname': '',
        'common_name': '',
        'type': 'UNKNOWN',
        'rna_type': 'rna_UNKNOWN',
        'orientation': 'none',
        'reference_standards': [],
        'genomic_regions': [],
        'chromosomes': [],
        'nomenclature_authority': {},
        'swiss_prot_accessions': [],
        'ensembl_gene_ids': [],
        'omim_ids': [],
        'synonyms': [],
        'replaced_gene_id': '',
        'annotations': [],
        'transcript_count': 0,
        'protein_count': 0,
        'transcript_type_counts': [],
        'gene_groups': [],
        'summary': [],
        'gene_ontology': {},
        'locus_tag': '',
    }

    # Add the new columns to the existing DataFrame with the default values
    for col, value in gene_columns.items():
        df[col] = value

def add_gene_info(row):
    ensg_id = row['Geneid']
    ncbi_id = convert_ensg_to_ncbi(ensg_id)
    gene_data = fetch_gene_data(ncbi_id)
     # Extract gene information from the report
    gene_info = gene_data.get('gene', {})

    # Define the gene columns to be updated from the report
    gene_columns = {
        'gene_id': gene_info.get('gene_id', ''),
        'symbol': gene_info.get('symbol', ''),
        'description': gene_info.get('description', ''),
        'tax_id': gene_info.get('tax_id', ''),
        'taxname': gene_info.get('taxname', ''),
        'common_name': gene_info.get('common_name', ''),
        'type': gene_info.get('type', 'UNKNOWN'),
        'rna_type': gene_info.get('rna_type', 'rna_UNKNOWN'),
        'orientation': gene_info.get('orientation', 'none'),
        'reference_standards': gene_info.get('reference_standards', []),
        'genomic_regions': gene_info.get('genomic_regions', []),
        'chromosomes': gene_info.get('chromosomes', []),
        'nomenclature_authority': gene_info.get('nomenclature_authority', {}),
        'swiss_prot_accessions': gene_info.get('swiss_prot_accessions', []),
        'ensembl_gene_ids': gene_info.get('ensembl_gene_ids', []),
        'omim_ids': gene_info.get('omim_ids', []),
        'synonyms': gene_info.get('synonyms', []),
        'replaced_gene_id': gene_info.get('replaced_gene_id', ''),
        'annotations': gene_info.get('annotations', []),
        'transcript_count': gene_info.get('transcript_count', 0),
        'protein_count': gene_info.get('protein_count', 0),
        'transcript_type_counts': gene_info.get('transcript_type_counts', []),
        'gene_groups': gene_info.get('gene_groups', []),
        'summary': gene_info.get('summary', []),
        'gene_ontology': gene_info.get('gene_ontology', {}),
        'locus_tag': gene_info.get('locus_tag', ''),
    }

    # Update the row with the gene data from the report
    for col, value in gene_columns.items():
        row[col] = value

    return row


    