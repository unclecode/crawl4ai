#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time
import json
import yaml
import requests
import os

# Steps for deployment
STEPS = [
    "refresh_aws_auth",
    "fetch_or_create_vpc_and_subnets",
    "create_ecr_repositories",
    "create_iam_role",
    "create_security_groups",
    "request_acm_certificate",
    "build_and_push_docker",
    "create_task_definition",
    "setup_alb",
    "deploy_ecs_service",
    "configure_custom_domain",
    "test_endpoints"
]

# Utility function to prompt user for confirmation
def confirm_step(step_name):
    while True:
        response = input(f"Proceed with {step_name}? (yes/no): ").strip().lower()
        if response in ["yes", "no"]:
            return response == "yes"
        print("Please enter 'yes' or 'no'.")

# Utility function to run AWS CLI or shell commands and handle errors
def run_command(command, error_message, additional_diagnostics=None, cwd="."):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=cwd)
        return result
    except subprocess.CalledProcessError as e:
        with open("error_context.md", "w") as f:
            f.write(f"{error_message}:\n")
            f.write(f"Command: {' '.join(command)}\n")
            f.write(f"Exit Code: {e.returncode}\n")
            f.write(f"Stdout: {e.stdout}\n")
            f.write(f"Stderr: {e.stderr}\n")
            if additional_diagnostics:
                for diag_cmd in additional_diagnostics:
                    diag_result = subprocess.run(diag_cmd, capture_output=True, text=True)
                    f.write(f"\nDiagnostic command: {' '.join(diag_cmd)}\n")
                    f.write(f"Stdout: {diag_result.stdout}\n")
                    f.write(f"Stderr: {diag_result.stderr}\n")
        raise Exception(f"{error_message}: {e.stderr}")

# Utility function to load or initialize state
def load_state(project_name):
    state_file = f"{project_name}-state.json"
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {"last_step": -1}

# Utility function to save state
def save_state(project_name, state):
    state_file = f"{project_name}-state.json"
    with open(state_file, "w") as f:
        json.dump(state, f, indent=4)

# DNS Check Function
def check_dns_propagation(domain, alb_dns):
    try:
        result = subprocess.run(["dig", "+short", domain], capture_output=True, text=True)
        if alb_dns in result.stdout:
            return True
        return False
    except Exception as e:
        print(f"Failed to check DNS: {e}")
        return False

# Step Functions
def refresh_aws_auth(project_name, state, config):
    if state["last_step"] >= 0:
        print("Skipping refresh_aws_auth (already completed)")
        return
    if not confirm_step("Refresh AWS authentication"):
        sys.exit("User aborted.")
    run_command(
        ["aws", "sts", "get-caller-identity"],
        "Failed to verify AWS credentials"
    )
    print("AWS authentication verified.")
    state["last_step"] = 0
    save_state(project_name, state)

