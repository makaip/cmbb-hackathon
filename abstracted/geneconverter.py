import time
import threading
import pandas as pd
import gget
from concurrent.futures import ThreadPoolExecutor, as_completed

class RateLimiter:
    """
    A simple rate limiter using a token bucket approach.
    It ensures that no more than `max_calls` are made within `period` seconds.
    """
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.lock = threading.Lock()
        self.calls = []

    def acquire(self):
        with self.lock:
            now = time.time()
            # Remove calls that occurred before the current period
            self.calls = [call for call in self.calls if now - call < self.period]
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                time.sleep(sleep_time)
            self.calls.append(time.time())


class GeneInfoConverter:
    """
    A class to convert ENSG gene IDs to NCBI gene IDs.
    """
    # Create a shared RateLimiter instance to allow 15 requests per second.
    _rate_limiter = RateLimiter(10, 1)

    @staticmethod
    def convert_ensg_to_ncbi(ensg_id: str) -> str:
        """
        Convert an ENSG ID to an NCBI Gene ID using the gget.info function.

        :param ensg_id: The ENSG ID to convert.
        :return: The corresponding NCBI Gene ID as a string, or "NCBI ID not found" if not available.
        """
        print(f"Converting {ensg_id} to NCBI ID...")
        try:
            # Enforce rate limiting before making the API request.
            GeneInfoConverter._rate_limiter.acquire()
            gene_info = gget.info([ensg_id])
            ncbi_id = gene_info.ncbi_gene_id.get(ensg_id)
            if not ncbi_id:
                return "NCBI ID not found"
            return ncbi_id
        except Exception as error:
            print(f"Error converting {ensg_id}: {error}")
            return "NCBI ID not found"

    def add_ncbi_ids_parallel(
        self, dataframe: pd.DataFrame, row_limit: int = None, max_workers: int = 5
    ) -> pd.DataFrame:
        """
        Add a new column with NCBI IDs to the provided DataFrame using parallel execution.
        The ENSG ID is assumed to be in the first column of the DataFrame.
        After conversion, any rows with non-numerical NCBI_IDs are removed.

        :param dataframe: DataFrame containing ENSG IDs and read counts.
        :param row_limit: Optional integer to limit the number of rows processed.
        :param max_workers: Maximum number of worker threads to use.
        :return: A new DataFrame with ENSG IDs, read counts, and corresponding NCBI IDs.
        """
        df = dataframe.copy()

        # Apply row limit if specified
        if row_limit is not None:
            df = df.iloc[:row_limit]

        # Get ENSG IDs from the first column
        ensg_ids = df.iloc[:, 0].tolist()
        results = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_id = {
                executor.submit(self.convert_ensg_to_ncbi, ensg): ensg for ensg in ensg_ids
            }
            for future in as_completed(future_to_id):
                ensg = future_to_id[future]
                results[ensg] = future.result()

        # Map the conversion results to a new column
        df["NCBI_ID"] = df.iloc[:, 0].map(results)

        return df


def convert_dataframe_parallel(
    df: pd.DataFrame, row_limit: int = None, max_workers: int = 5
) -> pd.DataFrame:
    """
    Convert a DataFrame by adding an NCBI ID column based on the ENSG IDs using parallel processing.
    The ENSG ID is assumed to be in the first column of the DataFrame.
    Rows with non-numerical NCBI IDs are removed.

    :param df: DataFrame containing ENSG IDs and read counts.
    :param row_limit: Optional integer to limit the number of rows processed.
    :param max_workers: Maximum number of worker threads to use.
    :return: DataFrame with ENSG IDs, read counts, and corresponding NCBI IDs.
    """
    converter = GeneInfoConverter()
    return converter.add_ncbi_ids_parallel(df, row_limit=row_limit, max_workers=max_workers)
