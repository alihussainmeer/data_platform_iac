# dags/dbt_pipeline.py
import pendulum
from airflow.models.dag import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
import os
from kubernetes.client import models as k8s

CLUSTER_CONTEXT = os.environ["CLUSTER_CONTEXT"]

# The KubernetesPodOperator will use your local ~/.kube/config file to connect
# to your remote EKS cluster. Ensure your AWS credentials are also configured locally.
with DAG(
    dag_id="dbt_terraform_eks_pipeline",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    tags=["dbt", "kubernetes", "terraform"],
) as dag:
    run_dbt_models_on_eks = KubernetesPodOperator(
        task_id="run_dbt_models_on_eks",
        namespace="default",
        name="somethingGood",
        # This is the ECR image URI you pushed in the previous step
        # image="<aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/my-dbt-repo:latest",
        image="hello-world",
        cmds=["dbt"],
        arguments=["run"],
        # Use an environment variable to pass the profiles directory
        env_vars={"DBT_PROFILES_DIR": "/usr/app/dbt"},
        get_logs=True,
        do_xcom_push=False,
        in_cluster=False,
        cluster_context=CLUSTER_CONTEXT,
        config_file="/home/airflow/.kube/config",  # Replace with your local kubeconfig path
        security_context=k8s.V1SecurityContext(run_as_user=50000),
    )
