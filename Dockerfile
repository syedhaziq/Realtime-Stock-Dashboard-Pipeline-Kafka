# # FROM apache/airflow:2.10.3
# FROM apache/airflow:2.10.3-python3.10
# # FROM apache/airflow:2.7.2

# # Install PostgreSQL development libraries
# USER root
# RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# # Switch back to airflow user
# USER airflow

# # Copy the requirements file
# COPY requirements.txt /requirements.txt

# # Install Python dependencies
# RUN pip install --no-cache-dir -r /requirements.txt

FROM apache/airflow:2.10.3-python3.9

USER root

# Install Java 17
RUN apt-get update && \
    apt-get install -y \
    libpq-dev \
    gcc \
    wget \
    && \
    wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | apt-key add - && \
    echo "deb https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" | tee /etc/apt/sources.list.d/adoptium.list && \
    apt-get update && \
    apt-get install -y temurin-17-jdk \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME for Java 17
ENV JAVA_HOME /usr/lib/jvm/temurin-17-jdk-amd64
ENV PATH $PATH:$JAVA_HOME/bin

# Install Spark 3.5.1
RUN wget https://dlcdn.apache.org/spark/spark-3.5.4/spark-3.5.4-bin-hadoop3.tgz && \
    tar -xzf spark-3.5.4-bin-hadoop3.tgz && \
    mv spark-3.5.4-bin-hadoop3 /opt/spark && \
    rm spark-3.5.4-bin-hadoop3.tgz

# Set Spark environment variables
ENV SPARK_HOME /opt/spark
ENV PATH $PATH:$SPARK_HOME/bin
ENV PYTHONPATH $SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-version-src.zip:$PYTHONPATH

USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
