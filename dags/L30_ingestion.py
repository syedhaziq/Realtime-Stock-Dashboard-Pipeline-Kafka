from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline.pipeline import l30d_pipeline

default_args = {
    'owner': 'haziq',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


with DAG(
    dag_id='L30d_pipeline',
    default_args=default_args,
    description='pipeline for L30d stock data',
    schedule_interval='0 4 * * *',  
    start_date=datetime(2023, 12, 23),    
    catchup=False,                        
    tags=['stock', 'realtime', 'L30d'],           
) as dag:


    def push_success_string(**kwargs):
    
        ti = kwargs['ti']  
        success_string = "success"
        ti.xcom_push(key='task1', value=success_string)
 

    task1 = PythonOperator(
        task_id='L30d_pipeline',
        python_callable=l30d_pipeline,
        op_args=['L30d','AAPL'],
        provide_context=True
    )
    
    task2 = PythonOperator(
        task_id='push_success_string',
        python_callable=push_success_string,
        provide_context=True
    )
    

    task1 >> task2

