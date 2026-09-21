import json
import os
import sqlite3 as sql
import pandas as pd

COLUMN_MAPPING = {
    'account': 'patient_account_id',
    'patient first': 'patient_first',
    'patient last': 'patient_last',
    'pt_fname': 'patient_first',
    'first name': 'patient_first',
    'pt_lname': 'patient_last',
    'last name': 'patient_last',
    'birth date': 'dob',
    'dob': 'dob',
    'sex': 'sex',
    'zip code': 'zip_code',
    'billed amt': 'billed_amt',
    'charge': 'billed_amt',
    'bill_amount': 'billed_amt',
    'paid': 'paid',
    'due': 'due',
    'date of service': 'date_of_service',
    'dos': 'date_of_service',
}

STANDARD_PATIENT_COLS = [
    'patient_account_id',
    'patient_first',
    'patient_last',
    'sex',
    'dob',
    'zip_code',
    'billed_amt',
    'paid',
    'due',
    'date_of_service',
]


def process_and_ingest(file_path, db_name='universal_medical.db'):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

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

    known_cols = [col for col in df.columns if col in STANDARD_PATIENT_COLS]
    unknown_cols = [
        col for col in df.columns if col not in STANDARD_PATIENT_COLS
    ]

    if unknown_cols:
        df['extra_attributes'] = df[unknown_cols].to_dict(orient='records')
        df['extra_attributes'] = df['extra_attributes'].apply(json.dumps)
    else:
        df['extra_attributes'] = '{}'

    final_cols = known_cols + ['extra_attributes']
    final_df = df[final_cols]

    conn = sql.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS universal_patients (
        patient_account_id INTEGER,
        patient_first TEXT,
        patient_last TEXT,
        sex TEXT,
        dob TEXT,
        zip_code TEXT,
        billed_amt REAL,
        paid REAL,
        due REAL,
        date_of_service TEXT,
        extra_attributes TEXT
    );
    """)

    final_df.to_sql(
        'universal_patients', conn, if_exists='append', index=False
    )
    conn.commit()
    conn.close()

    print(f"Successfully ingested: {file_path}")


if __name__ == '__main__':
    input_folder = 'input_files'

    if os.path.exists(input_folder):
        files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
        if not files:
            print(f"No CSV files found in '{input_folder}'.")
        else:
            for file_name in files:
                full_path = os.path.join(input_folder, file_name)
                process_and_ingest(full_path)
            print('All files processed successfully.')
    else:
        print(f"Directory '{input_folder}' does not exist.")