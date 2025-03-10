#!/usr/bin/env python3
"""
Crawl4ai AWS Lambda Deployment Script

This script automates the deployment of the Crawl4ai web crawler as an AWS Lambda function,
providing an interactive step-by-step process with rich terminal UI.
"""

import os
import sys
import json
import time
import subprocess
from typing import Optional, Dict, List, Any, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich import print as rprint

# Initialize typer app and console
app = typer.Typer(help="Deploy Crawl4ai to AWS Lambda")
console = Console()

# Default configuration
DEFAULT_CONFIG = {
    "aws_region": "us-east-1",
    "ecr_repository_name": "crawl4ai-lambda",
    "lambda_function_name": "crawl4ai-function",
    "api_gateway_name": "crawl4ai-api",
    "memory_size": 4096,
    "timeout": 300,
    "enable_provisioned_concurrency": False,
    "provisioned_concurrency_count": 2,
    "ephemeral_storage_size": 10240,
}

def run_command(command: List[str], capture_output: bool = False) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, and stderr."""
    console.print(f"[dim]$ {' '.join(command)}[/dim]")
    
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )
    
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    
    if not capture_output:
        if stdout:
            console.print(stdout)
        if stderr and result.returncode != 0:
            console.print(f"[bold red]Error:[/bold red] {stderr}")
    
    return result.returncode, stdout, stderr

def show_step_header(step_number: int, step_title: str) -> None:
    """Display a step header with step number and title."""
    console.print(f"\n[bold blue]Step {step_number}:[/bold blue] [bold]{step_title}[/bold]")
    console.print("=" * 80)

def wait_for_confirmation(message: str = "Press Enter to continue...") -> None:
    """Wait for user confirmation to proceed."""
    console.print()
    Prompt.ask(f"[yellow]{message}[/yellow]")

def check_aws_credentials() -> bool:
    """Check if AWS credentials are configured."""
    code, stdout, stderr = run_command(["aws", "sts", "get-caller-identity"], capture_output=True)
    if code != 0:
        console.print(Panel(
            "[bold red]AWS credentials not found or invalid![/bold red]\n\n"
            "Please configure your AWS credentials by running:\n"
            "  aws configure\n\n"
            "You'll need to provide your AWS Access Key ID, Secret Access Key, and default region.",
            title="AWS Authentication Error",
            expand=False
        ))
        return False
    
    try:
        identity = json.loads(stdout)
        console.print(f"[green]Authenticated as:[/green] [bold]{identity.get('Arn')}[/bold]")
        return True
    except json.JSONDecodeError:
        console.print("[bold red]Error parsing AWS identity information[/bold red]")
        return False

def check_prerequisites() -> bool:
    """Check if all required tools are installed."""
    prerequisites = {
        "aws": "AWS CLI",
        "docker": "Docker"
    }
    
    all_installed = True
    
    with console.status("[bold blue]Checking prerequisites...[/bold blue]"):
        for cmd, name in prerequisites.items():
            try:
                subprocess.run(
                    ["which", cmd],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                console.print(f"[green]✓[/green] {name} is installed")
            except subprocess.CalledProcessError:
                console.print(f"[red]✗[/red] {name} is [bold red]not installed[/bold red]")
                all_installed = False
    
    if not all_installed:
        console.print(Panel(
            "Please install the missing prerequisites and try again.",
            title="Missing Prerequisites",
            expand=False
        ))
    
    return all_installed

def verify_iam_role(config: Dict[str, Any]) -> Optional[str]:
    """Verify the Lambda execution role exists and return its ARN."""
    role_name = "lambda-execution-role"
    with console.status(f"[bold blue]Verifying IAM role '{role_name}'...[/bold blue]"):
        code, stdout, stderr = run_command(
            ["aws", "iam", "get-role", "--role-name", role_name, "--query", "Role.Arn", "--output", "text"],
            capture_output=True
        )
        
        if code != 0:
            console.print(f"[bold yellow]IAM role '{role_name}' not found. Creating it...[/bold yellow]")
            # Create basic execution role
            policy_document = json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            })
            
            code, create_stdout, create_stderr = run_command([
                "aws", "iam", "create-role",
                "--role-name", role_name,
                "--assume-role-policy-document", policy_document,
                "--query", "Role.Arn",
                "--output", "text"
            ], capture_output=True)
            
            if code != 0:
                console.print(f"[bold red]Failed to create IAM role:[/bold red] {create_stderr}")
                return None
            
            # Attach basic Lambda execution policy
            run_command([
                "aws", "iam", "attach-role-policy",
                "--role-name", role_name,
                "--policy-arn", "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            ])
            
            console.print(f"[green]Created IAM role:[/green] {create_stdout.strip()}")
            return create_stdout.strip()
        else:
            console.print(f"[green]Found IAM role:[/green] {stdout.strip()}")
            return stdout.strip()

def build_docker_image(config: Dict[str, Any]) -> bool:
    """Build the Docker image for the Lambda function."""
    show_step_header(1, "Building Docker Image")
    console.print("This step will build the Docker image that contains Crawl4ai and its dependencies.")
    
    if not os.path.exists("Dockerfile"):
        console.print("[bold red]Error:[/bold red] Dockerfile not found in the current directory.")
        return False
    
    if not os.path.exists("lambda_function.py"):
        console.print("[bold red]Error:[/bold red] lambda_function.py not found in the current directory.")
        return False
    
    wait_for_confirmation()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Building Docker image...[/bold blue]"),
        console=console
    ) as progress:
        progress.add_task("build", total=None)
        code, stdout, stderr = run_command([
            "docker", "build", "-t", config["ecr_repository_name"], "."
        ])
    
    if code != 0:
        console.print("[bold red]Docker build failed![/bold red]")
        return False
    
    console.print("[bold green]Docker image built successfully![/bold green]")
    return True

def setup_ecr_repository(config: Dict[str, Any]) -> Optional[str]:
    """Create ECR repository if it doesn't exist and return repository URI."""
    show_step_header(2, "Setting Up Amazon ECR Repository")
    console.print("This step will create an Amazon ECR repository to store the Docker image.")
    
    wait_for_confirmation()
    
    # Check if repository exists
    code, stdout, stderr = run_command([
        "aws", "ecr", "describe-repositories",
        "--repository-names", config["ecr_repository_name"],
        "--region", config["aws_region"],
        "--query", "repositories[0].repositoryUri",
        "--output", "text"
    ], capture_output=True)
    
    if code != 0:
        console.print(f"[yellow]Creating new ECR repository: {config['ecr_repository_name']}[/yellow]")
        code, create_stdout, create_stderr = run_command([
            "aws", "ecr", "create-repository",
            "--repository-name", config["ecr_repository_name"],
            "--region", config["aws_region"],
            "--query", "repository.repositoryUri",
            "--output", "text"
        ], capture_output=True)
        
        if code != 0:
            console.print(f"[bold red]Failed to create ECR repository:[/bold red] {create_stderr}")
            return None
        
        repository_uri = create_stdout.strip()
    else:
        repository_uri = stdout.strip()
        console.print(f"[green]Found existing ECR repository:[/green] {repository_uri}")
    
    return repository_uri

