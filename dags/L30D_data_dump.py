from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline.pipeline import l30d_data_dump_pipeline

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
    dag_id='l30d_dump_pipeline',
    default_args=default_args,
    description='pipeline for l30d stock data dump',
    schedule_interval='05 4 * * *', 
    start_date=datetime(2023, 12, 23),   
    catchup=False,                      
    tags=['stock', 'realtime', 'dump', 'L30d'],           
) as dag:

    def check_status(**kwargs):
        task_status = kwargs['ti'].xcom_pull(
            key='task1',
            task_ids='push_success_string',
            dag_id='L30d_pipeline',
            include_prior_dates=True
        )
        if task_status:
            print(f'Retrieved status: {task_status}')
            if task_status == 'success':
                print('Task 1 was successful, proceeding with task 2')
                return True
            else:
                raise Exception('Task 1 did not return success status')
        else:
            raise Exception('Could not retrieve status from previous DAG')
 

    status = PythonOperator(
        task_id='check_status',
        python_callable=check_status,
        provide_context=True
    )

    task1 = PythonOperator(
        task_id='l30_dump_pipeline',
        python_callable=l30d_data_dump_pipeline,
        op_args=['L30d',"kafka:29092"],
        provide_context=True
    )


    status >> task1