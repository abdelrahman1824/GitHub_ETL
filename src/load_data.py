import psycopg
from dotenv import load_dotenv

def load_snapshot(snapshot):

    insert_statement = """"
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
    """

    