def push_image_to_ecr(config: Dict[str, Any], repository_uri: str) -> bool:
    """Push the Docker image to ECR."""
    show_step_header(3, "Pushing Docker Image to ECR")
    console.print("This step will push the Docker image to Amazon ECR.")
    
    wait_for_confirmation()
    
    # Get account ID
    code, account_id, stderr = run_command([
        "aws", "sts", "get-caller-identity",
        "--query", "Account",
        "--output", "text"
    ], capture_output=True)
    
    if code != 0:
        console.print("[bold red]Failed to get AWS account ID[/bold red]")
        return False
    
    account_id = account_id.strip()
    
    # Get ECR login password
    console.print("[blue]Logging in to Amazon ECR...[/blue]")
    code, password, stderr = run_command([
        "aws", "ecr", "get-login-password",
        "--region", config["aws_region"]
    ], capture_output=True)
    
    if code != 0:
        console.print("[bold red]Failed to get ECR login password[/bold red]")
        return False
    
    # Log in to ECR
    login_cmd = ["docker", "login", "--username", "AWS", "--password-stdin", 
                 f"{account_id}.dkr.ecr.{config['aws_region']}.amazonaws.com"]
    
    login_process = subprocess.Popen(
        login_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = login_process.communicate(input=password)
    
    if login_process.returncode != 0:
        console.print(f"[bold red]Failed to log in to ECR:[/bold red] {stderr}")
        return False
    
    console.print("[green]Successfully logged in to ECR[/green]")
    
    # Tag and push image
    console.print(f"[blue]Tagging image as {repository_uri}:latest[/blue]")
    code, stdout, stderr = run_command([
        "docker", "tag",
        f"{config['ecr_repository_name']}:latest",
        f"{repository_uri}:latest"
    ])
    
    if code != 0:
        console.print("[bold red]Failed to tag Docker image[/bold red]")
        return False
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Pushing image to ECR...[/bold blue]"),
        console=console
    ) as progress:
        progress.add_task("push", total=None)
        code, stdout, stderr = run_command([
            "docker", "push", f"{repository_uri}:latest"
        ])
    
    if code != 0:
        console.print("[bold red]Failed to push image to ECR[/bold red]")
        return False
    
    console.print("[bold green]Successfully pushed image to ECR![/bold green]")
    return True

