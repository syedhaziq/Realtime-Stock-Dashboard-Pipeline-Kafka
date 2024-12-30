import json
import os
# os.environ['HADOOP_HOME'] = 'C:/hadoop'  # Hadoop installation directory
# os.environ['PATH'] = os.environ['PATH'] + ';C:/hadoop/bin'
# print(os.environ['PATH'] + ';C:/hadoop/bin')
# os.environ['JAVA_HOME'] = 'C:/Program Files/Java'  # Update with your Java path
# os.environ['SPARK_LOCAL_DIRS'] = 'C:/Users/syed_/AppData/Local/Temp/spark'  # Create this directory

### for docker version ##########
os.environ['HADOOP_HOME'] = '/opt/spark'  # Because Hadoop is bundled with Spark in our setup
os.environ['PATH'] = os.environ['PATH'] + ':/opt/spark/bin'

# import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField,StringType, DoubleType, TimestampType, ArrayType
from pyspark.sql.functions import from_json, col, explode
from pyspark.sql import DataFrame
from sqlalchemy import create_engine
import psycopg2
from kafka import KafkaConsumer, TopicPartition
from io import StringIO
import sys



BROKER = "kafka:29092"
# topic= "test"

# spark =  SparkSession.builder \
#     .appName("KafkaIntegration") \
#     .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
#     .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow") \
#     .config("spark.sql.streaming.checkpointLocation", "C:/checkpoint/query1") \
#     .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem") \
#     .config("spark.driver.extraClassPath", "C:/hadoop/bin") \
#     .config("spark.hadoop.fs.defaultFS", "file:///") \
#     .master("local[*]") \
#     .getOrCreate()

def spark_streaming(topic, BROKER):


    spark =  SparkSession.builder \
        .appName("KafkaIntegration") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
        .master("local[*]") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("DEBUG")
    spark.sparkContext.setLogLevel("WARN")
    print(spark)
    print("Spark session created successfully")

    schema = StructType()\
        .add("ticker", StringType()) \
        .add("timestamp", StringType()) \
        .add("open", DoubleType()) \
        .add("dayLow", DoubleType()) \
        .add("dayHigh", DoubleType()) \
        .add("currentPrice", DoubleType()) \
        .add("currency", StringType()) \
        .add("volume", DoubleType()) \
        .add("marketCap", DoubleType())

    raw_stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", BROKER) \
        .option("subscribe", topic) \
        .option("startingoffsets", "earliest") \
        .load()

    print(f"Reading from topic {topic}")

    parsed_stream = raw_stream.selectExpr("CAST(value AS STRING) as json")\
        .select(from_json(col("json"), schema).alias("data"))\
        .select("data.*")


    

    def write_to_postgres(batch_df, batch_id):
        table_name = "stock_prices"
        df = batch_df.toPandas()
        df.columns = df.columns.str.lower()
        conn = None
        try:
            # Create connection
            conn = psycopg2.connect(
                host='postgres_data',
                database='admin',
                user='admin',
                password='admin',
                port='5432'
            )
            
            cur = conn.cursor()
        
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            
            table_exists = cur.fetchone()[0]
            
            # If table doesn't exist, create it
            if not table_exists:
                columns = list(df.columns)
                # You can modify the data types based on your needs
                create_table_query = f"""
                CREATE TABLE public.{table_name} (
                    {', '.join(f"{col} TEXT" for col in columns)}
                );
                """
                print(create_table_query)
                cur.execute(create_table_query)
                print(f"Created new table: {table_name}")
            else:
                print(f"Table {table_name} already exists")
            
            # Convert DataFrame to CSV string for efficient copying
            buffer = StringIO()
            df.to_csv(buffer, index=False, header=False)
            buffer.seek(0)
            
            # Use COPY command to append data
            cur.copy_from(
                buffer,
                table_name,
                sep=',',
                columns=df.columns
            )
            
            # Commit transaction
            conn.commit()
            print(f"Successfully appended {len(df)} rows to {table_name}")
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error: {str(e)}")
            raise
        
        finally:
            if 'cur' in locals():
                cur.close()
            if conn:
                conn.close()

    

    # query = parsed_stream.writeStream \
    #     .outputMode("append") \
    #     .foreachBatch(write_to_postgres) \
    #     .option("checkpointLocation", "C:/checkpoint/query1") \
    #     .start()
    query = parsed_stream.writeStream \
        .outputMode("append") \
        .foreachBatch(write_to_postgres) \
        .start()
    query.awaitTermination()


