# take data and check if its slx, tsv, csv, then turn it into a pandas dataframe
# then call ensembl or whatever to get gene lengths, then normalize the data
# from there we can do whatever is in excalidraw i frogot already 

# use whatever functions im gonna be focusing on frontend

import pandas as pd
from io import BytesIO

def get_data(file_stream: BytesIO, filename: str) -> int:
    """
    Reads the uploaded file and returns the number of rows.

    :param file_stream: In-memory file object
    :param filename: Name of the uploaded file
    :return: Number of rows in the file
    """
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file_stream)
        elif filename.endswith('.tsv'):
            df = pd.read_csv(file_stream, sep='\t')
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_stream)
        else:
            raise ValueError("Unsupported file format")

        return len(df)  # Return number of rows
    except Exception as e:
        raise ValueError(f"Error processing file: {e}")

