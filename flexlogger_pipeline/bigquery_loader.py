import pandas as pd
import os
from google.cloud import bigquery

def upload_to_bigquery(df, table_id):
    client = bigquery.Client()

    TABLE_ID = 'our-lamp-495415-f5.flexlogger_data.temperature'

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True,
    )

    job = client.load_table_from_dataframe(
        df,
        TABLE_ID,
        job_config=job_config,
    )

    job.result()  # Wait for the job to complete
    print(f"Uplaoded {len(df)} rows to {TABLE_ID}")

#below is test to see if the client connection works after: gcloud auth application-default login --no-browser
# client = bigquery.Client()

# query = "SELECT * FROM `our-lamp-495415-f5.flexlogger_data.temperature`"

# query_job = client.query(query)

# for row in query_job:
#     print(row)