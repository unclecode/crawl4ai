#!/usr/bin/env python3
import argparse
import subprocess
import sys
import yaml
import requests

def run_command(cmd, explanation, require_confirm=True, allow_already_exists=False):
    print("\n=== {} ===".format(explanation))
    if require_confirm:
        input("Press Enter to run: [{}]\n".format(cmd))
    print("Running: {}".format(cmd))
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        if allow_already_exists and "ALREADY_EXISTS" in result.stderr:
            print("Repository already exists, skipping creation.")
            return ""
        print("Error:\n{}".format(result.stderr))
        sys.exit(1)
    out = result.stdout.strip()
    if out:
        print("Output:\n{}".format(out))
    return out

def load_config():
    try:
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print("Failed to load config.yml: {}".format(e))
        sys.exit(1)
    required = ["project_id", "region", "artifact_repo", "function_name", "local_image"]
    for key in required:
        if key not in config or not config[key]:
            print("Missing required config parameter: {}".format(key))
            sys.exit(1)
    return config

def deploy_function(config):
    project_id     = config["project_id"]
    region         = config["region"]
    artifact_repo  = config["artifact_repo"]
    function_name  = config["function_name"]
    memory         = config.get("memory", "2048MB")
    timeout        = config.get("timeout", "540s")
    local_image    = config["local_image"]
    test_query_url = config.get("test_query_url", "https://example.com")

    # Repository image format: "<region>-docker.pkg.dev/<project_id>/<artifact_repo>/<function_name>:latest"
    repo_image = f"{region}-docker.pkg.dev/{project_id}/{artifact_repo}/{function_name}:latest"

    # 1. Create Artifact Registry repository (skip if exists)
    cmd = f"gcloud artifacts repositories create {artifact_repo} --repository-format=docker --location={region} --project={project_id}"
    run_command(cmd, "Creating Artifact Registry repository (if it doesn't exist)", allow_already_exists=True)

    # 2. Tag the local Docker image with the repository image name
    cmd = f"docker tag {local_image} {repo_image}"
    run_command(cmd, "Tagging Docker image for Artifact Registry")

    # 3. Authenticate Docker to Artifact Registry
    cmd = f"gcloud auth configure-docker {region}-docker.pkg.dev"
    run_command(cmd, "Authenticating Docker to Artifact Registry")

    # 4. Push the tagged Docker image to Artifact Registry
    cmd = f"docker push {repo_image}"
    run_command(cmd, "Pushing Docker image to Artifact Registry")

    # 5. Deploy the Cloud Function using the custom container
    cmd = (
        f"gcloud beta functions deploy {function_name} "
        f"--gen2 "
        f"--runtime=python310 "
        f"--entry-point=crawl "
        f"--region={region} "
        f"--docker-repository={region}-docker.pkg.dev/{project_id}/{artifact_repo} "
        f"--trigger-http "
        f"--memory={memory} "
        f"--timeout={timeout} "
        f"--project={project_id}"
    )
    run_command(cmd, "Deploying Cloud Function using custom container")

    # 6. Set the Cloud Function to allow public (unauthenticated) invocations
    cmd = (
        f"gcloud functions add-iam-policy-binding {function_name} "
        f"--region={region} "
        f"--member='allUsers' "
        f"--role='roles/cloudfunctions.invoker' "
        f"--project={project_id}"
        f"--quiet"
    )
    run_command(cmd, "Setting Cloud Function IAM to allow public invocations")

    # 7. Retrieve the deployed Cloud Function URL
    cmd = (
        f"gcloud functions describe {function_name} "
        f"--region={region} "
        f"--project={project_id} "
        f"--format='value(serviceConfig.uri)'"
    )
    deployed_url = run_command(cmd, "Extracting deployed Cloud Function URL", require_confirm=False)
    print("\nDeployed URL: {}\n".format(deployed_url))

    # 8. Test the deployed function
    test_url = f"{deployed_url}?url={test_query_url}"
    print("Testing function with: {}".format(test_url))
    try:
        response = requests.get(test_url)
        print("Response status: {}".format(response.status_code))
        print("Response body:\n{}".format(response.text))
        if response.status_code == 200:
            print("Test successful!")
        else:
            print("Non-200 response; check function logs.")
    except Exception as e:
        print("Test request error: {}".format(e))
        sys.exit(1)

    # 9. Final usage help
    print("\nDeployment complete!")
    print("Invoke your function with:")
    print(f"curl '{deployed_url}?url={test_query_url}'")
    print("For further instructions, refer to your documentation.")

def delete_function(config):
    project_id    = config["project_id"]
    region        = config["region"]
    function_name = config["function_name"]
    cmd = f"gcloud functions delete {function_name} --region={region} --project={project_id} --quiet"
    run_command(cmd, "Deleting Cloud Function")

def describe_function(config):
    project_id    = config["project_id"]
    region        = config["region"]
    function_name = config["function_name"]
    cmd = (
        f"gcloud functions describe {function_name} "
        f"--region={region} "
        f"--project={project_id} "
        f"--format='value(serviceConfig.uri)'"
    )
    deployed_url = run_command(cmd, "Describing Cloud Function to extract URL", require_confirm=False)
    print("\nCloud Function URL: {}\n".format(deployed_url))

def clear_all(config):
    print("\n=== CLEAR ALL RESOURCES ===")
    project_id    = config["project_id"]
    region        = config["region"]
    artifact_repo = config["artifact_repo"]

    confirm = input("WARNING: This will DELETE the Cloud Function and the Artifact Registry repository. Are you sure? (y/N): ")
    if confirm.lower() != "y":
        print("Aborting clear operation.")
        sys.exit(0)

    # Delete the Cloud Function
    delete_function(config)
    # Delete the Artifact Registry repository
    cmd = f"gcloud artifacts repositories delete {artifact_repo} --location={region} --project={project_id} --quiet"
    run_command(cmd, "Deleting Artifact Registry repository", require_confirm=False)
    print("All resources cleared.")

def main():
    parser = argparse.ArgumentParser(description="Deploy, delete, describe, or clear Cloud Function resources using config.yml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("deploy", help="Deploy the Cloud Function")
    subparsers.add_parser("delete", help="Delete the deployed Cloud Function")
    subparsers.add_parser("describe", help="Describe the Cloud Function and return its URL")
    subparsers.add_parser("clear", help="Delete the Cloud Function and Artifact Registry repository")

    args = parser.parse_args()
    config = load_config()

    if args.command == "deploy":
        deploy_function(config)
    elif args.command == "delete":
        delete_function(config)
    elif args.command == "describe":
        describe_function(config)
    elif args.command == "clear":
        clear_all(config)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
