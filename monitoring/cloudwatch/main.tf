provider "aws" {
  access_key = "${var.aws_access_key}"
  region = "${var.aws_region}"
  secret_key = "${var.aws_secret_key}"
}

resource "aws_cloudwatch_metric_alarm" "environment_health_alarm" {
  alarm_name                = "${var.elastic_beanstalk_environment_name}-env-health"
  comparison_operator       = "GreaterThanOrEqualToThreshold"
  evaluation_periods        = "2"
  metric_name               = "CPUUtilization"
  namespace                 = "AWS/ElasticBeanstalk"
  period                    = "60"
  statistic                 = "Average"
  threshold                 = "10"  # 0=Ok, 1=Info, 15=Warning, 20=Degraded
  alarm_description         = "This metric monitors elastic beanstalk environment health"
  insufficient_data_actions = []
  alarm_actions = [
    "${var.sns_topic_arn}"
  ]
  dimensions {
    EnvironmentName = "${var.elastic_beanstalk_environment_name}"
  }
}

resource "aws_cloudwatch_metric_alarm" "cpu_utilization_alarm" {
  alarm_name                = "${var.elastic_beanstalk_environment_name}-cpuutil"
  comparison_operator       = "GreaterThanOrEqualToThreshold"
  evaluation_periods        = "2"
  metric_name               = "CPUUtilization"
  namespace                 = "AWS/EC2"
  period                    = "300"
  statistic                 = "Average"
  threshold                 = "80"
  alarm_description         = "This metric monitors ec2 cpu utilization"
  insufficient_data_actions = []
  alarm_actions = [
    "${var.sns_topic_arn}"
  ]
  dimensions {
    AutoScalingGroupName = "${var.auto_scaling_group_name}"
  }
}