def deploy_lambda_function(config: Dict[str, Any], repository_uri: str, role_arn: str) -> bool:
    """Create or update Lambda function."""
    show_step_header(4, "Deploying Lambda Function")
    console.print("This step will create or update the AWS Lambda function.")
    
    wait_for_confirmation()
    
    # Check if Lambda function exists
    code, stdout, stderr = run_command([
        "aws", "lambda", "list-functions",
        "--region", config["aws_region"],
        "--query", f"Functions[?FunctionName=='{config['lambda_function_name']}'].FunctionName",
        "--output", "text"
    ], capture_output=True)
    
    function_exists = stdout.strip() != ""
    
    if function_exists:
        console.print(f"[yellow]Updating existing Lambda function: {config['lambda_function_name']}[/yellow]")
        
        # Update function code
        with console.status("[bold blue]Updating Lambda function code...[/bold blue]"):
            code, stdout, stderr = run_command([
                "aws", "lambda", "update-function-code",
                "--region", config["aws_region"],
                "--function-name", config["lambda_function_name"],
                "--image-uri", f"{repository_uri}:latest"
            ])
            
            if code != 0:
                console.print("[bold red]Failed to update Lambda function code[/bold red]")
                return False
        
        # Update function configuration
        with console.status("[bold blue]Updating Lambda function configuration...[/bold blue]"):
            code, stdout, stderr = run_command([
                "aws", "lambda", "update-function-configuration",
                "--region", config["aws_region"],
                "--function-name", config["lambda_function_name"],
                "--timeout", str(config["timeout"]),
                "--memory-size", str(config["memory_size"]),
                "--ephemeral-storage", f"Size={config['ephemeral_storage_size']}",
                "--environment", f"Variables={{"
                    f"CRAWL4_AI_BASE_DIRECTORY=/tmp/.crawl4ai,"
                    f"HOME=/tmp,"
                    f"PLAYWRIGHT_BROWSERS_PATH=/function/pw-browsers"
                f"}}"
            ])
            
            if code != 0:
                console.print("[bold red]Failed to update Lambda function configuration[/bold red]")
                return False
    else:
        console.print(f"[blue]Creating new Lambda function: {config['lambda_function_name']}[/blue]")
        
        with console.status("[bold blue]Creating Lambda function...[/bold blue]"):
            code, stdout, stderr = run_command([
                "aws", "lambda", "create-function",
                "--region", config["aws_region"],
                "--function-name", config["lambda_function_name"],
                "--package-type", "Image",
                "--code", f"ImageUri={repository_uri}:latest",
                "--role", role_arn,
                "--timeout", str(config["timeout"]),
                "--memory-size", str(config["memory_size"]),
                "--ephemeral-storage", f"Size={config['ephemeral_storage_size']}",
                "--environment", f"Variables={{"
                    f"CRAWL4_AI_BASE_DIRECTORY=/tmp/.crawl4ai,"
                    f"HOME=/tmp,"
                    f"PLAYWRIGHT_BROWSERS_PATH=/function/pw-browsers"
                f"}}"
            ])
            
            if code != 0:
                console.print("[bold red]Failed to create Lambda function[/bold red]")
                return False
    
    console.print("[bold green]Lambda function deployed successfully![/bold green]")
    return True

