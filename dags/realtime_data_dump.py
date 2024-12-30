from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline.pipeline import data_dump_pipeline

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
    dag_id='realtime_dump_pipeline',
    default_args=default_args,
    description='realtime pipeline for stock data dump',
    schedule_interval='05 09 * * *',   
    start_date=datetime(2023, 12, 23),    
    catchup=False,                        
    tags=['stock', 'realtime', 'dump'],           
) as dag:

 

    task1 = PythonOperator(
        task_id='realtime_pipeline',
        python_callable=data_dump_pipeline,
        op_args=['stock',"kafka:29092"],
    )


    task1