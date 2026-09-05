# GitHub_ETL
I'm a total BEGINNER in the field of Data Engineering :) This project is to get a hands-on experience on the basics of Data Engineering, how to handle External APIs, how to create Python scripts for Data Extraction and Transformation, How to use SQL and PostgreSQL for data manipulation and storage. Last but not least how to build a fully automated ETL pipeline that can handle real-time changing data and can Extract, Load and Transform data from GitHub Tensorflow repository into our local desktop PostgreSQL. This project will fall under the title Data Storage and Orchestration, your remarks and comments would be very much appreciated as I might (most propably will) need your tips and remarks to progress more in the project.
The project will have 4 phases:
Phase 1: Raw Data Extraction from GitHub to AWS S3 
Phase 2: Data Transformation and Processing using Python (Pandas/PySpark)
Phase 3: Load processed data into PostgreSQL
Phase 4: Orchestrate the entire pipeline using Apache Airflow

Updates in the README file will be documented, stay tuned!

# This is a change to test syncing of Local repo and GitHub repo (main branch)

# This another change for cross validation between Local and GitHub

# Phase 1
15/04/2026: Phase 1.1 is now complete, a script is ready for extracting raw data from tensorflow_tensorflow repo and stored in a json file, the script also handles errors for anything related to API requests and authentication and handles any data serialization, file and directory errors. The script includes the following functions:
Configuration => Loads the GitHub Token that is used for requests authentication, this function handles errors of the environmental variable GITHUB_TOKEN is not found or readable by python.

Request setup => This function is mainly responsible for setting-up the request parameters, fo our case we are only using headers for proper identification and authorization for our request.

Data Extraction => This is the function responsiple for getting the data from our endpoint repo, it handles errors like timeout so the request doesn't get stuck if we can't retrieve our data for any reason and it handles response errors so we know whether our data retrieval is successfull or not.

JSON Data snapshots => Dumping our JSON extraction snapshot into an S3 Bucket

# Phase 2
02/09/2026: Data has been extracted, now we have to transform our data in a way so that we can create a dataset for our analytics on the tensorflow repo, this includes choosing the right features that can help in our analytics and maybe we can use feature engineering to create features from our choosen features that can also help in more accurate analysis.

Raw Data Processing => Choosing the keys from the data that shall be used in creating our table that will be later loaded to the database and generated to CSV.