def setup_api_gateway(config: Dict[str, Any]) -> Optional[str]:
    """Create or update API Gateway."""
    show_step_header(5, "Setting Up API Gateway")
    console.print("This step will create an API Gateway to expose your Lambda function as a REST API.")
    
    wait_for_confirmation()
    
    # Check if API Gateway exists
    code, api_id, stderr = run_command([
        "aws", "apigateway", "get-rest-apis",
        "--region", config["aws_region"],
        "--query", f"items[?name=='{config['api_gateway_name']}'].id",
        "--output", "text"
    ], capture_output=True)
    
    api_id = api_id.strip()
    
    if not api_id:
        console.print(f"[blue]Creating new API Gateway: {config['api_gateway_name']}[/blue]")
        
        # Create API Gateway
        code, api_id, stderr = run_command([
            "aws", "apigateway", "create-rest-api",
            "--name", config["api_gateway_name"],
            "--region", config["aws_region"],
            "--query", "id",
            "--output", "text"
        ], capture_output=True)
        
        if code != 0:
            console.print("[bold red]Failed to create API Gateway[/bold red]")
            return None
        
        api_id = api_id.strip()
        
        # Get root resource ID
        code, parent_id, stderr = run_command([
            "aws", "apigateway", "get-resources",
            "--rest-api-id", api_id,
            "--region", config["aws_region"],
            "--query", "items[?path=='/'].id",
            "--output", "text"
        ], capture_output=True)
        
        if code != 0:
            console.print("[bold red]Failed to get API Gateway root resource[/bold red]")
            return None
        
        parent_id = parent_id.strip()
        
        # Create resource
        console.print("[blue]Creating API Gateway resource...[/blue]")
        code, resource_id, stderr = run_command([
            "aws", "apigateway", "create-resource",
            "--rest-api-id", api_id,
            "--region", config["aws_region"],
            "--parent-id", parent_id,
            "--path-part", "crawl",
            "--query", "id",
            "--output", "text"
        ], capture_output=True)
        
        if code != 0:
            console.print("[bold red]Failed to create API Gateway resource[/bold red]")
            return None
        
        resource_id = resource_id.strip()
        
        # Create POST method
        console.print("[blue]Creating POST method...[/blue]")
        code, stdout, stderr = run_command([
            "aws", "apigateway", "put-method",
            "--rest-api-id", api_id,
            "--resource-id", resource_id,
            "--http-method", "POST",
            "--authorization-type", "NONE",
            "--region", config["aws_region"]
        ])
        
        if code != 0:
            console.print("[bold red]Failed to create API Gateway method[/bold red]")
            return None
        
        # Get Lambda function ARN
        code, lambda_arn, stderr = run_command([
            "aws", "lambda", "get-function",
            "--function-name", config["lambda_function_name"],
            "--region", config["aws_region"],
            "--query", "Configuration.FunctionArn",
            "--output", "text"
        ], capture_output=True)
        
        if code != 0:
            console.print("[bold red]Failed to get Lambda function ARN[/bold red]")
            return None
        
        lambda_arn = lambda_arn.strip()
        
        # Set Lambda integration
        console.print("[blue]Setting up Lambda integration...[/blue]")
        code, stdout, stderr = run_command([
            "aws", "apigateway", "put-integration",
            "--rest-api-id", api_id,
            "--resource-id", resource_id,
            "--http-method", "POST",
            "--type", "AWS_PROXY",
            "--integration-http-method", "POST",
            "--uri", f"arn:aws:apigateway:{config['aws_region']}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations",
            "--region", config["aws_region"]
        ])
        
        if code != 0:
            console.print("[bold red]Failed to set API Gateway integration[/bold red]")
            return None
        
        # Deploy API
        console.print("[blue]Deploying API...[/blue]")
        code, stdout, stderr = run_command([
            "aws", "apigateway", "create-deployment",
            "--rest-api-id", api_id,
            "--stage-name", "prod",
            "--region", config["aws_region"]
        ])
        
        if code != 0:
            console.print("[bold red]Failed to deploy API Gateway[/bold red]")
            return None
        
        # Set Lambda permission
        account_id = lambda_arn.split(":")[4]
        
        console.print("[blue]Setting Lambda permissions...[/blue]")
        code, stdout, stderr = run_command([
            "aws", "lambda", "add-permission",
            "--function-name", config["lambda_function_name"],
            "--statement-id", "apigateway",
            "--action", "lambda:InvokeFunction",
            "--principal", "apigateway.amazonaws.com",
            "--source-arn", f"arn:aws:execute-api:{config['aws_region']}:{account_id}:{api_id}/*/POST/crawl",
            "--region", config["aws_region"]
        ])
        
        if code != 0:
            console.print("[bold red]Failed to set Lambda permission[/bold red]")
            return None
    else:
        console.print(f"[green]Found existing API Gateway:[/green] {api_id}")
    
    console.print("[bold green]API Gateway setup complete![/bold green]")
    return api_id

