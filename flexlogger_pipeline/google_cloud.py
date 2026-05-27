from google.cloud import bigquery

client = bigquery.Client()

query = "SELECT * FROM `our-lamp-495415-f5.flexlogger_data.temperature`"

query_job = client.query(query)

for row in query_job:
    print(row)