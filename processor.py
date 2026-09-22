import json
import os
import pandas as pd

from config import COLUMN_MAPPING, STANDARD_PATIENT_COLS


def process_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return None

    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip().str.lower()

    if (
        'patient first' in df.columns
        and 'guarantor last' in df.columns
        and not df.empty
    ):
        first_val = str(df['patient first'].iloc[0]).strip()
        guar_val = str(df['guarantor last'].iloc[0]).strip()

        if first_val == guar_val:
            df['patient first'], df['patient last'] = (
                df['patient last'],
                df['patient first'],
            )

    df = df.rename(columns=COLUMN_MAPPING)

    known_cols = [
        col for col in df.columns
        if col in STANDARD_PATIENT_COLS
    ]

    unknown_cols = [
        col for col in df.columns
        if col not in STANDARD_PATIENT_COLS
    ]

    if unknown_cols:
        df['extra_attributes'] = (
            df[unknown_cols].to_dict(orient='records')
        )

        df['extra_attributes'] = (
            df['extra_attributes'].apply(json.dumps)
        )
    else:
        df['extra_attributes'] = '{}'

    final_cols = known_cols + ['extra_attributes']
    final_df = df[final_cols]

    return final_df
