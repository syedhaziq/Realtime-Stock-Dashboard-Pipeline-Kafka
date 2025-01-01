# Realtime Stock Dashboard Pipeline with Kafka

This project implements a real-time data pipeline that streams live stock market data using Apache Kafka, processes it, and visualizes the information through a real-time dashboard.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Design](#system-design)
- [Technologies Used](#technologies-used)
- [Dashboard](#dashboard)

## Overview

In the fast-paced world of stock trading, real-time data analysis is crucial. This project sets up a data streaming pipeline that captures live stock data, processes it, and displays it on a real-time dashboard for analysis and decision-making.

## Features

- **Real-Time Data Streaming**: Utilizes Apache Kafka to stream live stock market data.
- **Data Processing**: Processes incoming data for analysis.
- **Batch Processing**: Aggregates and stores historical data for trend analysis.
- **Email Alerts**: Sends notifications for actionable stock movements.
- **Real-Time Dashboard**: Visualizes processed data for monitoring.

## System Design

The system integrates real-time and batch processing pipelines with orchestration and alerting mechanisms. Here’s an overview:

### 1. Real-Time Data Pipeline
- **Producer DAG (`realtime_ingestion.py`)**:
  - Fetches stock market data every second using Yahoo Stock API.
  - Publishes the data to an Apache Kafka topic.
  
- **Real-Time Consumer (`realtime_data_dump.py`)**:
  - Spark Streaming application that consumes Kafka data.
  - Inserts processed data into a PostgreSQL table (`live_stock`).

- **Pipeline Schedule**:
  - Runs continuously during market hours (9:00 AM to 4:30 PM).

### 2. Batch Processing Pipeline
- **Batch Producer DAG (`L30_ingestion.py`)**:
  - Fetches daily stock data and sends it to a Kafka topic.
  
- **Batch Processor (`L30D_data_dump.py`)**:
  - Spark batch application that processes Kafka data.
  - Stores results in the `historical_stock_data` table in PostgreSQL.
  - Scheduled to run once daily after market hours.

### 3. Email Alerts
- **Email Generation DAG (`email_generation.py`)**:
  - Sends alerts when stock prices hit predefined thresholds.
  - Helps users make data-driven decisions like buying or selling stocks.
  - Schedule can be customized based on needs.

### 4. Orchestration
- Managed using **Apache Airflow**, which ensures task dependencies and execution order are maintained efficiently.

### 5. Containerization
- Services, including producer, consumer, Airflow, Kafka, and PostgreSQL, are containerized using **Docker**.
- **Why Docker?**:
  - Ensures consistent environments across development, testing, and production.
  - Isolates services to prevent conflicts.
  - Simplifies scalability and portability.
  - Allows easy deployment on any system with Docker installed.

## Technologies Used

- **Programming Language**: Python
- **Data Streaming**: Apache Kafka
- **Data Processing**: Apache Spark (Streaming and Batch)
- **Database**: PostgreSQL
- **Visualization**: Power BI
- **Orchestration**: Apache Airflow
- **Containerization**: Docker

## Dashboard

Open `dashboard_real-time.pbix` in Power BI and connect it to your PostgreSQL database.

![Dashboard](dashboard.png "System Architecture Overview")

