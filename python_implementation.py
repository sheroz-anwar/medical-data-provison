import json
import os
import csv

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


def process_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return None

    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        if rows:
            first_row = rows[0]

            if (
                'patient first' in first_row
                and 'guarantor last' in first_row
            ):
                first_val = str(first_row['patient first']).strip()
                guar_val = str(first_row['guarantor last']).strip()

                if first_val == guar_val:
                    first_row['patient first'], first_row['patient last'] = (
                        first_row['patient last'],
                        first_row['patient first']
                    )

        processed_rows = []

        for row in rows:
            cleaned_row = {}

            for column in row:
                clean_column = column.strip().lower()
                standard_column = COLUMN_MAPPING.get(
                    clean_column,
                    clean_column
                )
                cleaned_row[standard_column] = row[column]

            known_cols = []

            for column in cleaned_row:
                if column in STANDARD_PATIENT_COLS:
                    known_cols.append(column)

            unknown_cols = []

            for column in cleaned_row:
                if column not in STANDARD_PATIENT_COLS:
                    unknown_cols.append(column)

            if unknown_cols:
                extra_attributes = {}

                for column in unknown_cols:
                    extra_attributes[column] = cleaned_row[column]

                extra_attributes_json = json.dumps(extra_attributes)
            else:
                extra_attributes_json = '{}'

            final_row = {}

            for column in known_cols:
                final_row[column] = cleaned_row[column]

            final_row['extra_attributes'] = extra_attributes_json
            processed_rows.append(final_row)

        return processed_rows


input_folder = 'input_files'
output_file = 'processed_patients.csv'

if os.path.exists(input_folder):
    files = [
        f for f in os.listdir(input_folder)
        if f.endswith('.csv')
    ]

    if not files:
        print(f"No CSV files found in '{input_folder}'.")
    else:
        all_processed_rows = []

        for file_name in files:
            full_path = os.path.join(input_folder, file_name)
            processed_rows = process_file(full_path)

            if processed_rows is not None:
                all_processed_rows.extend(processed_rows)

        with open(
            output_file,
            'w',
            newline='',
            encoding='utf-8'
        ) as file:
            fieldnames = STANDARD_PATIENT_COLS + ['extra_attributes']

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            writer.writeheader()
            writer.writerows(all_processed_rows)

        print('All files processed successfully.')
else:
    print(f"Directory '{input_folder}' does not exist.")
