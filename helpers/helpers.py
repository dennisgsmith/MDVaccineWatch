import pandas as pd

# Clean up the data in pandas
def clean_df(df):
    '''clean pandas df and return transformed dataframe'''
    # Clean and replace the file locally as backup
    try:
        # Drop daily columns
        df.drop(
            columns=["FirstDoseDaily", "SecondDoseDaily", "SingleDoseDaily"],
            inplace=True,
        )
    except:
        pass

    try:
        # Strip trailing whitespace from end of County names
        df["County"] = df["County"].str.rstrip()

        df.fillna(0, inplace=True)  # Fill missing entries with 0

        # Compute and store aggregates in df to save on load time
        # Get county total of at least 1 vaccination and full vaccinations
        df["AtLeastOneVaccine"] = (
            df["FirstDoseCumulative"] + df["SingleDoseCumulative"]
        )
        df["FullyVaccinated"] = df["SecondDoseCumulative"] + df["SingleDoseCumulative"]
        pass
    except:
        print('ERROR helpers.clean_csv: Could not clean file')
        return

    try:
        # all cols to lowercase for postgres to play nicely
        df.columns = [x.lower() for x in df.columns]
        return df
    except:
        print("Counld not convert columns to lowercase")
        return
