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

#-------- Creating a function doe retrieving stored repositories --------#
def get_stored_repos(cursor):
    select_repos = """ 
    SELECT github_repo_id, repo_name, owner_id
    FROM analytics.repositories;
    """
    cursor.execute(
        select_repos
    ) 

    stored_repos = {
        row[0]:
        {
            "repo_name": row[1],
            "owner_id": row[2]
        }
        for row in cursor.fetchall()
    }

    print(f"Stored repos: {stored_repos}")

    return stored_repos

#-------- Creat the main data loading function --------#
@task(name = "load_to_database", retries = 2, retry_delay_seconds = 45, cache_policy = None)
@timer
def load_snapshot(processed_data):
    logger = get_run_logger()
    logger.info("Loading data into database...")

    insert_repository = """ 
    INSERT INTO analytics.repositories
    (
    github_repo_id,
    repo_name,
    owner_id,
    created_at
    )
    VALUES
    (
    %(repo_id)s,
    %(name)s,
    %(owner_id)s,
    %(created_at)s
    )
    ON CONFLICT (github_repo_id, repo_name)
    DO NOTHING
    RETURNING repo_id;
    """

    try:
        postgres_connection = create_postgres_connection()

        with postgres_connection as connection:
            with connection.cursor() as cursor:

                #The repo details of the snapshot
                snapshot_repo = {
                    "snapshot_repo_id": processed_data.get("repo_id")
                }

                #The repo id for comparing stored repos
                snapshot_repo_id = snapshot_repo.get("snapshot_repo_id")

                stored_repos = get_stored_repos(cursor)
                
                if not stored_repos:
                    cursor.execute(
                            insert_repository,
                            processed_data
                        )
                    repo_id = cursor.fetchone()[0]
                    logger.info(f"New Repository inserted with the id {repo_id}")
                
                else:
                    if snapshot_repo_id not in stored_repos:
                        print("New repository!")  
                        cursor.execute(
                                insert_repository,
                                processed_data
                            )
                        repo_id = cursor.fetchone()[0]
                        logger.info(f"New Repository inserted with the id {repo_id}")

                    else:
                        get_stored_repo_id = """ 
                        SELECT repo_id 
                        FROM analytics.repositories
                        WHERE github_repo_id = %(snapshot_repo_id)s
                        """
                        cursor.execute(
                            get_stored_repo_id,
                            snapshot_repo
                        )
                        repo_id = cursor.fetchone()[0]
                        logger.info(f"Repository with id {repo_id} already exists!")

                insert_snapshot = """
                INSERT INTO analytics.repository_snapshots
                (
                stargazers_count,
                forks_count,
                open_issues,
                subscribers_count,
                pushed_at,
                updated_at,
                extracted_at,
                s3_object,
                repo_id
                )
                VALUES
                (
                %(stargazers_count)s,
                %(forks_count)s,
                %(open_issues)s,
                %(subscribers_count)s,
                %(pushed_at)s,
                %(updated_at)s,
                %(extracted_at)s,
                %(s3_key)s,
                %(repo_id)s
                )
                RETURNING snapshot_id;
                """
                
                snapshot_parameters = processed_data.copy()
                snapshot_parameters["repo_id"] = repo_id

                cursor.execute(
                    insert_snapshot,
                    snapshot_parameters
                )
                snapshot_id = cursor.fetchone()[0]

                print(f"Data inserted as a new row, with snapshot_id {snapshot_id}")

        return True

    except Exception as e:
        logger.error(f"Couldn't load data to the database, details: {e}")
        
        return False