def configure_provisioned_concurrency(config: Dict[str, Any]) -> bool:
    """Configure provisioned concurrency if enabled."""
    if not config["enable_provisioned_concurrency"]:
        console.print("[yellow]Skipping provisioned concurrency setup (not enabled)[/yellow]")
        return True
    
    show_step_header(6, "Setting Up Provisioned Concurrency")
    console.print("This step will configure provisioned concurrency to avoid cold starts.")
    
    wait_for_confirmation()
    
    # Publish a version
    console.print("[blue]Publishing Lambda version...[/blue]")
    code, version, stderr = run_command([
        "aws", "lambda", "publish-version",
        "--function-name", config["lambda_function_name"],
        "--region", config["aws_region"],
        "--query", "Version",
        "--output", "text"
    ], capture_output=True)
    
    if code != 0:
        console.print("[bold red]Failed to publish Lambda version[/bold red]")
        return False
    
    version = version.strip()
    console.print(f"[green]Published version:[/green] {version}")
    
    # Check if alias exists
    alias_exists = False
    code, stdout, stderr = run_command([
        "aws", "lambda", "get-alias",
        "--function-name", config["lambda_function_name"],
        "--name", "prod",
        "--region", config["aws_region"]
    ], capture_output=True)
    
    alias_exists = code == 0
    
    # Create or update alias
    if alias_exists:
        console.print("[blue]Updating 'prod' alias...[/blue]")
        code, stdout, stderr = run_command([
            "aws", "lambda", "update-alias",
            "--function-name", config["lambda_function_name"],
            "--name", "prod",
            "--function-version", version,
            "--region", config["aws_region"]
        ])
    else:
        console.print("[blue]Creating 'prod' alias...[/blue]")
        code, stdout, stderr = run_command([
            "aws", "lambda", "create-alias",
            "--function-name", config["lambda_function_name"],
            "--name", "prod",
            "--function-version", version,
            "--region", config["aws_region"]
        ])
    
    if code != 0:
        console.print("[bold red]Failed to create/update alias[/bold red]")
        return False
    
    # Configure provisioned concurrency
    console.print(f"[blue]Configuring provisioned concurrency ({config['provisioned_concurrency_count']} instances)...[/blue]")
    code, stdout, stderr = run_command([
        "aws", "lambda", "put-provisioned-concurrency-config",
        "--function-name", config["lambda_function_name"],
        "--qualifier", "prod",
        "--provisioned-concurrent-executions", str(config["provisioned_concurrency_count"]),
        "--region", config["aws_region"]
    ])
    
    if code != 0:
        console.print("[bold red]Failed to configure provisioned concurrency[/bold red]")
        return False
    
    # Update API Gateway to use alias
    api_id = run_command([
        "aws", "apigateway", "get-rest-apis",
        "--region", config["aws_region"],
        "--query", f"items[?name=='{config['api_gateway_name']}'].id",
        "--output", "text"
    ], capture_output=True)[1].strip()
    
    if not api_id:
        console.print("[bold red]Failed to find API Gateway ID[/bold red]")
        return False
    
    resource_id = run_command([
        "aws", "apigateway", "get-resources",
        "--rest-api-id", api_id,
        "--region", config["aws_region"],
        "--query", "items[?path=='/crawl'].id",
        "--output", "text"
    ], capture_output=True)[1].strip()
    
    if not resource_id:
        console.print("[bold red]Failed to find API Gateway resource ID[/bold red]")
        return False
    
    account_id = run_command([
        "aws", "sts", "get-caller-identity",
        "--query", "Account",
        "--output", "text"
    ], capture_output=True)[1].strip()
    
    lambda_alias_arn = f"arn:aws:lambda:{config['aws_region']}:{account_id}:function:{config['lambda_function_name']}:prod"
    
    console.print("[blue]Updating API Gateway to use Lambda alias...[/blue]")
    code, stdout, stderr = run_command([
        "aws", "apigateway", "put-integration",
        "--rest-api-id", api_id,
        "--resource-id", resource_id,
        "--http-method", "POST",
        "--type", "AWS_PROXY",
        "--integration-http-method", "POST",
        "--uri", f"arn:aws:apigateway:{config['aws_region']}:lambda:path/2015-03-31/functions/{lambda_alias_arn}/invocations",
        "--region", config["aws_region"]
    ])
    
    if code != 0:
        console.print("[bold red]Failed to update API Gateway integration[/bold red]")
        return False
    
    # Redeploy API Gateway
    console.print("[blue]Redeploying API Gateway...[/blue]")
    code, stdout, stderr = run_command([
        "aws", "apigateway", "create-deployment",
        "--rest-api-id", api_id,
        "--stage-name", "prod",
        "--region", config["aws_region"]
    ])
    
    if code != 0:
        console.print("[bold red]Failed to redeploy API Gateway[/bold red]")
        return False
    
    console.print("[bold green]Provisioned concurrency setup complete![/bold green]")
    return True

