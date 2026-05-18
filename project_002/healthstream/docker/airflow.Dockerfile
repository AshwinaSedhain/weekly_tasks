FROM apache/airflow:2.8.3

USER airflow

RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres==5.10.2 \
    apache-airflow-providers-common-sql==1.14.2
