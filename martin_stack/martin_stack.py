import os
from typing import Optional

from aws_cdk import (
    Stack,
    Duration,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_apigatewayv2_alpha as apigwv2_alpha,
    aws_apigatewayv2_integrations_alpha as apigwv2_integrations_alpha,
)
from constructs import Construct
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), os.environ.get('ENV_FILE_PATH', '.cdk-stack-dev.env'))
)


class MartinStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load environment variables but can be replaced with the actual value
        self.vpc_id = os.environ.get('VPC_ID')
        self.image_uri = os.environ.get('IMAGE_URI')
        self.cluster_name = os.environ.get('CLUSTER_NAME')
        self.service_name = os.environ.get('SERVICE_NAME')
        self.execution_role_arn = os.environ.get('EXECUTION_ROLE_ARN')
        self.ecs_cpu = os.environ.get('ECS_CPU')
        self.ecs_memory = os.environ.get('ECS_MEMORY')
        self.load_balancer_name = os.environ.get('LOAD_BALANCER_NAME')
        self.api_name = os.environ.get('API_NAME')
        self.assign_public_ip = self.str_to_bool(s=os.environ.get('ASSIGN_PUBLIC_IP', 'False'))
        self.private_with_nat = self.str_to_bool(s=os.environ.get('PRIVATE_WITH_NAT', 'True'))
        self.subnet_id = os.environ.get('SUBNET_ID')

        # private variables
        self.__vpc = None
        self.__security_group = None
        self.__iam_role_exc = None
        self.__cluster = None
        self.__task_definition = None
        self.__fargate_service = None
        self.__alb = None
        self.__listener = None

        # Deploy the stack
        self.network_configuration(vpc_id=self.vpc_id)  # 1. Create network configuration (required)
        self.iam_role(role_arn=self.execution_role_arn)  # 2. Create IAM role (required)
        self.cluster_configuration(cluster_name=self.cluster_name)  # 3. Create ECS cluster (required)
        self.task_configuration(
            image_uri=self.image_uri,
            cpu=int(self.ecs_cpu),
            memory=int(self.ecs_memory),
            port=3000
        )  # 4. Create ECS task definition (required)
        self.fargate_service_configuration(service_name=self.service_name,
                                           assign_public_ip=self.assign_public_ip,
                                           private_with_nat=self.private_with_nat,
                                           subnet_id=self.subnet_id)  # 5. Add Fargate service (optional)
        self.load_balancer_configuration(load_balancer_name=self.load_balancer_name,
                                         assign_public_ip=self.assign_public_ip)  # 6. (Optional) If you want to expose the service via ALB (Application Load Balancer) **But if you add this, you need to add api_gateway_configuration() to expose the service together **
        self.api_gateway_configuration(api_name=self.api_name)  # 7. (Optional) Add API Gateway to expose the service to the public **But if you add this, you need to add load_balancer_configuration() to expose the service together **

    def network_configuration(self, vpc_id: str):
        """
        Create network configuration
        """
        # Look up the VPC
        self.__vpc = ec2.Vpc.from_lookup(
            self,
            "VPC",
            vpc_id=vpc_id
        )

        # Create security group
        self.__security_group = ec2.SecurityGroup(
            self,
            'MARTIN_SECURITY_GROUP',
            vpc=self.__vpc,
            description='Allow http access to martin service',
            allow_all_outbound=True
        )

        self.__security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(3000),
            description='Allow http access to martin service'
        )

    def iam_role(self, role_arn: str):
        """
        Create IAM role
        """
        self.__iam_role_exc = iam.Role.from_role_arn(
            self,
            'EXECUTION_ROLE',
            role_arn=role_arn
        )

    def cluster_configuration(self, cluster_name: str):
        """
        Create ECS cluster
        """
        self.__cluster = ecs.Cluster(
            self,
            "MARTIN_ECS_CLUSTER",
            cluster_name=cluster_name,
            vpc=self.__vpc
        )

    def task_configuration(
            self,
            image_uri: str,
            container_name: Optional[str] = 'martin-vector-container',
            cpu: Optional[int] = 256,
            memory: Optional[int] = 512,
            port: Optional[int] = 3000
    ):
        """
        Create ECS task definition
        """
        self.__task_definition = ecs.FargateTaskDefinition(
            self,
            'TASK_DEFINITION',
            task_role=self.__iam_role_exc,
            execution_role=self.__iam_role_exc,
            cpu=cpu,  # Adjust CPU as needed
            memory_limit_mib=memory,  # Adjust memory limit as needed
        )

        # Create log group
        log_group = logs.LogGroup(
            self,
            "LOG_GROUP",
            retention=logs.RetentionDays.ONE_WEEK,  # Adjust retention policy as needed
        )

        # Create log driver
        log_driver = ecs.AwsLogDriver(
            stream_prefix="ContainerLogs",
            log_group=log_group,
        )

        # Health check at path /api.html to make sure the container is up
        self.__task_definition.add_container(
            'MARTIN_VECTOR_TILE_SERVER',
            image=ecs.ContainerImage.from_registry(image_uri),
            container_name=container_name,
            port_mappings=[ecs.PortMapping(container_port=port)],
            logging=log_driver
        )

    def fargate_service_configuration(
            self,
            service_name: str,
            assign_public_ip: Optional[bool] = False,
            private_with_nat: Optional[bool] = True,
            subnet_id: Optional[str] = None
    ):
        """
        Add Fargate service without public IP but expose to public via API Gateway and ALB (Application Load Balancer)
        """
        if private_with_nat is False and subnet_id is None:
            raise ValueError("Subnet ID is required if you want to deploy the service in public subnet")
        print(type(private_with_nat), private_with_nat)
        if assign_public_ip is False:
            subnet_type = ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS) if private_with_nat is True else ec2.SubnetSelection(
                subnets=[ec2.Subnet.from_subnet_id(self, 'Subnet', subnet_id)])
        else:
            subnet_type = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)

        print(f"fargate_service_configuration VPC: {self.vpc_id}, Subnet Type: {subnet_type}")

        self.__fargate_service = ecs.FargateService(
            self,
            'MARIN_FARGATE_SERVICE',
            cluster=self.__cluster,
            task_definition=self.__task_definition,
            platform_version=ecs.FargatePlatformVersion.VERSION1_3,
            vpc_subnets=subnet_type,
            desired_count=1,
            assign_public_ip=assign_public_ip,
            service_name=service_name,
            security_groups=[self.__security_group]
        )
        print(f"Service Name: {service_name}")

    def load_balancer_configuration(self,
                                    load_balancer_name: str,
                                    assign_public_ip: Optional[bool] = False,
                                    health_check_path: Optional[str] = '/health',
                                    port: Optional[int] = 80):
        """
        FOR HTTPS 443 PORT
        - This is optional, if you want to expose your service via HTTPS, you can add the listener and target group below
        listener_https = alb.add_listener(
            'ListenerHTTPS', port=443, protocol=elbv2.ApplicationProtocol.HTTPS)
        listener_https.add_certificates(
            'CertificateTitiler',
            certificates=[
                elbv2.ListenerCertificate.from_arn(
                    os.environ.get('CERTIFICATE_ARN')
                )
            ]
        )

        listener_https.add_target_groups(
            'TargetsTitilerHTTPS',
            target_groups=[target_80],
        )
        END HTTPS 443 PORT
        """

        print(f"load_balancer_configuration assign_public_ip: {assign_public_ip}")
        self.alb = elbv2.ApplicationLoadBalancer(
            self,
            'AlbMartin',
            vpc=self.__vpc,
            internet_facing=assign_public_ip,  # Contain private subnet with NAT gateway
            load_balancer_name=load_balancer_name
        )

        # Add listener
        self.listener = self.alb.add_listener('ListenerMartin', port=port)
        self.listener.add_targets(
            'TargetsMartin',
            target_group_name='MartinEoAPITargetGroup',
            port=port, targets=[self.__fargate_service],
            health_check=elbv2.HealthCheck(
                path=health_check_path,
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                healthy_threshold_count=3,
                unhealthy_threshold_count=3,
            )  # Health check at path /health to make sure the container is up
        )
        print(f"Load Balancer Name: {load_balancer_name}")

    def api_gateway_configuration(self, api_name: str):
        """
        Add API Gateway to expose the service to the public
        """
        # Add CORS options
        print(f"api_gateway_configuration api_name: {api_name}")
        cors_options = apigwv2_alpha.CorsPreflightOptions(
            allow_origins=['*'],
            allow_headers=['*'],
            allow_methods=[apigwv2_alpha.CorsHttpMethod.GET, apigwv2_alpha.CorsHttpMethod.HEAD,
                           apigwv2_alpha.CorsHttpMethod.OPTIONS, apigwv2_alpha.CorsHttpMethod.POST,
                           apigwv2_alpha.CorsHttpMethod.ANY
                           ],
            max_age=Duration.days(10)
        )

        # # Add api gateway
        http_endpoint = apigwv2_alpha.HttpApi(
            self, 'HttpApiVector',
            api_name=api_name,
            cors_preflight=cors_options,
        )

        # Add route to the api gateway and integrate with ALB
        # This is the exposed URL to the public
        http_endpoint.add_routes(
            path="/{proxy+}",
            methods=[apigwv2_alpha.HttpMethod.ANY],
            integration=apigwv2_integrations_alpha.HttpAlbIntegration(
                "DefaultIntegration",
                self.listener,
            ),
        )
        print(f"API Name: {api_name}")

        """
        Things to manually do after the stack is created:
        - Add API gateway to custom domain (if needed)
        - Add SSL certificate to the custom domain (if needed)
        - Add Route53 record to the custom domain (if needed)
        """

    # Utility
    @staticmethod
    def str_to_bool(s: str) -> bool:
        return s.lower() in ['true', 'True', '1', 't', 'y', 'yes']
