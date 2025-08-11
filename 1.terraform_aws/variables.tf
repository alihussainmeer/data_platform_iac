variable "db_name" {
  description = "The name of the database to create"
  type        = string
  default     = "mydb"
}

variable "db_username" {
  description = "The master username for the database"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "The master password for the database"
  type        = string
  sensitive   = true 
}