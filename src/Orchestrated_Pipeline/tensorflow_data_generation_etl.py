
from extraction_repo_overview_orch import *
from data_transformation_orch import *
from load_data_orch import *
from prefect import flow, task, get_run_logger

@flow(name = "github_etl_pipeline")
def main():
    logger = get_run_logger()

    logger.info("GitHub Tensorflow ETL Pipeline Initiated!")

    try:
        #Extraction Function
        extract_repo_data()

        #Verification of Upload
        verify_upload()

        #Filtering data
        processed_data = process_data()

        #Loading filtered data to database
        load_snapshot(processed_data)

        return True
    
    except Exception as e:
        logger.error(f"ETL process failed, details: {e}")

        return False

if __name__ == "__main__":
   etl_pipeline = main()

      