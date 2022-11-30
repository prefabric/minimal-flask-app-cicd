from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    Tags,
)
from constructs import Construct

class ProdStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, common_infra_stack: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        config = self.node.try_get_context("context")["config"]

        # vpc creation
        vpc = ec2.Vpc(
            self,
            "FlaskAppVPC",
            cidr=f"{config['prod']['cidr']}/21",
            max_azs=config["prod"]["max_azs"],
            nat_gateways=config["prod"]["nat_gateways"],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                    name="PublicSubnet"
                ),
            ]
        )

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "sudo yum update -y",
            "sudo yum install -y docker ruby wget",
            "sudo service docker start",
            "sudo usermod -a -G docker ec2-user",
            "sudo chkconfig docker on",
            "sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose",
            "sudo chmod +x /usr/local/bin/docker-compose",
            "sudo amazon-linux-extras install nginx1",
            "sudo service nginx start",
            "sudo yum install -y amazon-ecr-credential-helper",
            "sudo chkconfig nginx on",
            'mkdir /home/ec2-user/.docker',
            'echo "{\\"credsStore\\": \\"ecr-login\\"}" > /home/ec2-user/.docker/config.json',
            f"wget https://aws-codedeploy-{self.region}.s3.{self.region}.amazonaws.com/latest/install",
            "chmod +x ./install",
            "sudo ./install auto"
        )

        user_data.add_s3_download_command(
            bucket=common_infra_stack.nginx_conf.bucket,
            bucket_key=common_infra_stack.nginx_conf.s3_object_key,
        )

        user_data.add_commands(
            f"sudo cp /tmp/{common_infra_stack.nginx_conf.s3_object_key} /etc/nginx/nginx.conf",
            "sudo nginx -s reload"
        )

        self.ec2_instance = ec2.Instance(
            self,
            "Instance",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
                cpu_type=ec2.AmazonLinuxCpuType.X86_64,
            ),
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=ec2.BlockDeviceVolume.ebs(50)
                )
            ],
            user_data=user_data,
        )

        common_infra_stack.artifact_bucket.grant_read(self.ec2_instance.role)

        Tags.of(self.ec2_instance).add("deploy_flask_app", "true")
        self.ec2_instance.connections.allow_from_any_ipv4(ec2.Port.tcp(80))

        self.ec2_instance.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:Get*", "s3:List*"],
                resources=[f"arn:aws:s3:::{common_infra_stack.nginx_conf.s3_bucket_name}/*"]
            )
        )

        common_infra_stack.ecr_repository.grant_pull_push(self.ec2_instance.role)
