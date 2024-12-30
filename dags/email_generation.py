from datetime import datetime, timedelta
from posixpath import split
from airflow import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook # type: ignore
from airflow.providers.smtp.operators.smtp import EmailOperator
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

default_args = {
    'owner': 'haziq',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def check_stock_price(**kwargs):
    # PostgreSQL connection
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')

    if pg_hook.test_connection():
        print("Connection successful")
    else:
        print("Connection failed")
    
    print("Checking stock price...")
    # Query to get latest stock price
    query = """
        SELECT ticker, "Current Price" as current_price 
        FROM public.live_stock 
        LIMIT 1;
    """
    
    # Execute query and get results
    records = pg_hook.get_records(query)
    

    if not records:
        raise Exception("No price data found in database")
    else:
        print(f"Records: {records}")

    ticker, price = records[0]
    price = price.split('$')[1]
    
    print(f"Ticker: {ticker}, Price: {price}")
    price = float(price)
    threshold = 200  # Set your threshold price
    
    # Push values to XCom
    kwargs['task_instance'].xcom_push(key='current_price', value=price)
    kwargs['task_instance'].xcom_push(key='ticker', value=ticker)
    
    # Check if price is below threshold
    if price < threshold:
        kwargs['task_instance'].xcom_push(key='alert_needed', value=True)
        print(f"Alert: {ticker} price ${price} is below threshold ${threshold}")
    else:
        kwargs['task_instance'].xcom_push(key='alert_needed', value=False)
        print(f"Normal: {ticker} price ${price} is above threshold ${threshold}")

def should_send_email(**kwargs):
    """ShortCircuit function to determine if email should be sent"""
    alert_needed = kwargs['task_instance'].xcom_pull(key='alert_needed')
    return alert_needed

def prepare_email_content(**kwargs):
    """Prepare email content with current price information"""
    current_price = kwargs['task_instance'].xcom_pull(key='current_price')
    ticker = kwargs['task_instance'].xcom_pull(key='ticker')
    threshold = 266
    
    email_content = f"""
    <h2>Stock Price Alert</h2>
    <p>This is an automated alert for your stock price monitoring.</p>
    
    <ul>
        <li>Ticker: {ticker}</li>
        <li>Current Price: ${current_price}</li>
        <li>Threshold Price: ${threshold}</li>
    </ul>
    
    <p>The stock price has fallen below your set threshold.</p>
    <p>Please review and take necessary action.</p>
    
    <small>This is an automated message from your Airflow DAG.</small>
    """
    
    return email_content

# def email_generation(**kwargs):
#     message = kwargs['ti'].xcom_pull(task_ids='prepare_email_content')

#     try:
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login('haziqairflowtesting@gmail.com', 'tpihyzxgcdstfwsq')
#         server.sendmail('haziqairflowtesting@gmail.com', 'haziqairflowtesting@gmail.com', f'Subject: Test\n\n{message}.')
#         server.quit()
#         print("Email sent successfully")
#     except Exception as e:
#         print(f"Error: {e}")

def email_generation(**kwargs):
    message = kwargs['ti'].xcom_pull(task_ids='prepare_email_content')

   # Sender and recipient information
    sender_email = 'sender_email'
    recipient_email = 'recipient_email@gmail.com'
    subject = 'Stock Price Alert'

    # HTML email content
    # ticker = 'AAPL'
    # current_price = 145.67
    # threshold = 150.00

    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the HTML content
    msg.attach(MIMEText(message, 'html'))

    try:
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure connection
        server.login(sender_email, 'app pass')  # Login to your Gmail account

        # Send the email
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()  # Terminate the SMTP session
        print("Email sent successfully")
    except Exception as e:
        print(f"Error: {e}")

with DAG(
    'stock_price_monitor_v1',
    default_args=default_args,
    description='Monitor stock prices and send email alerts when below threshold',
    schedule_interval='*/2 * * * *',  # Run every 30 minutes
    start_date=datetime(2024, 12, 29),
    catchup=False,
    tags=['stocks', 'monitoring', 'alerts'],
) as dag:

    # Task 1: Check stock price
    check_price = PythonOperator(
        task_id='check_stock_price',
        python_callable=check_stock_price,
        provide_context=True,
    )

    # Task 2: Determine if email should be sent
    email_check = ShortCircuitOperator(
        task_id='check_if_email_needed',
        python_callable=should_send_email,
        provide_context=True,
    )

    # Task 3: Prepare email content
    prepare_email = PythonOperator(
        task_id='prepare_email_content',
        python_callable=prepare_email_content,
        provide_context=True,
    )

    # Task 4: Send email alert
    # send_email_alert = EmailOperator(
    #     task_id='send_email_alert',
    #     to='your.email@example.com',  # Replace with your email
    #     subject='Stock Price Alert - Price Below Threshold',
    #     html_content="{{ task_instance.xcom_pull(task_ids='prepare_email_content') }}",
    #     conn_id='smtp_default'
    # )
    send_email_alert = PythonOperator(
        task_id='send_email_alert',
        python_callable=email_generation,
        provide_context=True,
    )

    # Set task dependencies
    check_price >> email_check >> prepare_email >> send_email_alert