def show_deployment_summary(config: Dict[str, Any], api_id: str) -> None:
    """Show a summary of the deployment."""
    endpoint_url = f"https://{api_id}.execute-api.{config['aws_region']}.amazonaws.com/prod/crawl"
    
    # Create a summary table
    table = Table(title="Deployment Summary")
    table.add_column("Component", style="cyan")
    table.add_column("Details", style="green")
    
    table.add_row("API Endpoint", endpoint_url)
    table.add_row("Lambda Function", config["lambda_function_name"])
    table.add_row("Memory Size", f"{config['memory_size']} MB")
    table.add_row("Timeout", f"{config['timeout']} seconds")
    table.add_row("Ephemeral Storage", f"{config['ephemeral_storage_size']} MB")
    table.add_row("Provisioned Concurrency", 
                 "Enabled" if config["enable_provisioned_concurrency"] 
                 else "Disabled")
    
    if config["enable_provisioned_concurrency"]:
        table.add_row("Concurrency Units", str(config["provisioned_concurrency_count"]))
    
    console.print("\n")
    console.print(Panel(
        "🚀 [bold green]Crawl4ai has been successfully deployed to AWS Lambda![/bold green]",
        expand=False
    ))
    console.print(table)
    
    # Example usage
    console.print("\n[bold]Example Usage:[/bold]")
    url = "https://example.com"
    example_cmd = f"curl -X POST {endpoint_url} -H 'Content-Type: application/json' -d '{{\"url\": \"{url}\"}}'"
    console.print(Syntax(example_cmd, "bash", theme="monokai", line_numbers=False))
    
    console.print("\n[bold]Python Example:[/bold]")
    python_example = f'''import requests
import json

url = "{endpoint_url}"
payload = {{
    "url": "https://example.com",
    "browser_config": {{
        "headless": True,
        "verbose": False
    }},
    "crawler_config": {{
        "crawler_config": {{
            "type": "CrawlerRunConfig",
            "params": {{
                "markdown_generator": {{
                    "type": "DefaultMarkdownGenerator",
                    "params": {{
                        "content_filter": {{
                            "type": "PruningContentFilter",
                            "params": {{
                                "threshold": 0.48,
                                "threshold_type": "fixed"
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
}}

response = requests.post(url, json=payload)
result = response.json()
print(json.dumps(result, indent=2))
'''
    console.print(Syntax(python_example, "python", theme="monokai", line_numbers=False))
    
    console.print("\n[bold green]Thank you for using Crawl4ai on AWS Lambda![/bold green]")


