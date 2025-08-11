# output "db_endpoint" {
#   description = "The address of the RDS database instance."
#   value       = aws_db_instance.default.address
# }

output "security_group_id" {
  description = "The ID of the security group that was created."
  value       = aws_security_group.mysql_sg.id
}
