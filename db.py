import sqlite3 as sql
from datetime import datetime


DB_FILE = "universal_medical.db"


PATIENT_COLUMNS = {
    "patient_account_id": "INTEGER",
    "patient_first": "TEXT",
    "patient_last": "TEXT",
    "sex": "TEXT",
    "dob": "TEXT",
    "ssn": "TEXT",
    "patient_address_1": "TEXT",
    "patient_address_2": "TEXT",
    "patient_city": "TEXT",
    "patient_state": "TEXT",
    "zip_code": "TEXT",
    "billed_amt": "REAL",
    "paid": "REAL",
    "due": "REAL",
    "date_of_service": "TEXT",
    "extra_attributes": "TEXT",
}


def create_database(db_name: str = DB_FILE):
    conn = sql.connect(db_name)
    cursor = conn.cursor()

    columns = ",\n".join(
        f"{name} {data_type}"
        for name, data_type in PATIENT_COLUMNS.items()
    )

    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS universal_patients (
            {columns}
        );
        """
    )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_files (
            file_name TEXT,
            file_hash TEXT UNIQUE,
            processed_at TEXT
        );
    """)

    cursor.execute(
        "PRAGMA table_info(universal_patients)"
    )

    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    for name, data_type in PATIENT_COLUMNS.items():
        if name not in existing_columns:
            cursor.execute(
                f"""
                ALTER TABLE universal_patients
                ADD COLUMN {name} {data_type}
                """
            )

    conn.commit()

    return conn


def is_file_processed(
    file_hash: str,
    db_name: str = DB_FILE,
) -> bool:

    conn = sql.connect(db_name)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM processed_files
        WHERE file_hash = ?
        LIMIT 1
        """,
        (file_hash,),
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


def mark_file_processed(
    file_name: str,
    file_hash: str,
    db_name: str = DB_FILE,
) -> None:

    conn = sql.connect(db_name)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO processed_files
        (file_name, file_hash, processed_at)
        VALUES (?, ?, ?)
        """,
        (
            file_name,
            file_hash,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    conn.commit()
    conn.close()


def insert_data(rows, conn) -> None:

    columns = list(PATIENT_COLUMNS.keys())

    placeholders = ", ".join("?" for _ in columns)
    column_names = ", ".join(columns)

    values = [
        tuple(row.get(column, "") for column in columns)
        for row in rows
    ]

    conn.executemany(
        f"""
        INSERT INTO universal_patients
        ({column_names})
        VALUES ({placeholders})
        """,
        values,
    )

    conn.commit()