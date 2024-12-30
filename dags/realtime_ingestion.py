from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline.pipeline import realtime_pipeline, l30d_pipeline


# Default arguments for the DAG
default_args = {
    'owner': 'haziq',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    dag_id='realtime_pipeline',
    default_args=default_args,
    description='realtime pipeline for stock data',
    schedule_interval='0 09 * * *',  # Runs daily
    start_date=datetime(2023, 12, 23),    # Set a valid start date
    catchup=False,                        # Don't backfill missing runs
    tags=['stock', 'realtime'],           # Tags to help organize the DAGs
) as dag:

 

    task1 = PythonOperator(
        task_id='realtime_pipeline',
        python_callable=realtime_pipeline,
        op_args=['stock','AAPL'],
    )
    

    task1
    
    



