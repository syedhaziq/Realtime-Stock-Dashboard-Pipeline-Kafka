from etl.data_ingestion import data_ingestion, data_ingestion_l30d
from etl.data_dump_v2 import spark_streaming, spark_l30d


def realtime_pipeline(topic_name, ticker):
    data_ingestion(topic_name, ticker)

def l30d_pipeline(topic_name, ticker):
    data_ingestion_l30d(topic_name, ticker)

def data_dump_pipeline(topic, BROKER):
    spark_streaming(topic, BROKER)

def l30d_data_dump_pipeline(topic, BROKER):
    spark_l30d(topic, BROKER)


