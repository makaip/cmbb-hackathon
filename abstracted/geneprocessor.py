import pandas as pd
import requests
import json

class GeneDataProcessor:
    """
    A class to handle gene data processing, including sorting and adding gene-related columns.
    """

    DEFAULT_GENE_COLUMNS = {
        'gene_id': '', 'symbol': '', 'description': '', 'tax_id': '', 'taxname': '',
        'common_name': '', 'type': 'UNKNOWN', 'rna_type': 'rna_UNKNOWN', 'orientation': 'none',
        'reference_standards': [], 'genomic_regions': [], 'chromosomes': [],
        'nomenclature_authority': {}, 'swiss_prot_accessions': [], 'ensembl_gene_ids': [],
        'omim_ids': [], 'synonyms': [], 'replaced_gene_id': '', 'annotations': [],
        'transcript_count': 0, 'protein_count': 0, 'transcript_type_counts': [],
        'gene_groups': [], 'summary': [], 'gene_ontology': {}, 'locus_tag': ''
    }

    @staticmethod
    def sort_by_read_counts(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        Sorts the DataFrame by Normalized_Read_Counts in descending order and selects the top N rows.
        :param df: DataFrame containing gene data
        :param top_n: Number of top rows to select (default: 20)
        :return: Sorted and truncated DataFrame
        """

        return df.sort_values(by='Normalized_Read_Counts', ascending=False).iloc[:top_n]

    @classmethod
    def add_gene_columns(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds predefined gene-related columns to the DataFrame.
        :param df: DataFrame to which gene columns will be added
        :return: Updated DataFrame with additional columns
        """

        for col, value in cls.DEFAULT_GENE_COLUMNS.items():
            df[col] = [value] * len(df)

        return df

    @staticmethod
    def fetch_gene_info(ncbi_id: int) -> dict:
        """
        Fetch gene information from the NCBI API.
        :param ncbi_id: NCBI Gene ID
        :return: Dictionary containing gene information
        """
        url = f"https://api.ncbi.nlm.nih.gov/datasets/v2/gene/id/{ncbi_id}"
        print(f"[DEBUG] Fetching data from API for NCBI ID: {ncbi_id}")

        try:
            response = requests.get(url)
            response.raise_for_status()
            json_response = response.json()  # Parse response JSON
            
            # Fix structure: Convert 'reports' from list to dict
            if 'reports' in json_response and isinstance(json_response['reports'], list):
                if len(json_response['reports']) == 1:
                    json_response['reports'] = json_response['reports'][0]  # Convert to dict
                elif len(json_response['reports']) > 1:
                    json_response['reports'] = {k: v for d in json_response['reports'] for k, v in d.items()}

            return json_response  # Now 'reports' is a dictionary

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed: {e}")
            return {}
        except ValueError:
            print("[ERROR] Failed to parse JSON response")
            return {}


    @classmethod
    def enrich_gene_data(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Iterates through the DataFrame, fetching gene information and updating rows accordingly.
        :param df: DataFrame containing gene data
        :return: Updated DataFrame with enriched gene information
        """

        for index, row in df.iterrows():
            gene_info = cls.fetch_gene_info(row['NCBI_ID'])

            if gene_info:
                df.at[index, 'gene_id'] = gene_info['reports']['gene']['gene_id'] if 'gene_id' in gene_info['reports']['gene'] else ''
                df.at[index, 'symbol'] = gene_info['reports']['gene']['symbol'] if 'symbol' in gene_info['reports']['gene'] else ''
                df.at[index, 'description'] = gene_info['reports']['gene']['description'] if 'description' in gene_info['reports']['gene'] else ''
                df.at[index, 'tax_id'] = gene_info['reports']['gene']['tax_id'] if 'tax_id' in gene_info['reports']['gene'] else ''
                df.at[index, 'taxname'] = gene_info['reports']['gene']['taxname'] if 'taxname' in gene_info['reports']['gene'] else ''
                df.at[index, 'common_name'] = gene_info['reports']['gene']['common_name'] if 'common_name' in gene_info['reports']['gene'] else ''
                df.at[index, 'type'] = gene_info['reports']['gene']['type'] if 'type' in gene_info['reports']['gene'] else 'UNKNOWN'
                df.at[index, 'rna_type'] = gene_info['reports']['gene']['rna_type'] if 'rna_type' in gene_info['reports']['gene'] else 'rna_UNKNOWN'
                df.at[index, 'orientation'] = gene_info['reports']['gene']['orientation'] if 'orientation' in gene_info['reports']['gene'] else 'none'

                # Extracting list-based fields
                df.at[index, 'chromosomes'] = gene_info['reports']['gene']['chromosomes'] if 'chromosomes' in gene_info['reports']['gene'] else []
                df.at[index, 'ensembl_gene_ids'] = gene_info['reports']['gene']['ensembl_gene_ids'] if 'ensembl_gene_ids' in gene_info['reports']['gene'] else []
                df.at[index, 'omim_ids'] = gene_info['reports']['gene']['omim_ids'] if 'omim_ids' in gene_info['reports']['gene'] else []
                df.at[index, 'synonyms'] = gene_info['reports']['gene']['synonyms'] if 'synonyms' in gene_info['reports']['gene'] else []
                df.at[index, 'gene_groups'] = gene_info['reports']['gene']['gene_groups'] if 'gene_groups' in gene_info['reports']['gene'] else []
                df.at[index, 'summary'] = gene_info['reports']['gene']['summary'] if 'summary' in gene_info['reports']['gene'] else []

                # Extracting complex/nested structures
                df.at[index, 'genomic_regions'] = gene_info['reports']['gene']['genomic_regions'] if 'genomic_regions' in gene_info['reports']['gene'] else []
                df.at[index, 'annotations'] = gene_info['reports']['gene']['annotations'] if 'annotations' in gene_info['reports']['gene'] else []

                # Handling dictionaries
                df.at[index, 'nomenclature_authority'] = gene_info['reports']['gene']['nomenclature_authority'] if 'nomenclature_authority' in gene_info['reports']['gene'] else {}
                df.at[index, 'gene_ontology'] = gene_info['reports']['gene']['gene_ontology'] if 'gene_ontology' in gene_info['reports']['gene'] else {}

                # Handling numerical fields
                df.at[index, 'transcript_count'] = gene_info['reports']['gene']['transcript_count'] if 'transcript_count' in gene_info['reports']['gene'] else 0
                df.at[index, 'protein_count'] = gene_info['reports']['gene']['protein_count'] if 'protein_count' in gene_info['reports']['gene'] else 0
                df.at[index, 'transcript_type_counts'] = gene_info['reports']['gene']['transcript_type_counts'] if 'transcript_type_counts' in gene_info['reports']['gene'] else []

                # Handling single-value fields
                df.at[index, 'replaced_gene_id'] = gene_info['reports']['gene']['replaced_gene_id'] if 'replaced_gene_id' in gene_info['reports']['gene'] else ''
                df.at[index, 'locus_tag'] = gene_info['reports']['gene']['locus_tag'] if 'locus_tag' in gene_info['reports']['gene'] else ''

        return df

# Example usage:
# df_with_ncbi_sorted = GeneDataProcessor.sort_by_read_counts(df_with_ncbi)
# df_with_gene_columns = GeneDataProcessor.add_gene_columns(df_with_ncbi_sorted)
# df_final = GeneDataProcessor.enrich_gene_data(df_with_gene_columns)
