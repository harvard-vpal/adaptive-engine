variable "aws_access_key" {
  description = "The AWS access key."
}
variable "aws_secret_key" {
  description = "The AWS secret key."
}
variable "aws_region" {
  default = "us-east-1"
}
variable "auto_scaling_group_name" {
  description = "Auto Scaling group name"
}
variable "elastic_beanstalk_environment_name" {
  description = "Elastic Beanstalk environment name"
}
variable "sns_topic_arn" {
  description = "SNS topic to send alarm alerts to"
}
