import pendulum
from airflow.utils.task_group import TaskGroup
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.models.dag import DAG
from airflow.decorators import task_group
from airflow.models.baseoperator import chain
from airflow.operators.python_operator import PythonOperator
from airflow.operators.slack_operator import SlackAPIPostOperator
from airflow.contrib.operators.slack_webhook_operator import SlackWebhookOperator
import requests

dag = DAG(
    dag_id="test_dag",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example"],
)


def slack_failed_task(task_name):
    failed_alert = SlackWebhookOperator(
        task_id="slack_failed_alert",
        http_conn_id="slack_connection",
        webhook_token="T04AMSUHSKW/B04AKLNTXHQ/no3dinLUfWDptKt6yLtwfOiN",
        message="@here DAG Failed {}".format(task_name),
        channel="D04A4SU081M",
        username="Airflow_{}".format("DEV"),
        icon_emoji=":red_circle:",
        link_names=True,
    )
    return failed_alert.execute


def gtask(name, run_type="P", dag=dag):
    if run_type == "M":
        name = name.lower() + "_run"
    elif run_type == "T":
        name = name.lower() + "_test"
    elif run_type == "DH":
        name = "datahub_ingestion_" + name
    elif run_type == "TG":
        return dag.task_group.get_child_by_label(name)
    return dag.get_task(name)


bash_operator_for_google_sheets = BashOperator
bash_operator_for_erp = BashOperator

start_task = BashOperator(
    task_id="start_task",
    bash_command="sleep 5",
    dag=dag,
)
end_task = BashOperator(task_id="end_task", bash_command="sleep 5", dag=dag)

# TG
list_of_task_groups = ["gsheet"]
for i in list_of_task_groups:
    paths = TaskGroup(group_id=f"{i}", dag=dag)


list_of_google_sheet_tasks = [["g1", "gsheet"], ["g2", "gsheet"]]

for i in list_of_google_sheet_tasks:
    m1 = bash_operator_for_google_sheets(
        task_id=f"{i[0]}",
        bash_command="sleep 5",
        dag=dag,
        task_group=gtask(f"{i[1]}", run_type="TG"),
    )

list_of_erp_tasks = ["erp1", "erp2"]
with TaskGroup(group_id="erp", dag=dag) as erp_tasks:
    for i in list_of_erp_tasks:
        m1 = bash_operator_for_erp(task_id=f"{i}", bash_command="sleep 5", dag=dag)


list_of_task_order = [
    chain(
        gtask("erp.erp1"),
        gtask("erp.erp2"),
    ),
    chain(
        gtask("start_task", run_type="P"),
        gtask("gsheet", run_type="TG"),
        gtask("erp", run_type="TG"),
        gtask("end_task", run_type="P"),
    ),
]

# slack_msg = "Hi Wssup?"

# slack_test = SlackWebhookOperator(
#     task_id="slack_test",
#     http_conn_id="slack_connection",
#     webhook_token="T04AMSUHSKW/B04AKLNTXHQ/no3dinLUfWDptKt6yLtwfOiN",
#     message=slack_msg,
#     channel="#random",
#     username="airflow_",
#     icon_emoji=None,
#     link_names=False,
#     dag=dag,
# )
# slack_test


task_with_failed_slack_alerts = PythonOperator(
    task_id="task0",
    python_callable=lambda: 0 / 0,
    on_failure_callback=slack_failed_task,
    provide_context=True,
    dag=dag,
)

def send_slack_msg():
    slack_token = "xpxb-9534042403-731932630054-KSwhrmhg87TXGuF23Z4ipTRm"

    data = {
        'token': slack_token,
        'channel': 'UJ24R2MPE',    # User ID.
        'as_user': True,
        'text': "@amir GO Home!"
    }

    requests.post(url='https://slack.com/api/chat.postMessage',
                data=data)

task_with_failed_slack_alerts

for i in list_of_task_order:
    i
# start_task >> gtask("gsheet", run_type="TG") >> erp_tasks >> end_task
