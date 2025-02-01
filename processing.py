import pandas as pd
from io import BytesIO
import requests
from typing import Dict
import time
def get_data(file_stream: BytesIO, filename: str) -> pd.DataFrame:
    """
    Reads the uploaded file and returns a Pandas DataFrame.

    :param file_stream: In-memory file object
    :param filename: Name of the uploaded file
    :return: Pandas DataFrame containing the file data
    """
    try:
        if filename.endswith('.csv'):
            return pd.read_csv(file_stream)
        elif filename.endswith('.tsv'):
            return pd.read_csv(file_stream, sep='\t')
        elif filename.endswith(('.xls', '.xlsx')):
            return pd.read_excel(file_stream)
        else:
            raise ValueError("Unsupported file format")
    except Exception as e:
        raise ValueError(f"Error processing file: {e}")

def get_local_data(filename: str) -> pd.DataFrame:
    """
    Reads a local Excel file, removes low counts, fetches gene info, normalizes read counts,
    and adds the gene biotype to the DataFrame.

    :param filename: Path to the Excel file
    :return: Processed Pandas DataFrame
    """
    print(f"Reading file: {filename}")
    df = pd.read_excel(filename)
    
    remove_low_counts(df, 1)
    gene_data = get_gene_info(df)
    normalize_read_counts(df, gene_data)
    add_gene_type(df, gene_data)
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
            df.iloc[index, 1:] = row[1:] / gene_length
    
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

def add_gene_type(df: pd.DataFrame, gene_data: Dict[str, Dict[str, float]]) -> None:
    """
    Adds a 'biotype' column to the DataFrame based on the 'biotype' property from gene_data.

    :param df: DataFrame containing gene information with a 'Geneid' column.
    :param gene_data: Dictionary mapping Gene IDs to their detailed info, including 'biotype'.
    """
    if 'Geneid' not in df.columns:
        raise ValueError("Missing 'Geneid' column in DataFrame")
    
    # Create the new 'biotype' column by looking up each gene's 'biotype' from gene_data.
    df['biotype'] = df['Geneid'].apply(lambda gene_id: gene_data.get(gene_id, {}).get('biotype'))
    print("Biotype column added!")
