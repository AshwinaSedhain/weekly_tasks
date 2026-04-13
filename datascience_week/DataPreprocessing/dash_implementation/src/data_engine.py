import polars as pl
import os

# since we have many null values in the some of the column of the data.Instead of data cleaning manually, 
# here we are making the pipeline which cleans the data and pass for the dash creation

#This function loads the CSV file and cleans it before sending to dashboard.
def load_and_clean_data(filename: str) -> pl.DataFrame:
    

    # Finding  the current folder (src)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Building th e path to data file (go up one level → data folder)
    filepath = os.path.join(base_dir, "..", "data", filename)

    # Loading the  CSV file into a table (DataFrame)
    df = pl.read_csv(filepath)

    # Removinh  this column cuz it is not useful for analysis
    if "mp_commoditysource" in df.columns:
        df = df.drop(["mp_commoditysource"])

    # in our data region name is missing,  so replacing  it with "Unknown"
    if "adm1_name" in df.columns:
        df = df.with_columns(
            pl.col("adm1_name").fill_null("Unknown")
        )

    # Converting th e price column into numeric format which will be important for graphss
    df = df.with_columns(
        pl.col("mp_price").cast(pl.Float64)
    )

    # Combinining  year + month into a proper date column for time-series graphs
    df = df.with_columns(
        pl.date("mp_year", "mp_month", 1).alias("date")
    )

    # Removing the  rows where price is missing (we cannot plot them)
    df = df.filter(pl.col("mp_price").is_not_null())

    return df


def get_countries(df: pl.DataFrame):
    """
    This function extracts all unique country names for dropdown.
    """

    # here it takes the  unique country names and sort them alphabetically
    return sorted(df["adm0_name"].unique().to_list())