# take data and check if its slx, tsv, csv, then turn it into a pandas dataframe
# then call ensembl or whatever to get gene lengths, then normalize the data
# from there we can do whatever is in excalidraw i frogot already 

# use whatever functions im gonna be focusing on frontend

import pandas as pd
from io import BytesIO
from gprofiler import GProfiler
import requests
def get_data(file_stream: BytesIO, filename: str) -> pd.DataFrame:
    """
    Reads the uploaded file and returns the number of rows.

    :param file_stream: In-memory file object
    :param filename: Name of the uploaded file
    :return: Number of rows in the file
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


def normalize_read_counts(df: pd.DataFrame, r: requests.Request) -> None:
    columns = df.columns.tolist()
    del columns[0]
    for i in range(len(df)):
        for column in columns:
            df[column][i] = df[column][i] / (float(data['end']) - float(data['start']) + 1)
    print("Read counts normalized!")
    return 

def remove_low_counts(df: pd.DataFrame,num: int) -> None:
    columns = df.columns.tolist()
    del columns[0]
    for i in range(len(df)):
        if i > len(df):
            break
        if (df.iloc[i] <= num).all():
            df = df.drop(i)
            i -= 1
    print("Low read counts removed!")

def get_gene_info(df: pd.DataFrame) -> pd.DataFrame:
    gp = GProfiler(
        return_dataframe=True
    )
    return gp.profile(organism="hsapiens", query=list(df["ensg_ids"]))