def fetch_or_create_vpc_and_subnets(project_name, state, config):
    if state["last_step"] >= 1:
        print("Skipping fetch_or_create_vpc_and_subnets (already completed)")
        return state["vpc_id"], state["public_subnets"]
    if not confirm_step("Fetch or Create VPC and Subnets"):
        sys.exit("User aborted.")
    
    # Fetch AWS account ID
    result = run_command(
        ["aws", "sts", "get-caller-identity"],
        "Failed to get AWS account ID"
    )
    account_id = json.loads(result.stdout)["Account"]
    
    # Fetch default VPC
    result = run_command(
        ["aws", "ec2", "describe-vpcs", "--filters", "Name=isDefault,Values=true", "--region", config["aws_region"]],
        "Failed to describe VPCs"
    )
    vpcs = json.loads(result.stdout).get("Vpcs", [])
    if not vpcs:
        result = run_command(
            ["aws", "ec2", "create-vpc", "--cidr-block", "10.0.0.0/16", "--region", config["aws_region"]],
            "Failed to create VPC"
        )
        vpc_id = json.loads(result.stdout)["Vpc"]["VpcId"]
        run_command(
            ["aws", "ec2", "modify-vpc-attribute", "--vpc-id", vpc_id, "--enable-dns-hostnames", "--region", config["aws_region"]],
            "Failed to enable DNS hostnames"
        )
    else:
        vpc_id = vpcs[0]["VpcId"]
    
    # Fetch or create subnets
    result = run_command(
        ["aws", "ec2", "describe-subnets", "--filters", f"Name=vpc-id,Values={vpc_id}", "--region", config["aws_region"]],
        "Failed to describe subnets"
    )
    subnets = json.loads(result.stdout).get("Subnets", [])
    if len(subnets) < 2:
        azs = json.loads(run_command(
            ["aws", "ec2", "describe-availability-zones", "--region", config["aws_region"]],
            "Failed to describe availability zones"
        ).stdout)["AvailabilityZones"][:2]
        subnet_ids = []
        for i, az in enumerate(azs):
            az_name = az["ZoneName"]
            result = run_command(
                ["aws", "ec2", "create-subnet", "--vpc-id", vpc_id, "--cidr-block", f"10.0.{i}.0/24", "--availability-zone", az_name, "--region", config["aws_region"]],
                f"Failed to create subnet in {az_name}"
            )
            subnet_id = json.loads(result.stdout)["Subnet"]["SubnetId"]
            subnet_ids.append(subnet_id)
            run_command(
                ["aws", "ec2", "modify-subnet-attribute", "--subnet-id", subnet_id, "--map-public-ip-on-launch", "--region", config["aws_region"]],
                f"Failed to make subnet {subnet_id} public"
            )
    else:
        subnet_ids = [s["SubnetId"] for s in subnets[:2]]
    
    # Ensure internet gateway
    result = run_command(
        ["aws", "ec2", "describe-internet-gateways", "--filters", f"Name=attachment.vpc-id,Values={vpc_id}", "--region", config["aws_region"]],
        "Failed to describe internet gateways"
    )
    igws = json.loads(result.stdout).get("InternetGateways", [])
    if not igws:
        result = run_command(
            ["aws", "ec2", "create-internet-gateway", "--region", config["aws_region"]],
            "Failed to create internet gateway"
        )
        igw_id = json.loads(result.stdout)["InternetGateway"]["InternetGatewayId"]
        run_command(
            ["aws", "ec2", "attach-internet-gateway", "--vpc-id", vpc_id, "--internet-gateway-id", igw_id, "--region", config["aws_region"]],
            "Failed to attach internet gateway"
        )
    
    state["vpc_id"] = vpc_id
    state["public_subnets"] = subnet_ids
    state["last_step"] = 1
    save_state(project_name, state)
    print(f"VPC ID: {vpc_id}, Subnets: {subnet_ids}")
    return vpc_id, subnet_ids

