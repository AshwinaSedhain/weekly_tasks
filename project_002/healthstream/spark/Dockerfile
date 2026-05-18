FROM bitnami/spark:3.5.1

USER root

# Install Python deps
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Download PostgreSQL JDBC driver
RUN curl -fsSL \
    https://jdbc.postgresql.org/download/postgresql-42.7.1.jar \
    -o /opt/bitnami/spark/jars/postgresql-42.7.1.jar

COPY streaming_job.py      /app/streaming_job.py
COPY batch_aggregation.py  /app/batch_aggregation.py

WORKDIR /app

CMD ["spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1", \
     "--jars", "/opt/bitnami/spark/jars/postgresql-42.7.1.jar", \
     "streaming_job.py"]
