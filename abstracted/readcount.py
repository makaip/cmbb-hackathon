import pandas as pd
import requests
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class ReadCountProcessor:
    """
    A class to process and normalize read counts from a Pandas DataFrame.
    """
    ENSEMBL_API_URL = "https://rest.ensembl.org/lookup/id/{}"

    def __init__(self, dataframe: pd.DataFrame, gene_limit: Optional[int] = None) -> None:
        """
        Initializes the processor with a DataFrame and an optional gene limit.

        :param dataframe: Pandas DataFrame with ENSG IDs and read counts.
        :param gene_limit: Optional limit on the number of genes to process.
        """
        self._validate_dataframe(dataframe)
        self.dataframe = dataframe.copy()
        self.gene_limit = gene_limit

    def _validate_dataframe(self, dataframe: pd.DataFrame) -> None:
        """
        Validates if the dataframe has the correct structure.

        :param dataframe: Pandas DataFrame to validate.
        :raises ValueError: If the dataframe does not meet expectations.
        """
        if dataframe.shape[1] < 2:
            raise ValueError("DataFrame must have at least two columns (ENSG IDs and read counts).")
        if not isinstance(dataframe.iloc[:, 1], pd.Series):
            raise TypeError("The second column should be a Pandas Series containing read counts.")

    def _fetch_gene_count(self, gene_id: str) -> int:
        """
        Fetches the expected gene count (or gene length) from the Ensembl database.

        :param gene_id: The Ensembl gene ID.
        :return: The expected gene count (default to 1 if unavailable).
        """
        try:
            response = requests.get(
                self.ENSEMBL_API_URL.format(gene_id),
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                print(f"Successfully fetched data for {gene_id}")
                return data.get("length", 1)
        except requests.RequestException:
            print(f"Failed to fetch data for {gene_id}")
        return 1  # Default value if API request fails

    def fetch_all_gene_counts(self, max_workers: int) -> Dict[str, int]:
        """
        Fetches gene counts for all unique gene IDs in the dataframe concurrently, 
        limiting to `gene_limit` if specified.

        :param max_workers: Number of threads to use for concurrent requests.
        :return: Dictionary mapping gene_id to gene count.
        """
        gene_ids = self.dataframe.iloc[:, 0].unique()
        if self.gene_limit:
            gene_ids = gene_ids[:self.gene_limit]
        
        gene_counts: Dict[str, int] = {}

        print("Fetching gene counts from Ensembl...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_gene = {executor.submit(self._fetch_gene_count, gene_id): gene_id for gene_id in gene_ids}

            for future in as_completed(future_to_gene):
                gene_id = future_to_gene[future]
                try:
                    gene_counts[gene_id] = future.result()
                except Exception:
                    gene_counts[gene_id] = 1
        print("Finished fetching all gene counts.")
        return gene_counts

    def normalize_read_counts(self, max_workers: int = 10) -> pd.DataFrame:
        """
        Normalizes the read counts by dividing by the expected gene count from Ensembl.

        :param max_workers: Number of threads to use for fetching gene counts.
        :return: Pandas DataFrame with ENSG IDs and normalized read counts.
        """
        gene_counts = self.fetch_all_gene_counts(max_workers=max_workers)

        # Create a new column with normalized read counts.
        self.dataframe["Normalized_Read_Counts"] = self.dataframe.apply(
            lambda row: row.iloc[1] / gene_counts.get(row.iloc[0], 1),
            axis=1
        )
        return self.dataframe

    def get_processed_data(self) -> pd.DataFrame:
        """
        Returns the processed dataframe.

        :return: Pandas DataFrame with ENSG IDs and read counts.
        """
        return self.dataframe