def create_ecr_repositories(project_name, state, config):
    if state["last_step"] >= 2:
        print("Skipping create_ecr_repositories (already completed)")
        return
    if not confirm_step("Create ECR Repositories"):
        sys.exit("User aborted.")
    
    account_id = json.loads(run_command(
        ["aws", "sts", "get-caller-identity"],
        "Failed to get AWS account ID"
    ).stdout)["Account"]
    repos = [project_name, f"{project_name}-nginx"]
    for repo in repos:
        result = subprocess.run(
            ["aws", "ecr", "describe-repositories", "--repository-names", repo, "--region", config["aws_region"]],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            run_command(
                ["aws", "ecr", "create-repository", "--repository-name", repo, "--region", config["aws_region"]],
                f"Failed to create ECR repository {repo}"
            )
        print(f"ECR repository {repo} is ready.")
    state["last_step"] = 2
    save_state(project_name, state)

def create_iam_role(project_name, state, config):
    if state["last_step"] >= 3:
        print("Skipping create_iam_role (already completed)")
        return
    if not confirm_step("Create IAM Role"):
        sys.exit("User aborted.")
    
    account_id = json.loads(run_command(
        ["aws", "sts", "get-caller-identity"],
        "Failed to get AWS account ID"
    ).stdout)["Account"]
    role_name = "ecsTaskExecutionRole"
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    with open("trust_policy.json", "w") as f:
        json.dump(trust_policy, f)
    
    result = subprocess.run(
        ["aws", "iam", "get-role", "--role-name", role_name],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        run_command(
            ["aws", "iam", "create-role", "--role-name", role_name, "--assume-role-policy-document", "file://trust_policy.json"],
            f"Failed to create IAM role {role_name}"
        )
    run_command(
        ["aws", "iam", "attach-role-policy", "--role-name", role_name, "--policy-arn", "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"],
        "Failed to attach ECS task execution policy"
    )
    os.remove("trust_policy.json")
    state["execution_role_arn"] = f"arn:aws:iam::{account_id}:role/{role_name}"
    state["last_step"] = 3
    save_state(project_name, state)
    print(f"IAM role {role_name} configured.")

def create_security_groups(project_name, state, config):
    if state["last_step"] >= 4:
        print("Skipping create_security_groups (already completed)")
        return state["alb_sg_id"], state["ecs_sg_id"]
    if not confirm_step("Create Security Groups"):
        sys.exit("User aborted.")
    
    vpc_id = state["vpc_id"]
    alb_sg_name = f"{project_name}-alb-sg"
    result = run_command(
        ["aws", "ec2", "describe-security-groups", "--filters", f"Name=vpc-id,Values={vpc_id}", f"Name=group-name,Values={alb_sg_name}", "--region", config["aws_region"]],
        "Failed to describe ALB security group"
    )
    if not json.loads(result.stdout).get("SecurityGroups"):
        result = run_command(
            ["aws", "ec2", "create-security-group", "--group-name", alb_sg_name, "--description", "Security group for ALB", "--vpc-id", vpc_id, "--region", config["aws_region"]],
            "Failed to create ALB security group"
        )
        alb_sg_id = json.loads(result.stdout)["GroupId"]
        run_command(
            ["aws", "ec2", "authorize-security-group-ingress", "--group-id", alb_sg_id, "--protocol", "tcp", "--port", "80", "--cidr", "0.0.0.0/0", "--region", config["aws_region"]],
            "Failed to authorize HTTP ingress"
        )
        run_command(
            ["aws", "ec2", "authorize-security-group-ingress", "--group-id", alb_sg_id, "--protocol", "tcp", "--port", "443", "--cidr", "0.0.0.0/0", "--region", config["aws_region"]],
            "Failed to authorize HTTPS ingress"
        )
    else:
        alb_sg_id = json.loads(result.stdout)["SecurityGroups"][0]["GroupId"]
    
    ecs_sg_name = f"{project_name}-ecs-sg"
    result = run_command(
        ["aws", "ec2", "describe-security-groups", "--filters", f"Name=vpc-id,Values={vpc_id}", f"Name=group-name,Values={ecs_sg_name}", "--region", config["aws_region"]],
        "Failed to describe ECS security group"
    )
    if not json.loads(result.stdout).get("SecurityGroups"):
        result = run_command(
            ["aws", "ec2", "create-security-group", "--group-name", ecs_sg_name, "--description", "Security group for ECS tasks", "--vpc-id", vpc_id, "--region", config["aws_region"]],
            "Failed to create ECS security group"
        )
        ecs_sg_id = json.loads(result.stdout)["GroupId"]
        run_command(
            ["aws", "ec2", "authorize-security-group-ingress", "--group-id", ecs_sg_id, "--protocol", "tcp", "--port", "80", "--source-group", alb_sg_id, "--region", config["aws_region"]],
            "Failed to authorize ECS ingress"
        )
    else:
        ecs_sg_id = json.loads(result.stdout)["SecurityGroups"][0]["GroupId"]
    
    state["alb_sg_id"] = alb_sg_id
    state["ecs_sg_id"] = ecs_sg_id
    state["last_step"] = 4
    save_state(project_name, state)
    print("Security groups configured.")
    return alb_sg_id, ecs_sg_id

def request_acm_certificate(project_name, state, config):
    if state["last_step"] >= 5:
        print("Skipping request_acm_certificate (already completed)")
        return state["cert_arn"]
    if not confirm_step("Request ACM Certificate"):
        sys.exit("User aborted.")
    
    domain_name = config["domain_name"]
    result = run_command(
        ["aws", "acm", "describe-certificates", "--certificate-statuses", "ISSUED", "--region", config["aws_region"]],
        "Failed to describe certificates"
    )
    certificates = json.loads(result.stdout).get("CertificateSummaryList", [])
    cert_arn = next((c["CertificateArn"] for c in certificates if c["DomainName"] == domain_name), None)
    
    if not cert_arn:
        result = run_command(
            ["aws", "acm", "request-certificate", "--domain-name", domain_name, "--validation-method", "DNS", "--region", config["aws_region"]],
            "Failed to request ACM certificate"
        )
        cert_arn = json.loads(result.stdout)["CertificateArn"]
        
        time.sleep(10)
        result = run_command(
            ["aws", "acm", "describe-certificate", "--certificate-arn", cert_arn, "--region", config["aws_region"]],
            "Failed to describe certificate"
        )
        cert_details = json.loads(result.stdout)["Certificate"]
        dns_validations = cert_details.get("DomainValidationOptions", [])
        for validation in dns_validations:
            if validation["ValidationMethod"] == "DNS" and "ResourceRecord" in validation:
                record = validation["ResourceRecord"]
                print(f"Please add this DNS record to validate the certificate for {domain_name}:")
                print(f"Name: {record['Name']}")
                print(f"Type: {record['Type']}")
                print(f"Value: {record['Value']}")
        print("Press Enter after adding the DNS record...")
        input()
        
        while True:
            result = run_command(
                ["aws", "acm", "describe-certificate", "--certificate-arn", cert_arn, "--region", config["aws_region"]],
                "Failed to check certificate status"
            )
            status = json.loads(result.stdout)["Certificate"]["Status"]
            if status == "ISSUED":
                break
            elif status in ["FAILED", "REVOKED", "INACTIVE"]:
                print("Certificate issuance failed.")
                sys.exit(1)
            time.sleep(10)
    
    state["cert_arn"] = cert_arn
    state["last_step"] = 5
    save_state(project_name, state)
    print(f"Certificate ARN: {cert_arn}")
    return cert_arn

def build_and_push_docker(project_name, state, config):
    if state["last_step"] >= 6:
        print("Skipping build_and_push_docker (already completed)")
        return state["fastapi_image"], state["nginx_image"]
    if not confirm_step("Build and Push Docker Images"):
        sys.exit("User aborted.")
    
    with open("./version.txt", "r") as f:
        version = f.read().strip()
    
    account_id = json.loads(run_command(
        ["aws", "sts", "get-caller-identity"],
        "Failed to get AWS account ID"
    ).stdout)["Account"]
    region = config["aws_region"]
    
    login_password = run_command(
        ["aws", "ecr", "get-login-password", "--region", region],
        "Failed to get ECR login password"
    ).stdout.strip()
    run_command(
        ["docker", "login", "--username", "AWS", "--password", login_password, f"{account_id}.dkr.ecr.{region}.amazonaws.com"],
        "Failed to authenticate Docker to ECR"
    )
    
    fastapi_image = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{project_name}:{version}"
    run_command(
        ["docker", "build", "-f", "Dockerfile", "-t", fastapi_image, "."],
        "Failed to build FastAPI Docker image"
    )
    run_command(
        ["docker", "push", fastapi_image],
        "Failed to push FastAPI image"
    )
    
    nginx_image = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{project_name}-nginx:{version}"
    run_command(
        ["docker", "build", "-f", "Dockerfile", "-t", nginx_image, "."],
        "Failed to build Nginx Docker image",
        cwd="./nginx"
    )
    run_command(
        ["docker", "push", nginx_image],
        "Failed to push Nginx image"
    )
    
    state["fastapi_image"] = fastapi_image
    state["nginx_image"] = nginx_image
    state["last_step"] = 6
    save_state(project_name, state)
    print("Docker images built and pushed.")
    return fastapi_image, nginx_image

def create_task_definition(project_name, state, config):
    if state["last_step"] >= 7:
        print("Skipping create_task_definition (already completed)")
        return state["task_def_arn"]
    if not confirm_step("Create Task Definition"):
        sys.exit("User aborted.")
    
    log_group = f"/ecs/{project_name}-logs"
    result = run_command(
        ["aws", "logs", "describe-log-groups", "--log-group-name-prefix", log_group, "--region", config["aws_region"]],
        "Failed to describe log groups"
    )
    if not any(lg["logGroupName"] == log_group for lg in json.loads(result.stdout).get("logGroups", [])):
        run_command(
            ["aws", "logs", "create-log-group", "--log-group-name", log_group, "--region", config["aws_region"]],
            f"Failed to create log group {log_group}"
        )
    
    task_definition = {
        "family": f"{project_name}-taskdef",
        "networkMode": "awsvpc",
        "requiresCompatibilities": ["FARGATE"],
        "cpu": "512",
        "memory": "2048",
        "executionRoleArn": state["execution_role_arn"],
        "containerDefinitions": [
            {
                "name": "fastapi",
                "image": state["fastapi_image"],
                "portMappings": [{"containerPort": 8000, "hostPort": 8000, "protocol": "tcp"}],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": log_group,
                        "awslogs-region": config["aws_region"],
                        "awslogs-stream-prefix": "fastapi"
                    }
                }
            },
            {
                "name": "nginx",
                "image": state["nginx_image"],
                "portMappings": [{"containerPort": 80, "hostPort": 80, "protocol": "tcp"}],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": log_group,
                        "awslogs-region": config["aws_region"],
                        "awslogs-stream-prefix": "nginx"
                    }
                }
            }
        ]
    }
    
    with open("task_def.json", "w") as f:
        json.dump(task_definition, f)
    result = run_command(
        ["aws", "ecs", "register-task-definition", "--cli-input-json", "file://task_def.json", "--region", config["aws_region"]],
        "Failed to register task definition"
    )
    task_def_arn = json.loads(result.stdout)["taskDefinition"]["taskDefinitionArn"]
    os.remove("task_def.json")
    
    state["task_def_arn"] = task_def_arn
    state["last_step"] = 7
    save_state(project_name, state)
    print("Task definition created.")
    return task_def_arn

