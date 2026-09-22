import sqlite3 as sql


def create_database(db_name='universal_medical.db'):
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

    conn.commit()

    return conn


def insert_data(final_df, conn):
    final_df.to_sql(
        'universal_patients',
        conn,
        if_exists='append',
        index=False
    )

    conn.commit()