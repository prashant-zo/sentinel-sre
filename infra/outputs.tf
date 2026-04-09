output "server_public_ip" {
  description = "Public ip address of EC2 instance"
  value       = aws_instance.server.public_ip
}