def setup_alb(project_name, state, config):
    if state["last_step"] >= 8:
        print("Skipping setup_alb (already completed)")
        return state["alb_arn"], state["tg_arn"], state["alb_dns"]
    if not confirm_step("Set Up ALB"):
        sys.exit("User aborted.")
    
    vpc_id = state["vpc_id"]
    public_subnets = state["public_subnets"]
    alb_name = f"{project_name}-alb"
    
    result = subprocess.run(
        ["aws", "elbv2", "describe-load-balancers", "--names", alb_name, "--region", config["aws_region"]],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        run_command(
            ["aws", "elbv2", "create-load-balancer", "--name", alb_name, "--subnets"] + public_subnets + ["--security-groups", state["alb_sg_id"], "--region", config["aws_region"]],
            "Failed to create ALB"
        )
    alb_arn = json.loads(run_command(
        ["aws", "elbv2", "describe-load-balancers", "--names", alb_name, "--region", config["aws_region"]],
        "Failed to describe ALB"
    ).stdout)["LoadBalancers"][0]["LoadBalancerArn"]
    alb_dns = json.loads(run_command(
        ["aws", "elbv2", "describe-load-balancers", "--names", alb_name, "--region", config["aws_region"]],
        "Failed to get ALB DNS name"
    ).stdout)["LoadBalancers"][0]["DNSName"]
    
    tg_name = f"{project_name}-tg"
    result = subprocess.run(
        ["aws", "elbv2", "describe-target-groups", "--names", tg_name, "--region", config["aws_region"]],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        run_command(
            ["aws", "elbv2", "create-target-group", "--name", tg_name, "--protocol", "HTTP", "--port", "80", "--vpc-id", vpc_id, "--region", config["aws_region"]],
            "Failed to create target group"
        )
    tg_arn = json.loads(run_command(
        ["aws", "elbv2", "describe-target-groups", "--names", tg_name, "--region", config["aws_region"]],
        "Failed to describe target group"
    ).stdout)["TargetGroups"][0]["TargetGroupArn"]
    
    result = run_command(
        ["aws", "elbv2", "describe-listeners", "--load-balancer-arn", alb_arn, "--region", config["aws_region"]],
        "Failed to describe listeners"
    )
    listeners = json.loads(result.stdout).get("Listeners", [])
    if not any(l["Port"] == 80 for l in listeners):
        run_command(
            ["aws", "elbv2", "create-listener", "--load-balancer-arn", alb_arn, "--protocol", "HTTP", "--port", "80", "--default-actions", "Type=redirect,RedirectConfig={Protocol=HTTPS,Port=443,StatusCode=HTTP_301}", "--region", config["aws_region"]],
            "Failed to create HTTP listener"
        )
    if not any(l["Port"] == 443 for l in listeners):
        run_command(
            ["aws", "elbv2", "create-listener", "--load-balancer-arn", alb_arn, "--protocol", "HTTPS", "--port", "443", "--certificates", f"CertificateArn={state['cert_arn']}", "--default-actions", f"Type=forward,TargetGroupArn={tg_arn}", "--region", config["aws_region"]],
            "Failed to create HTTPS listener"
        )
    
    state["alb_arn"] = alb_arn
    state["tg_arn"] = tg_arn
    state["alb_dns"] = alb_dns
    state["last_step"] = 8
    save_state(project_name, state)
    print("ALB configured.")
    return alb_arn, tg_arn, alb_dns

def deploy_ecs_service(project_name, state, config):
    if state["last_step"] >= 9:
        print("Skipping deploy_ecs_service (already completed)")
        return
    if not confirm_step("Deploy ECS Service"):
        sys.exit("User aborted.")
    
    cluster_name = f"{project_name}-cluster"
    result = run_command(
        ["aws", "ecs", "describe-clusters", "--clusters", cluster_name, "--region", config["aws_region"]],
        "Failed to describe clusters"
    )
    if not json.loads(result.stdout).get("clusters"):
        run_command(
            ["aws", "ecs", "create-cluster", "--cluster-name", cluster_name, "--region", config["aws_region"]],
            "Failed to create ECS cluster"
        )
    
    service_name = f"{project_name}-service"
    result = run_command(
        ["aws", "ecs", "describe-services", "--cluster", cluster_name, "--services", service_name, "--region", config["aws_region"]],
        "Failed to describe services",
        additional_diagnostics=[["aws", "ecs", "list-tasks", "--cluster", cluster_name, "--service-name", service_name, "--region", config["aws_region"]]]
    )
    services = json.loads(result.stdout).get("services", [])
    if not services or services[0]["status"] == "INACTIVE":
        run_command(
            ["aws", "ecs", "create-service", "--cluster", cluster_name, "--service-name", service_name, "--task-definition", state["task_def_arn"], "--desired-count", "1", "--launch-type", "FARGATE", "--network-configuration", f"awsvpcConfiguration={{subnets={json.dumps(state['public_subnets'])},securityGroups=[{state['ecs_sg_id']}],assignPublicIp=ENABLED}}", "--load-balancers", f"targetGroupArn={state['tg_arn']},containerName=nginx,containerPort=80", "--region", config["aws_region"]],
            "Failed to create ECS service"
        )
    else:
        run_command(
            ["aws", "ecs", "update-service", "--cluster", cluster_name, "--service", service_name, "--task-definition", state["task_def_arn"], "--region", config["aws_region"]],
            "Failed to update ECS service"
        )
    
    state["last_step"] = 9
    save_state(project_name, state)
    print("ECS service deployed.")

def configure_custom_domain(project_name, state, config):
    if state["last_step"] >= 10:
        print("Skipping configure_custom_domain (already completed)")
        return
    if not confirm_step("Configure Custom Domain"):
        sys.exit("User aborted.")
    
    domain_name = config["domain_name"]
    alb_dns = state["alb_dns"]
    print(f"Please add a CNAME record for {domain_name} pointing to {alb_dns} in your DNS provider.")
    print("Press Enter after updating the DNS record...")
    input()
    
    while not check_dns_propagation(domain_name, alb_dns):
        print("DNS propagation not complete. Waiting 30 seconds before retrying...")
        time.sleep(30)
    print("DNS propagation confirmed.")
    
    state["last_step"] = 10
    save_state(project_name, state)
    print("Custom domain configured.")

def test_endpoints(project_name, state, config):
    if state["last_step"] >= 11:
        print("Skipping test_endpoints (already completed)")
        return
    if not confirm_step("Test Endpoints"):
        sys.exit("User aborted.")
    
    domain = config["domain_name"]
    time.sleep(30)  # Wait for service to stabilize
    
    response = requests.get(f"https://{domain}/health", verify=False)
    if response.status_code != 200:
        with open("error_context.md", "w") as f:
            f.write("Health endpoint test failed:\n")
            f.write(f"Status Code: {response.status_code}\n")
            f.write(f"Response: {response.text}\n")
        sys.exit(1)
    print("Health endpoint test passed.")
    
    payload = {
        "urls": ["https://example.com"],
        "browser_config": {"headless": True},
        "crawler_config": {"stream": False}
    }
    response = requests.post(f"https://{domain}/crawl", json=payload, verify=False)
    if response.status_code != 200:
        with open("error_context.md", "w") as f:
            f.write("Crawl endpoint test failed:\n")
            f.write(f"Status Code: {response.status_code}\n")
            f.write(f"Response: {response.text}\n")
        sys.exit(1)
    print("Crawl endpoint test passed.")
    
    state["last_step"] = 11
    save_state(project_name, state)
    print("Endpoints tested successfully.")

# Main Deployment Function
def deploy(project_name, force=False):
    config_file = f"{project_name}-config.yml"
    if not os.path.exists(config_file):
        print(f"Configuration file {config_file} not found. Run 'init' first.")
        sys.exit(1)
    
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    
    state = load_state(project_name)
    if force:
        state = {"last_step": -1}
    
    last_step = state.get("last_step", -1)
    
    for step_idx, step_name in enumerate(STEPS):
        if step_idx <= last_step:
            print(f"Skipping {step_name} (already completed)")
            continue
        print(f"Executing step: {step_name}")
        func = globals()[step_name]
        if step_name == "fetch_or_create_vpc_and_subnets":
            vpc_id, public_subnets = func(project_name, state, config)
        elif step_name == "create_security_groups":
            alb_sg_id, ecs_sg_id = func(project_name, state, config)
        elif step_name == "request_acm_certificate":
            cert_arn = func(project_name, state, config)
        elif step_name == "build_and_push_docker":
            fastapi_image, nginx_image = func(project_name, state, config)
        elif step_name == "create_task_definition":
            task_def_arn = func(project_name, state, config)
        elif step_name == "setup_alb":
            alb_arn, tg_arn, alb_dns = func(project_name, state, config)
        elif step_name == "deploy_ecs_service":
            func(project_name, state, config)
        elif step_name == "configure_custom_domain":
            func(project_name, state, config)
        elif step_name == "test_endpoints":
            func(project_name, state, config)
        else:
            func(project_name, state, config)

# Init Command
def init(project_name, domain_name, aws_region):
    config = {
        "project_name": project_name,
        "domain_name": domain_name,
        "aws_region": aws_region
    }
    config_file = f"{project_name}-config.yml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    print(f"Configuration file {config_file} created.")

# Argument Parser
parser = argparse.ArgumentParser(description="Crawl4AI Deployment Script")
subparsers = parser.add_subparsers(dest="command")

# Init Parser
init_parser = subparsers.add_parser("init", help="Initialize configuration")
init_parser.add_argument("--project", required=True, help="Project name")
init_parser.add_argument("--domain", required=True, help="Domain name")
init_parser.add_argument("--region", required=True, help="AWS region")

# Deploy Parser
deploy_parser = subparsers.add_parser("deploy", help="Deploy the project")
deploy_parser.add_argument("--project", required=True, help="Project name")
deploy_parser.add_argument("--force", action="store_true", help="Force redeployment from start")

args = parser.parse_args()

if args.command == "init":
    init(args.project, args.domain, args.region)
elif args.command == "deploy":
    deploy(args.project, args.force)
else:
    parser.print_help()