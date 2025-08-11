# Project Setup Guide

## 1. Deploy Infrastructure with Terraform

### Prerequisites

Before running Terraform, ensure you have the following installed and configured:

1. **Terraform** (version >= 1.0)
   - Download from: https://www.terraform.io/downloads.html
   - Verify installation: `terraform --version`

2. **AWS CLI** (version >= 2.0)
   - Download from: https://aws.amazon.com/cli/
   - Verify installation: `aws --version`

3. **AWS Credentials Configuration**
   - Configure AWS credentials using one of these methods:
     - AWS CLI: `aws configure`
     - Environment variables: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
     - IAM roles (if running on EC2)
   - Ensure your AWS account has sufficient permissions for:
     - EKS (Elastic Kubernetes Service)
     - RDS (Relational Database Service)
     - ECR (Elastic Container Registry)
     - IAM (Identity and Access Management)
     - VPC and Security Groups

4. **kubectl** (for EKS cluster interaction)
   - Download from: https://kubernetes.io/docs/tasks/tools/
   - Verify installation: `kubectl version --client`

### Deployment Steps

1. **Navigate to the Terraform directory:**
   ```bash
   cd 1.terraform_aws
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Set the database password variable:**
   ```bash
   export TF_VAR_db_password="your-secure-password-here"
   ```
   Or create a `terraform.tfvars` file:
   ```hcl
   db_password = "your-secure-password-here"
   ```

4. **Review the deployment plan:**
   ```bash
   terraform plan
   ```

5. **Apply the infrastructure:**
   ```bash
   terraform apply
   ```
   Type `yes` when prompted to confirm the deployment.

### Expected Output

After successful deployment, you should see output similar to:

```
Apply complete! Resources: 8 added, 0 changed, 0 destroyed.

Outputs:

