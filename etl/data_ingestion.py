import yfinance as yf
import json
import time
import logging
# import six
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError,KafkaError
from datetime import datetime, timedelta

LOG_FILE = "stock_producer.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

producer_instance = None
# topic_name = 'test'

def fetch_stock_data(ticker):

    try:
        stock = yf.Ticker(ticker)
        data = stock.info
        # print(f'Data has been fetched successfully!!!')
        logging.info(f'Data has been fetched successfully!!!')
        logging.info(json.dumps(data,indent=4))
        return {
            'ticker': ticker,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'open': data.get('open', None),
            'dayLow':data.get('dayLow', None),
            'dayHigh':data.get('dayHigh', None),
            'currentPrice':data.get('currentPrice', None),
            'currency': data.get('currency', 'Unknown'),
            'volume': data.get('volume', None),
            'marketCap': data.get('marketCap', None),
        }
    except Exception as e:
        # print(f"Error in fetching the data {e}")
        logging.error(f"Error in fetching the data {e}")


def fetch_last_30_days_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        last_30_days_data = hist[['Open', 'Close']].reset_index()
        logging.info(f'Last 30 days data has been fetched successfully for {ticker}!!!')
        logging.info(last_30_days_data)
        return last_30_days_data
    except Exception as e:
        logging.error(f"Error in fetching the last 30 days data for {ticker}: {e}")
        return None


def create_producer():
    global producer_instance

    if producer_instance:
        logging.info(f"Producer already exists!!")
        return producer_instance

    try:
        producer_config = {
            'bootstrap_servers': 'kafka:29092',
            'client_id': 'json-dump',
            'value_serializer': lambda v: str(v).encode('utf-8')  # This is for serializing the message as a string
        }

        # KafkaProducer object creation
        producer_instance = KafkaProducer(**producer_config)

        logging.info(f"Producer has been created successfully")
        return producer_instance
    except Exception as e:
        logging.error(f"Couldn't create producer: {e}")



def topic_creation(topic_name):

    admin_client = KafkaAdminClient(
         bootstrap_servers='kafka:29092',
        client_id='topic-manager'
    )

    try:
        existing_topics = admin_client.list_topics()

        if topic_name in existing_topics:
            logging.info(f"The topic already exist!!!")
            return topic_name
        else:

            topic = NewTopic(
                name=  topic_name,
                num_partitions= 1,
                replication_factor= 1
            )

            admin_client.create_topics(new_topics=[topic])

            logging.info(f"The topic has been created successfully")
            return topic_name
    except TopicAlreadyExistsError:
        logging.info(f"Topic '{topic_name}' already exists.")
    except Exception as e:
         print(f"An error occurred: {e}")
    finally:
        admin_client.close()

  
def data_ingestion(topic_name, ticker):
    end_time = datetime.now() + timedelta(hours=7)
    producer = create_producer()
    topic = topic_creation(topic_name)
    while datetime.now() < end_time:
        data = fetch_stock_data(ticker)
        data = json.dumps(data)
        print(data)
        print(producer)
        print(topic)
        
        try:
            producer.send(
                topic = topic,
                value = data    
                # callback = delivery_report
            )
            producer.flush()
            logging.info(f"data send successfully")
        except Exception as e:
            logging.error("Couldn't send data")
        
        time.sleep(1)

def data_ingestion_l30d(topic_name, ticker):
    # end_time = datetime.now() + timedelta(minutes=1)
    producer = create_producer()
    topic = topic_creation(topic_name)
    
    data = fetch_last_30_days_data(ticker)
    
    data['Date'] = data['Date'].astype(str)
    data = data.to_dict(orient='records')
    # data = data.to_json(orient="records", date_format="iso", index=False)
    # result = {
    # "Date": data["Date"].tolist(),
    # "Open": data["Open"].tolist(),
    # "Close": data["Close"].tolist()
    # }
    data = json.dumps(data)
    print(json.dumps(data, indent=4))
    # print(json.dumps(data, indent=4))
    print(producer)
    print(topic)
    
    try:
        producer.send(
            topic = topic,
            value = data    
            # callback = delivery_report
        )
        producer.flush()
        logging.info(f"data send successfully")
    except Exception as e:
        logging.error("Couldn't send data")
    
    # time.sleep(10)       


# data_ingestion_l30d('l30d', 'AAPL')
# data_ingestion(topic_name, 'AAPL')



