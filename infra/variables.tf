variable "aws_region" {
  description = "The region for AWS"
  default     = "ap-south-1"
}

variable "instance_type" {
  description = "The instance for EC2"
  default     = "t2.micro"
}

variable "key_name" {
  description = "Name of SSH key pair"
  default     = "sentinel_key"
}
