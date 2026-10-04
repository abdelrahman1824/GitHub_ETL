import psycopg
from dotenv import load_dotenv
import os
from decorators import *
from prefect import flow, task, get_run_logger

#-------- Creat connection establishing function --------#
def create_postgres_connection():
    load_dotenv()

    #Load PostgreSQL .env variables
    username = os.getenv("POSTGRES_USERNAME")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTRGES_PORT")

    #Establish PostreSQL Connection
    postgres_credentials = {
        "POSTGRES_USERNAME": username,
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": database,
        "POSTGRES_HOST": host,
        "POSTGRES_PORT": port
    }

    missing_values = [name for name, value in postgres_credentials.items()
                      if not value]

    if missing_values:
        raise ValueError("Missing PostgreSQL Credentials"
                         + ",  ".join(missing_values))

    postgres_connection = psycopg.connect(
        host = host,
        port = port,
        dbname = database,
        user = username,
        password = password
    )

    return postgres_connection

#-------- Creat the main data loading function --------#
@task(name = "load_to_database", retries = 2, retry_delay_seconds = 45, cache_policy = None)
@timer
def load_snapshot(processed_data):
    logger = get_run_logger()

    logger.info("Loading data into the Database...")

    insert_statement = """
    INSERT INTO analytics.repository_snapshots
    (
    repository_name,
    repository_id,
    owner_id,
    stargazers_count,
    forks_count,
    open_issues,
    subscribers_count,
    created_at,
    pushed_at,
    updated_at,
    extracted_at,
    s3_object
    )
    VALUES
    (
    %(name)s,
    %(repo_id)s,
    %(owner_id)s,
    %(stargazers_count)s,
    %(forks_count)s,
    %(open_issues)s,
    %(subscribers_count)s,
    %(created_at)s,
    %(pushed_at)s,
    %(updated_at)s,
    %(extracted_at)s,
    %(s3_key)s
    )
    RETURNING snapshot_id
    """

    try:
        logger.info("Establishing postgreSQL connection")
        postgres_connection = create_postgres_connection()

        with postgres_connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    insert_statement,
                    processed_data
                )
                snapshot_id = cursor.fetchone()[0]

                logger.info(f"Data inserted as a new row, with snapshot_id {snapshot_id}")
        return True

    except Exception as e:
        logger.error(f"Couldn't load data to the database, details: {e}")
        
        return False
