import os

from processor import process_file
from database import create_database, insert_data


input_folder = 'input_files'

if os.path.exists(input_folder):

    files = [
        f for f in os.listdir(input_folder)
        if f.endswith('.csv')
    ]

    if not files:
        print(f"No CSV files found in '{input_folder}'.")

    else:
        conn = create_database()

        for file_name in files:

            full_path = os.path.join(input_folder, file_name)

            final_df = process_file(full_path)

            if final_df is not None:
                insert_data(final_df, conn)

        conn.close()

        print('All files processed successfully.')

else:
    print(f"Directory '{input_folder}' does not exist.")