security_group_id = "sg-xxxxxxxxx"
```

### What Gets Deployed

The Terraform configuration will create:

1. **RDS MySQL Database**
   - Instance type: `db.t3.micro`
   - Storage: 20GB GP2
   - Engine: MySQL 8.0
   - Publicly accessible for development
   - Security group allowing MySQL access (port 3306)

2. **EKS Cluster**
   - Cluster name: `dbt-airflow-cluster`
   - Node group with t3.medium instances
   - IAM roles and policies for EKS operations

3. **ECR Repository**
   - Repository for storing Docker images
   - Used for dbt and Airflow containers

4. **Security Groups and Networking**
   - VPC security groups for database access
   - Subnet groups for RDS

### Next Steps

After successful deployment:
1. Configure kubectl to connect to your EKS cluster
2. Proceed to the next step (Airbyte setup)

---

## 2. Setting up Airbyte Connectors and Connections

### 2.1 Create Kaggle Source Connector

1. Log in to Airbyte Cloud (https://cloud.airbyte.com)
2. Navigate to the Builder section in the main menu
3. Click "Create custom connector" in the top right corner
4. Select "Import YAML manifest"
5. Copy and paste the contents from [2.airbyte/kaggle.yaml](2.airbyte/kaggle.yaml) into the editor
6. Click "Create source"

This will create a custom connector that can fetch temperature readings data from the Kaggle IoT dataset.

### 2.2 Create MySQL Destination Connector

1. In Airbyte Cloud, navigate to "Destinations" in the main menu
2. Click "New destination"
3. Search for "MySQL" and select it
4. Configure the MySQL destination with the following settings:

   **Connection Configuration:**
   - **Host**: Use the RDS endpoint from Terraform output (e.g., `your-db-instance.region.rds.amazonaws.com`)
   - **Port**: `3306`
   - **Database Name**: `mydb` (or the value you set in `db_name` variable)
   - **Username**: `admin` (or the value you set in `db_username` variable)
   - **Password**: The password you set in `TF_VAR_db_password`
   - **JDBC URL Parameters**: Leave empty or add any additional parameters if needed

5. Click "Set up destination"
6. Test the connection to ensure it can connect to your RDS MySQL instance
7. Click "Save & continue"

### 2.3 Create Connection Between Source and Destination

1. In Airbyte Cloud, navigate to "Connections" in the main menu
2. Click "New connection"
3. Select your Kaggle source connector as the **Source**
4. Select your MySQL destination connector as the **Destination**
5. Click "Continue"

**Configure the connection settings:**

6. **Sync Mode**: Select "Full refresh - Overwrite" for initial setup
7. **Destination Stream Prefix**: Leave empty or add a prefix like `kaggle_`
8. **Destination Table Name**: The data will be written to a table named after the stream (e.g., `iot_temperature_data`)

**Configure the data stream:**

9. Click "Set up connection"

### 2.4 Test and Run the Connection

1. **Test the connection:**
   - Click "Test connection" to verify both source and destination are working
   - Ensure no errors are reported

2. **Run the initial sync:**
   - Click "Sync now" to start the first data transfer
   - Monitor the sync progress in the connection dashboard
   - Verify data appears in your MySQL database

3. **Verify data in MySQL:**
   ```sql
   -- Connect to your RDS MySQL instance
   mysql -h your-db-endpoint -u admin -p mydb

   -- Check if the table was created
   SHOW TABLES;

   -- View the imported data
   SELECT * FROM iot_temperature_data LIMIT 10;
   ```

### Expected Results

After successful setup, you should have:
- A custom Kaggle source connector configured
- A MySQL destination connector connected to your RDS instance
- A connection between source and destination
- Temperature data from Kaggle IoT dataset loaded into your MySQL database
- A table structure ready for dbt transformations

### Next Steps

The connection is now ready to be triggered by Airflow (which will be implemented in the next steps). The data pipeline will:
1. Extract data from Kaggle using the custom connector
2. Load data into MySQL RDS instance
3. Be orchestrated by Airflow for scheduled runs

---

## 3. Setting up dbt for Data Transformation

### 3.1 Prerequisites

Before proceeding, ensure you have:
- Docker installed and running
- AWS CLI configured with ECR access
- RDS MySQL database endpoint from Terraform output
- Database credentials ready

### 3.2 Configure Environment Variables

1. **Navigate to the dbt directory:**
   ```bash
   cd 3.dbt
   ```

2. **Create a `.env` file with your database credentials:**
   ```bash
   # Database Configuration
   DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
   DB_PORT=3306
   DB_SCHEMA=mydb
   DB_USER=admin
   DB_PASSWORD=your-secure-password

   # AWS Configuration (for ECR)
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_DEFAULT_REGION=us-west-2
   ```

   **⚠️ Security Note:** This `.env` file contains sensitive credentials. In production, use AWS Secrets Manager or environment variables instead.

3. **Update the profiles.yml file:**
   ```bash
   # Edit the profiles.yml file to use the correct host
   sed -i 's/host.docker.internal/your-rds-endpoint.region.rds.amazonaws.com/g' personal_project/profiles.yml
   ```

### 3.3 Build and Test dbt Docker Image Locally

1. **Build the Docker image:**
   ```bash
   docker build -t dbt-personal-project .
   ```

2. **Test the dbt connection:**
   ```bash
   docker run --env-file .env dbt-personal-project dbt debug
   ```

3. **Run dbt tests to verify data quality:**
   ```bash
   docker run --env-file .env dbt-personal-project dbt test
   ```

4. **Build the models:**
   ```bash
   docker run --env-file .env dbt-personal-project dbt run
   ```

### 3.4 Push Docker Image to ECR

1. **Get your ECR repository URI from Terraform output:**
   ```bash
   cd ../1.terraform_aws
   terraform output ecr_repository_uri
   ```

2. **Authenticate Docker to ECR:**
   ```bash
   aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin your-account-id.dkr.ecr.us-west-2.amazonaws.com
   ```

3. **Tag the Docker image:**
   ```bash
   docker tag dbt-personal-project:latest your-account-id.dkr.ecr.us-west-2.amazonaws.com/dbt-personal-project:latest
   ```

4. **Push to ECR:**
   ```bash
   docker push your-account-id.dkr.ecr.us-west-2.amazonaws.com/dbt-personal-project:latest
   ```

### 3.5 Data Quality Tests

The dbt project includes comprehensive data quality tests in `fact_iot_temperature_data.yml`:

- **Uniqueness tests** on device_id
- **Not null tests** on all critical fields
- **Accepted values tests** on device_location (must be 'In' or 'Out')

Run tests to ensure data quality:
```bash
docker run --env-file .env dbt-personal-project dbt test --select fact_iot_temperature_data
```

### 3.6 Verify Data Transformations

1. **Check the built tables:**
   ```bash
   docker run --env-file .env dbt-personal-project dbt run --select fact_iot_temperature_data
   ```

2. **View the transformed data:**
   ```sql
   -- Connect to your RDS MySQL instance
   mysql -h your-rds-endpoint -u admin -p mydb

   -- Check the transformed table
   SELECT * FROM stage.fact_iot_temperature_data LIMIT 10;

### Expected Results

After successful dbt execution, you should have:
- A transformed `fact_iot_temperature_data` table in the `stage` schema
- All data quality tests passing
- Clean, validated IoT temperature data ready for analytics
- Docker image pushed to ECR for Airflow orchestration

### Troubleshooting

- **Connection issues**: Verify RDS endpoint and credentials in `.env` file
- **Permission errors**: Ensure AWS credentials have ECR push permissions
- **Test failures**: Check data quality and adjust tests if needed

### Next Steps

The dbt transformation layer is now ready. The next step will be setting up Airflow to orchestrate the complete pipeline:
1. Trigger Airbyte sync
2. Run dbt transformations
3. Schedule the entire workflow

---

## 4. Setting up Airflow Orchestration

### 4.1 Local Airflow Setup (Planned Implementation)

The project includes a local Airflow setup using Docker Compose with Kubernetes integration for running dbt jobs on EKS.