def spark_l30d(topic, BROKER):

    spark = SparkSession.builder \
        .appName("L30d_Batch") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
        .master("local[*]") \
        .getOrCreate()
    
    print(spark)
    print("Spark session created successfully")
    
    spark.sparkContext.setLogLevel("WARN")

    schema = ArrayType(
        StructType()
        .add("Date", StringType())
        .add("Open", StringType())
        .add("Close", DoubleType())
    )

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=BROKER)
    
    # consumer.poll(timeout_ms=1000)
    topic = [topic]

    last_offsets = {}

    for topic in topic:
       
        topic_offsets = {}
        
       
        partitions = consumer.partitions_for_topic(topic)
        if not partitions:
            print(f"No partitions found for topic: {topic}")
            continue
        print(f"Partitions for topic {topic}: {partitions}")
       
        for partition in partitions:
            # Create a TopicPartition object for each partition
            tp = [TopicPartition(topic, partition)]
            print(f'hello {tp}')
            # Get the last offset for the partition
            last_offset = consumer.end_offsets(tp) #consumer.end_offsets([tp])[tp]
            print(f"Last offset for partition {partition}: {last_offset[tp[0]]}")
    
            topic_offsets[partition] = last_offset[tp[0]]-1


        last_offsets[topic] = topic_offsets
    
    starting_offset = json.dumps(last_offsets)
    print(f'final list is {last_offsets}')
    # Read data from Kafka as a batch
    parsed_data = spark.read \
        .format("kafka") \
        .option("kafka.bootstrap.servers", BROKER) \
        .option("subscribe", topic) \
        .option("startingOffsets", starting_offset)\
        .load()
    
    df = parsed_data.selectExpr("CAST(value AS string) AS json") \
        .select(from_json(col("json"), schema).alias("data")) \
        .select(explode(col("data")).alias("data")) \
        .select("data.Date", "data.Open", "data.Close")
    
    # Function to write data to Postgres
    def write_to_postgres(batch_df):
        table_name = "historical_stock_data"
        df = batch_df.toPandas()
        df.columns = df.columns.str.lower()
        conn = None
        try:
            # Create connection
            conn = psycopg2.connect(
                host='postgres_data',
                database='admin',
                user='admin',
                password='admin',
                port='5432'
            )
            
            cur = conn.cursor()
            
            # Check if the table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            
            table_exists = cur.fetchone()[0]
            print(table_exists)
            
            if not table_exists:
                print('Creating table')
                columns = list(df.columns)
                
                create_table_query = f"""
                CREATE TABLE public.{table_name} (
                    {', '.join(f"{col} TEXT" for col in columns)}
                );
                """
                print(create_table_query)
                cur.execute(create_table_query)
                print(f"Created new table: {table_name}")
            else:
                print(f"Table {table_name} already exists")
            
            truncate_query = f"TRUNCATE TABLE public.{table_name};"
            cur.execute(truncate_query)
         
            buffer = StringIO()
            df.to_csv(buffer, index=False, header=False)
            buffer.seek(0)
            
            cur.copy_from(
                buffer,
                table_name,
                sep=',',
                columns=df.columns
            )
            
            conn.commit()
            print(f"Successfully appended {len(df)} rows to {table_name}")
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error: {str(e)}")
            raise
        
        finally:
            if 'cur' in locals():
                cur.close()
            if conn:
                conn.close()

    # Write the batch data to Postgres
    write_to_postgres(df)
    print("Batch process completed.")

# def spark_l30d(topic, BROKER):

#     spark = SparkSession.builder \
#         .appName("L30d") \
#         .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
#         .master("local[*]") \
#         .getOrCreate()
    
#     print(spark)
#     print("Spark session created successfully")
    
#     spark.sparkContext.setLogLevel("DEBUG")
#     spark.sparkContext.setLogLevel("WARN")

    
#     schema = ArrayType(
#         StructType()\
#         .add("Date", StringType()) \
#         .add("Open", StringType()) \
#         .add("Close", DoubleType()) 
#     )

#     parsed_data = spark.readStream \
#         .format("kafka") \
#         .option("kafka.bootstrap.servers", BROKER) \
#         .option("subscribe", topic) \
#         .option("startingoffsets", "latest") \
#         .load()
    
#     df = parsed_data.selectExpr("Cast(value as string) as json") \
#         .select(from_json(col("json"), schema).alias("data")) \
#         .select(explode(col("data")).alias("data")) \
#         .select("data.Date", "data.Open", "data.Close")
    

#     def write_to_postgres(batch_df, batch_id):
#         table_name = "historical_stock_data"
#         df = batch_df.toPandas()
#         df.columns = df.columns.str.lower()
#         conn = None
#         try:
#             # Create connection
#             conn = psycopg2.connect(
#                 host='postgres_data',
#                 database='admin',
#                 user='admin',
#                 password='admin',
#                 port='5432'
#             )
            
#             cur = conn.cursor()
        
           
#             cur.execute("""
#                 SELECT EXISTS (
#                     SELECT FROM information_schema.tables 
#                     WHERE table_name = %s
#                 );
#             """, (table_name,))
            
#             table_exists = cur.fetchone()[0]
#             print(table_exists)
            
#             if not table_exists:
#                 print('Creating table')
#                 columns = list(df.columns)
               
#                 create_table_query = f"""
#                 CREATE TABLE public.{table_name} (
#                     {', '.join(f"{col} TEXT" for col in columns)}
#                 );
#                 """
#                 print(create_table_query)
#                 cur.execute(create_table_query)
#                 print(f"Created new table: {table_name}")
#             else:
#                 print(f"Table {table_name} already exists")
            
#             truncate_query = f"TRUNCATE TABLE public.{table_name};"
#             cur.execute(truncate_query)
         
#             buffer = StringIO()
#             df.to_csv(buffer, index=False, header=False)
#             buffer.seek(0)
            
           
#             cur.copy_from(
#                 buffer,
#                 table_name,
#                 sep=',',
#                 columns=df.columns
#             )
            
           
#             conn.commit()
#             print(f"Successfully appended {len(df)} rows to {table_name}")
            
#         except Exception as e:
#             if conn:
#                 conn.rollback()
#             print(f"Error: {str(e)}")
#             raise
        
#         finally:
#             if 'cur' in locals():
#                 cur.close()
#             if conn:
#                 conn.close()


#     query = df.writeStream \
#         .outputMode("append") \
#         .foreachBatch(write_to_postgres) \
#         .start()

#     # query = df.writeStream \
#     #     .outputMode("append") \
#     #     .format("console") \
#     #     .option("checkpointLocation", "C:/checkpoint/query2") \
#     #     .start()
#     query.awaitTermination()

# spark_l30d("l30d", BROKER)

# spark_streaming(topic, BROKER)



