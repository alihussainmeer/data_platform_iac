data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}


resource "aws_security_group" "mysql_sg" {
  name        = "mysql_access_sg"
  description = "Allow inbound traffic for MySQL"
  vpc_id      = data.aws_vpc.default.id


  ingress {
    description = "MySQL access from anywhere"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mysql_access_sg"
  }
}


resource "aws_db_subnet_group" "default_subnets" {
  name       = "mysql-subnet-group"
  subnet_ids = data.aws_subnets.default.ids
  tags = {
    Name = "MySQL Subnet Group"
  }
}


resource "aws_db_instance" "default" {
  allocated_storage = 20
  storage_type      = "gp2"
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = "db.t3.micro"
  db_name           = var.db_name
  username          = var.db_username
  password          = var.db_password
  parameter_group_name = "default.mysql8.0"
  skip_final_snapshot = true

  vpc_security_group_ids = [aws_security_group.mysql_sg.id]

  db_subnet_group_name = aws_db_subnet_group.default_subnets.name

  publicly_accessible = true
}






# Define your EKS cluster
resource "aws_eks_cluster" "my_dbt_cluster" {
  name     = "dbt-airflow-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids = data.aws_subnets.default.ids
  }

  tags = {
    Name = "dbt-airflow-cluster"
  }
}

# Define the IAM role for the EKS cluster
resource "aws_iam_role" "eks_cluster_role" {
  name = "eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      },
    ]
  })
}

# Attach the required policy to the cluster role
resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}


# Define the managed node group
resource "aws_eks_node_group" "my_dbt_node_group" {
  cluster_name    = aws_eks_cluster.my_dbt_cluster.name
  node_group_name = "dbt-nodes"
  node_role_arn   = aws_iam_role.eks_nodegroup_role.arn
  subnet_ids      = data.aws_subnets.default.ids
  instance_types = ["t3.medium"]
  scaling_config {
    desired_size = 1
    max_size     = 1
    min_size     = 1
  }

  tags = {
    Name = "dbt-node-group"
  }
}

# Define the IAM role for the EKS node group
resource "aws_iam_role" "eks_nodegroup_role" {
  name = "eks-nodegroup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

# Attach the required policies to the node group role
resource "aws_iam_role_policy_attachment" "eks_nodegroup_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodegroup_role.name
}
resource "aws_iam_role_policy_attachment" "eks_container_registry_read_only" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodegroup_role.name
}
resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodegroup_role.name
}

# Define the ECR repository
resource "aws_ecr_repository" "my_dbt_repo" {
  name = "my-dbt-repo"
  force_delete = true
  tags = {
    Name = "dbt-airflow-ecr"
  }
}

# Output the ECR repository URI
output "ecr_repository_uri" {
  value = aws_ecr_repository.my_dbt_repo.repository_url
}