#### Prerequisites for Local Setup

1. **Docker and Docker Compose** installed
2. **kubectl** configured to access your EKS cluster
3. **AWS credentials** configured locally
4. **Kubernetes config** mounted in the Airflow container

#### Local Airflow Deployment

1. **Navigate to the Airflow directory:**
   ```bash
   cd airflow
   ```

2. **Set up environment variables:**
   ```bash
   # Create .env file for Airflow
   cat > .env << EOF
   AIRFLOW_UID=50000
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_DEFAULT_REGION=us-west-2
   CLUSTER_CONTEXT=your-eks-cluster-context
   EOF
   ```

3. **Start Airflow services:**
   ```bash
   docker-compose up -d
   ```

4. **Access Airflow UI:**
   - Open http://localhost:8080
   - Login with: `airflow` / `airflow`

#### Current DAG Implementation

The project includes a DAG (`dbt_dag.py`) that uses `KubernetesPodOperator` to run dbt jobs on EKS:

```python
# Key features of the current implementation:
- Uses KubernetesPodOperator to run dbt in EKS pods
- Connects to EKS cluster using local kubeconfig
- Runs dbt commands with proper environment variables
- Supports manual triggering and logging
```

#### Running the Current DAG

1. **Enable the DAG in Airflow UI:**
   - Navigate to DAGs section
   - Find `dbt_terraform_eks_pipeline`
   - Toggle the DAG to "On"

2. **Trigger the DAG manually:**
   - Click on the DAG name
   - Click "Trigger DAG" button
   - Monitor execution in the Airflow UI

3. **View logs and results:**
   - Check task logs for dbt execution
   - Verify data transformations in MySQL

### 4.2 AWS MWAA Setup (Planned Implementation)

#### Prerequisites for MWAA

1. **AWS MWAA Environment** created
2. **VPC Configuration** with private subnets
3. **Security Groups** allowing MWAA to access EKS
4. **IAM Roles** with necessary permissions

#### MWAA Environment Setup

1. **Create MWAA Environment:**
   ```bash
   # Using AWS CLI (example)
   aws mwaa create-environment \
     --name dbt-airflow-environment \
     --source-bucket-arn arn:aws:s3:::your-airflow-bucket \
     --execution-role-arn arn:aws:iam::your-account:role/MWAAExecutionRole \
     --network-configuration SubnetIds=subnet-xxx,subnet-yyy,SecurityGroupIds=sg-xxx \
     --airflow-version 2.9.2
   ```

2. **Upload DAGs to S3:**
   ```bash
   # Package and upload DAGs
   aws s3 cp dags/ s3://your-airflow-bucket/dags/ --recursive
   ```

3. **Configure MWAA for EKS Access:**
   - Update security groups to allow MWAA → EKS communication
   - Configure IAM roles for EKS access
   - Set up VPC endpoints if needed

#### Enhanced DAG for MWAA

The MWAA implementation will include:

```python
# Planned enhancements:
- Airbyte API integration for triggering syncs
- Enhanced error handling and retries
- Data quality checks and alerts
- Monitoring and alerting integration
- Support for multiple environments (dev/staging/prod)
```

### 4.3 Complete Pipeline Orchestration

#### Current Pipeline Flow

1. **Manual Trigger** → Airflow DAG starts
2. **KubernetesPodOperator** → Creates pod in EKS
3. **dbt Container** → Runs from ECR image
4. **Data Transformation** → Executes dbt models
5. **Results** → Stored in MySQL database

#### Planned Enhanced Flow

1. **Scheduled Trigger** → Airflow DAG starts automatically
2. **Airbyte Sync** → Triggered via API
3. **Data Validation** → Check sync completion
4. **dbt Transformation** → Run on EKS
5. **Quality Checks** → Validate transformed data
6. **Notifications** → Send success/failure alerts

### 4.4 Monitoring and Maintenance

#### Current Monitoring

- Airflow UI for DAG status
- Kubernetes pod logs
- dbt execution logs
- MySQL database queries

#### Planned Monitoring

- CloudWatch metrics and alarms
- Data quality dashboards
- Slack/email notifications
- Performance monitoring
- Cost optimization alerts

### Expected Results

After successful Airflow setup, you should have:
- **Local Setup**: Working Airflow instance with EKS integration
- **MWAA Setup**: Managed Airflow environment (when implemented)
- **Automated Pipeline**: End-to-end data transformation workflow
- **Monitoring**: Visibility into pipeline execution and data quality

### Next Steps

1. **Complete MWAA Implementation**:
   - Set up MWAA environment
   - Migrate DAGs to S3
   - Configure networking and security
   - Test end-to-end pipeline

2. **Enhance Pipeline**:
   - Add Airbyte API integration
   - Implement comprehensive monitoring
   - Add data quality alerts
   - Optimize for production use

3. **Production Deployment**:
   - Implement proper secrets management
   - Add backup and disaster recovery
   - Set up CI/CD for DAG deployment
   - Configure production monitoring