def cleanup_resources(config: Dict[str, Any]) -> None:
    """Clean up all AWS resources created for Crawl4ai deployment."""
    show_step_header("Cleanup", "Removing AWS Resources")
    console.print("This will remove all AWS resources created for Crawl4ai deployment, including:")
    console.print("  • Lambda Function")
    console.print("  • API Gateway")
    console.print("  • ECR Repository and Images")
    console.print("  • IAM Permissions")
    
    if not Confirm.ask(
        "[bold red]⚠️ Are you sure you want to delete all resources?[/bold red]",
        default=False
    ):
        console.print("[yellow]Cleanup cancelled.[/yellow]")
        return
    
    # Get API Gateway ID
    api_id = None
    with console.status("[blue]Finding API Gateway...[/blue]"):
        code, api_id, stderr = run_command([
            "aws", "apigateway", "get-rest-apis",
            "--region", config["aws_region"],
            "--query", f"items[?name=='{config['api_gateway_name']}'].id",
            "--output", "text"
        ], capture_output=True)
        api_id = api_id.strip()
    
    # Delete API Gateway
    if api_id:
        console.print(f"[blue]Deleting API Gateway: {api_id}[/blue]")
        code, stdout, stderr = run_command([
            "aws", "apigateway", "delete-rest-api",
            "--rest-api-id", api_id,
            "--region", config["aws_region"]
        ])
        
        if code == 0:
            console.print("[green]✓[/green] API Gateway deleted successfully")
        else:
            console.print(f"[red]✗[/red] Failed to delete API Gateway: {stderr}")
    else:
        console.print("[yellow]No API Gateway found to delete[/yellow]")
    
    # Check if Lambda function exists
    lambda_exists = False
    with console.status("[blue]Checking Lambda function...[/blue]"):
        code, stdout, stderr = run_command([
            "aws", "lambda", "get-function",
            "--function-name", config["lambda_function_name"],
            "--region", config["aws_region"]
        ], capture_output=True)
        lambda_exists = code == 0
    
    # Delete provisioned concurrency if it exists
    if lambda_exists and config.get("enable_provisioned_concurrency", False):
        try:
            console.print("[blue]Removing provisioned concurrency...[/blue]")
            run_command([
                "aws", "lambda", "delete-provisioned-concurrency-config",
                "--function-name", config["lambda_function_name"],
                "--qualifier", "prod",
                "--region", config["aws_region"]
            ], capture_output=True)
            
            console.print("[blue]Deleting function alias...[/blue]")
            run_command([
                "aws", "lambda", "delete-alias",
                "--function-name", config["lambda_function_name"],
                "--name", "prod",
                "--region", config["aws_region"]
            ], capture_output=True)
        except Exception as e:
            console.print(f"[yellow]Warning: {str(e)}[/yellow]")
    
    # Delete Lambda function
    if lambda_exists:
        console.print(f"[blue]Deleting Lambda function: {config['lambda_function_name']}[/blue]")
        code, stdout, stderr = run_command([
            "aws", "lambda", "delete-function",
            "--function-name", config["lambda_function_name"],
            "--region", config["aws_region"]
        ])
        
        if code == 0:
            console.print("[green]✓[/green] Lambda function deleted successfully")
        else:
            console.print(f"[red]✗[/red] Failed to delete Lambda function: {stderr}")
    else:
        console.print("[yellow]No Lambda function found to delete[/yellow]")
    
    # Check if ECR repository exists
    ecr_exists = False
    with console.status("[blue]Checking ECR repository...[/blue]"):
        code, stdout, stderr = run_command([
            "aws", "ecr", "describe-repositories",
            "--repository-names", config["ecr_repository_name"],
            "--region", config["aws_region"]
        ], capture_output=True)
        ecr_exists = code == 0
    
    # Delete ECR repository
    if ecr_exists:
        console.print(f"[blue]Deleting ECR repository: {config['ecr_repository_name']}[/blue]")
        code, stdout, stderr = run_command([
            "aws", "ecr", "delete-repository",
            "--repository-name", config["ecr_repository_name"],
            "--force",  # Force delete even if it contains images
            "--region", config["aws_region"]
        ])
        
        if code == 0:
            console.print("[green]✓[/green] ECR repository deleted successfully")
        else:
            console.print(f"[red]✗[/red] Failed to delete ECR repository: {stderr}")
    else:
        console.print("[yellow]No ECR repository found to delete[/yellow]")
    
    # Check and clean up IAM permissions
    console.print("[blue]Cleaning up IAM permissions...[/blue]")
    try:
        # Remove the Lambda permission for API Gateway
        run_command([
            "aws", "lambda", "remove-permission",
            "--function-name", config["lambda_function_name"],
            "--statement-id", "apigateway",
            "--region", config["aws_region"]
        ], capture_output=True)
    except Exception:
        # It's okay if this fails, the function might already be deleted
        pass
    
    # Clean up local Docker images
    console.print("[blue]Cleaning up local Docker images...[/blue]")
    try:
        # Get account ID
        code, account_id, stderr = run_command([
            "aws", "sts", "get-caller-identity",
            "--query", "Account",
            "--output", "text"
        ], capture_output=True)
        
        if code == 0:
            account_id = account_id.strip()
            repo_uri = f"{account_id}.dkr.ecr.{config['aws_region']}.amazonaws.com/{config['ecr_repository_name']}"
            
            run_command([
                "docker", "rmi", 
                f"{repo_uri}:latest",
                "--force"
            ], capture_output=True)
            
            run_command([
                "docker", "rmi", 
                f"{config['ecr_repository_name']}:latest",
                "--force"
            ], capture_output=True)
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to clean up Docker images: {str(e)}[/yellow]")
    
    console.print("\n[bold green]Cleanup Complete![/bold green]")
    console.print("All AWS resources for the Crawl4ai deployment have been removed.")

