from extraction_repo_overview import *
from data_transformation import *
from load_data import *

def main():
    print("GitHub Tensorflow ETL Pipeline Initiated!")

    try:
        print("\nExtracting Tensorflow data...")
        extract_repo_data()
        verify_upload()

        print("\nTransformastion begining...")
        processed_data = process_data()

        print("\nLoading transformed data...")
        load_snapshot(processed_data)

        return True
    
    except Exception as e:
        print(f"ETL process failed, details: {e}")

        return False

if __name__ == "__main__":
    main()