FROM apache/airflow:2.9.2
USER root
# RUN pip install "apache-airflow[amazon]"
USER airflow
RUN pip install "apache-airflow[amazon]"

ENV CLUSTER_CONTEXT=arn:aws:eks:us-west-2:198457082874:cluster/dbt-airflow-cluster