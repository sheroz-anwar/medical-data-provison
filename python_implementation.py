import csv
import hashlib
import json
import os
from typing import Optional

import xlrd
import db


INPUT_FOLDER = "input_files"
OUTPUT_FILE = "processed_patients.csv"


COLUMN_ALIASES = {
    "patient_account_id": ["account", "account id", "patient account id"],
    "patient_first": ["patient first", "first name", "fname", "pt fname", "patient fname"],
    "patient_last": ["patient last", "last name", "lname", "pt lname", "patient lname"],
    "sex": ["sex", "gender", "m/f", "mf"],
    "dob": ["birth date", "date of birth", "dob"],
    "ssn": ["ssn", "social security", "social security number", "soc sec"],
    "patient_address_1": [
        "address", "address 1", "address1", "patient address",
        "patient address 1", "patient address1", "street address", "street"
    ],
    "patient_address_2": [
        "address 2", "address2", "patient address 2",
        "patient address2", "apt", "apartment", "unit", "suite"
    ],
    "patient_city": ["city", "patient city"],
    "patient_state": ["state", "patient state", "st"],
    "zip_code": ["zip", "zipcode", "zip code", "postal code"],
    "billed_amt": ["billed amt", "charge", "bill amount", "bill_amount"],
    "paid": ["paid", "amount paid"],
    "due": ["due", "amount due", "balance due"],
    "date_of_service": ["date of service", "dos", "service date"],
}


STANDARD_COLUMNS = list(COLUMN_ALIASES.keys())


def normalize_column_name(name: str) -> str:
    name = name.strip().lower()
    name = name.replace("_", " ")
    name = name.replace("-", " ")
    name = name.replace(".", " ")

    return " ".join(name.split())


def build_column_mapping() -> dict[str, str]:
    mapping = {}

    for standard_column, aliases in COLUMN_ALIASES.items():
        mapping[normalize_column_name(standard_column)] = standard_column

        for alias in aliases:
            mapping[normalize_column_name(alias)] = standard_column

    return mapping


COLUMN_MAPPING = build_column_mapping()


def make_unique_headers(headers: list[str]) -> list[str]:
    counts = {}
    unique_headers = []

    for header in headers:
        count = counts.get(header, 0) + 1
        counts[header] = count

        if count == 1:
            unique_headers.append(header)
        else:
            unique_headers.append(
                f"{header}__duplicate_{count}"
            )

    return unique_headers


def calculate_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def read_csv_file(
    file_path: str,
) -> tuple[list[str], list[dict[str, str]]]:

    with open(
        file_path,
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        rows = list(csv.reader(file))

    if not rows:
        return [], []

    headers = make_unique_headers(rows[0])
    data = []

    for values in rows[1:]:
        row = {
            header: values[index] if index < len(values) else ""
            for index, header in enumerate(headers)
        }
        data.append(row)

    return headers, data


def find_xls_header_row(sheet) -> Optional[int]:
    for row_index in range(sheet.nrows):
        matches = 0

        for column_index in range(sheet.ncols):
            value = sheet.cell_value(
                row_index,
                column_index,
            )

            if isinstance(value, str):
                normalized = normalize_column_name(value)

                if normalized in COLUMN_MAPPING:
                    matches += 1

        if matches >= 2:
            return row_index

    return None


def read_xls_file(
    file_path: str,
) -> tuple[list[str], list[dict[str, str]]]:

    workbook = xlrd.open_workbook(file_path)
    sheet = workbook.sheet_by_index(0)

    header_row = find_xls_header_row(sheet)

    if header_row is None:
        print(f"No header row found in '{file_path}'.")
        return [], []

    raw_headers = [
        str(
            sheet.cell_value(header_row, column)
        ).strip()
        for column in range(sheet.ncols)
    ]

    headers = make_unique_headers(raw_headers)
    data = []

    for row_index in range(header_row + 1, sheet.nrows):
        row = {
            header: str(
                sheet.cell_value(row_index, column_index)
            )
            for column_index, header in enumerate(headers)
        }
        data.append(row)

    return headers, data


def read_file(
    file_path: str,
) -> tuple[list[str], list[dict[str, str]]]:

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".csv":
        return read_csv_file(file_path)

    if extension == ".xls":
        return read_xls_file(file_path)

    return [], []


def process_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:

    processed_rows = []

    for row in rows:
        cleaned_row = {}
        extra_attributes = {}

        for raw_column, value in row.items():

            if "__duplicate_" in raw_column:
                extra_attributes[raw_column] = value
                continue

            standard_column = COLUMN_MAPPING.get(
                normalize_column_name(raw_column)
            )

            if standard_column:
                cleaned_row[standard_column] = value
            else:
                extra_attributes[raw_column] = value

        for column in STANDARD_COLUMNS:
            cleaned_row.setdefault(column, "")

        cleaned_row["extra_attributes"] = json.dumps(
            extra_attributes
        )

        processed_rows.append(cleaned_row)

    return processed_rows


def process_file(
    file_path: str,
) -> Optional[list[dict[str, str]]]:

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None

    headers, rows = read_file(file_path)

    if not headers or not rows:
        return []

    return process_rows(rows)


def process_all_files(
    input_folder: str,
) -> list[dict[str, str]]:

    if not os.path.exists(input_folder):
        print(f"Directory does not exist: {input_folder}")
        return []

    files = [
        file_name
        for file_name in os.listdir(input_folder)
        if file_name.lower().endswith((".csv", ".xls"))
    ]

    all_rows = []

    for file_name in files:
        file_path = os.path.join(input_folder, file_name)
        file_hash = calculate_file_hash(file_path)

        if db.is_file_processed(file_hash):
            print(f"Skipping already processed: {file_name}")
            continue

        print(f"Processing: {file_name}")

        rows = process_file(file_path)

        if not rows:
            print(f"No data found: {file_name}")
            continue

        all_rows.extend(rows)

        db.mark_file_processed(
            file_name,
            file_hash,
        )

    return all_rows


def write_processed_data(
    output_file: str,
    rows: list[dict[str, str]],
) -> None:

    fieldnames = STANDARD_COLUMNS + ["extra_attributes"]

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    conn = db.create_database()

    try:
        rows = process_all_files(INPUT_FOLDER)

        if not rows:
            print("No new files to process.")
            return

        write_processed_data(
            OUTPUT_FILE,
            rows,
        )

        db.insert_data(
            rows,
            conn,
        )

        print("All new files processed successfully.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()