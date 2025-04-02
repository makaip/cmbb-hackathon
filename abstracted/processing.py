from abstracted.readcount import ReadCountProcessor
from abstracted.geneconverter import convert_dataframe_parallel
from abstracted.geneprocessor import GeneDataProcessor

import pandas as pd

def process_data(df: pd.DataFrame, max_rows: int = 20, gene_limit: int = 100, max_workers: int = 100) -> pd.DataFrame:
    df = df[df['23Q'] > 1]
    df.reset_index(drop=True, inplace=True)

    processor = ReadCountProcessor(df, gene_limit=gene_limit)
    normalized_df = processor.normalize_read_counts(max_workers=max_workers)

    df_with_ncbi = convert_dataframe_parallel(normalized_df, row_limit=gene_limit, max_workers=max_workers)
    df_with_ncbi = df_with_ncbi[pd.to_numeric(df_with_ncbi['NCBI_ID'], errors='coerce').notnull()]
    print("df with ncbi complete!")

    df_with_ncbi_sorted = df_with_ncbi.sort_values(by='Normalized_Read_Counts', ascending=False)
    df_with_ncbi_sorted = df_with_ncbi_sorted.iloc[:max_rows]
    print("sorting complete")

    df_with_gene_columns = GeneDataProcessor.add_gene_columns(df_with_ncbi_sorted)
    df_final = GeneDataProcessor.enrich_gene_data(df_with_gene_columns)
    print("gene data enriched!")

    return df_final