# Add this to the app commands
@app.command()
def cleanup():
    """
    Remove all AWS resources created for Crawl4ai deployment.
    
    This will delete the Lambda function, API Gateway, and ECR repository.
    """
    console.print(Panel(
        "[bold red]Crawl4ai AWS Resources Cleanup[/bold red]\n\n"
        "This will remove all AWS resources created for Crawl4ai deployment.",
        title="Warning",
        expand=False
    ))
    
    # Check AWS credentials
    if not check_aws_credentials():
        return
    
    # Get configuration
    config = DEFAULT_CONFIG.copy()
    
    console.print("\n[bold]Configuration[/bold]")
    console.print("Please confirm the resources to clean up:")
    
    config["aws_region"] = Prompt.ask(
        "AWS Region",
        default=config["aws_region"]
    )
    
    config["lambda_function_name"] = Prompt.ask(
        "Lambda Function Name",
        default=config["lambda_function_name"]
    )
    
    config["api_gateway_name"] = Prompt.ask(
        "API Gateway Name",
        default=config["api_gateway_name"]
    )
    
    config["ecr_repository_name"] = Prompt.ask(
        "ECR Repository Name",
        default=config["ecr_repository_name"]
    )
    
    # Run cleanup
    cleanup_resources(config)

@app.command()
def main() -> None:
    """
    Deploy Crawl4ai to AWS Lambda.
    
    This script guides you through the process of deploying Crawl4ai
    as an AWS Lambda function with API Gateway integration.
    """
    # Show welcome banner
    console.print(Panel(
        "[bold blue]Crawl4ai AWS Lambda Deployment Wizard[/bold blue]\n\n"
        "This tool will help you deploy Crawl4ai to AWS Lambda with API Gateway integration.",
        title="Welcome",
        expand=False
    ))
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Check AWS credentials
    if not check_aws_credentials():
        return
    
    # Get configuration
    config = DEFAULT_CONFIG.copy()
    
    console.print("\n[bold]Configuration[/bold]")
    console.print("Please configure your deployment:")
    
    config["aws_region"] = Prompt.ask(
        "AWS Region",
        default=config["aws_region"]
    )
    
    config["lambda_function_name"] = Prompt.ask(
        "Lambda Function Name",
        default=config["lambda_function_name"]
    )
    
    config["api_gateway_name"] = Prompt.ask(
        "API Gateway Name",
        default=config["api_gateway_name"]
    )
    
    config["memory_size"] = int(Prompt.ask(
        "Lambda Memory Size (MB)",
        default=str(config["memory_size"])
    ))
    
    config["timeout"] = int(Prompt.ask(
        "Lambda Timeout (seconds)",
        default=str(config["timeout"])
    ))
    
    config["enable_provisioned_concurrency"] = Confirm.ask(
        "Enable Provisioned Concurrency (reduces cold starts)?",
        default=config["enable_provisioned_concurrency"]
    )
    
    if config["enable_provisioned_concurrency"]:
        config["provisioned_concurrency_count"] = int(Prompt.ask(
            "Number of Provisioned Concurrency instances",
            default=str(config["provisioned_concurrency_count"])
        ))
    
    # Verify IAM role
    role_arn = verify_iam_role(config)
    if not role_arn:
        console.print("[bold red]Failed to verify or create IAM role[/bold red]")
        return
    
    # Build Docker image
    if not build_docker_image(config):
        return
    
    # Setup ECR repository
    repository_uri = setup_ecr_repository(config)
    if not repository_uri:
        return
    
    # Push image to ECR
    if not push_image_to_ecr(config, repository_uri):
        return
    
    # Deploy Lambda function
    if not deploy_lambda_function(config, repository_uri, role_arn):
        return
    
    # Setup API Gateway
    api_id = setup_api_gateway(config)
    if not api_id:
        return
    
    # Configure provisioned concurrency if enabled
    if not configure_provisioned_concurrency(config):
        return
    
    # Show deployment summary
    show_deployment_summary(config, api_id)

if __name__ == "__main__":
    app()