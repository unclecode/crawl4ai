# Deploying Crawl4ai on Google Cloud Functions

This guide explains how to deploy **Crawl4ai**—an open‑source web crawler library—on Google Cloud Functions Gen2 using a custom container. We assume your project folder already includes:

- **Dockerfile:** Builds your container image (which installs Crawl4ai from its Git repository).
- **start.sh:** Activates your virtual environment and starts the function (using the Functions Framework).
- **main.py:** Contains your function logic with the entry point `crawl` (and imports Crawl4ai).

The guide is divided into two parts:
1. Manual deployment steps (using CLI commands)
2. Automated deployment using a Python script (`deploy.py`)

---

## Part 1: Manual Deployment Process

### Prerequisites

- **Google Cloud Project:** Ensure your project is active and billing is enabled.
- **Google Cloud CLI & Docker:** Installed and configured on your local machine.
- **Permissions:** You must have rights to create Cloud Functions and Artifact Registry repositories.
- **Files:** Your Dockerfile, start.sh, and main.py should be in the same directory.

### Step 1: Build Your Docker Image

Your Dockerfile packages Crawl4ai along with all its dependencies. Build your image with:

```bash
docker build -t gcr.io/<PROJECT_ID>/<FUNCTION_NAME>:latest .
```

Replace `<PROJECT_ID>` with your Google Cloud project ID and `<FUNCTION_NAME>` with your chosen function name (for example, `crawl4ai-t1`).

### Step 2: Create an Artifact Registry Repository

Cloud Functions Gen2 requires your custom container image to reside in an Artifact Registry repository. Create one by running:

```bash
gcloud artifacts repositories create <ARTIFACT_REPO> \
  --repository-format=docker \
  --location=<REGION> \
  --project=<PROJECT_ID>
```

Replace `<ARTIFACT_REPO>` (for example, `crawl4ai`) and `<REGION>` (for example, `asia-east1`).  
> **Note:** If you receive an `ALREADY_EXISTS` error, the repository is already created; simply proceed to the next step.

### Step 3: Tag Your Docker Image

Tag your locally built Docker image so it matches the Artifact Registry format:

```bash
docker tag gcr.io/<PROJECT_ID>/<FUNCTION_NAME>:latest <REGION>-docker.pkg.dev/<PROJECT_ID>/<ARTIFACT_REPO>/<FUNCTION_NAME>:latest
```

This step “renames” the image so you can push it to your repository.

### Step 4: Authenticate Docker to Artifact Registry

Configure Docker authentication to the Artifact Registry:

```bash
gcloud auth configure-docker <REGION>-docker.pkg.dev
```

This ensures Docker can securely push images to your registry using your Cloud credentials.

### Step 5: Push the Docker Image

Push the tagged image to Artifact Registry:

```bash
docker push <REGION>-docker.pkg.dev/<PROJECT_ID>/<ARTIFACT_REPO>/<FUNCTION_NAME>:latest
```

Once complete, your container image (with Crawl4ai installed) is hosted in Artifact Registry.

### Step 6: Deploy the Cloud Function

Deploy your function using the custom container image. Run:

```bash
gcloud beta functions deploy <FUNCTION_NAME> \
  --gen2 \
  --region=<REGION> \
  --docker-repository=<REGION>-docker.pkg.dev/<PROJECT_ID>/<ARTIFACT_REPO> \
  --trigger-http \
  --memory=2048MB \
  --timeout=540s \
  --project=<PROJECT_ID>
```

This command tells Cloud Functions Gen2 to pull your container image from Artifact Registry and deploy it. Make sure your main.py defines the `crawl` entry point.

### Step 7: Make the Function Public

To allow external (unauthenticated) access, update the function’s IAM policy:

```bash
gcloud functions add-iam-policy-binding <FUNCTION_NAME> \
  --region=<REGION> \
  --member="allUsers" \
  --role="roles/cloudfunctions.invoker" \
  --project=<PROJECT_ID> \
  --quiet
```

Using the `--quiet` flag ensures the command runs non‑interactively so the policy is applied immediately.

### Step 8: Retrieve and Test Your Function URL

Get the URL for your deployed function:

```bash
gcloud functions describe <FUNCTION_NAME> \
  --region=<REGION> \
  --project=<PROJECT_ID> \
  --format='value(serviceConfig.uri)'
```

Test your deployment with a sample GET request (using curl or your browser):

```bash
curl "<FUNCTION_URL>?url=https://example.com"
```

Replace `<FUNCTION_URL>` with the output URL from the previous command. A successful test (HTTP status 200) means Crawl4ai is running on Cloud Functions.

---

## Part 2: Automated Deployment with deploy.py

For a more streamlined process, use the provided `deploy.py` script. This Python script automates the manual steps, prompting you to confirm key actions and providing detailed logs throughout the process.

### What deploy.py Does:

- **Reads Parameters:** It loads a `config.yml` file containing all necessary parameters such as `project_id`, `region`, `artifact_repo`, `function_name`, `local_image`, etc.
- **Creates/Skips Repository:** It creates the Artifact Registry repository (or skips if it already exists).
- **Tags & Pushes:** It tags your local Docker image and pushes it to the Artifact Registry.
- **Deploys the Function:** It deploys the Cloud Function with your custom container.
- **Updates IAM:** It sets the IAM policy to allow public access (using the `--quiet` flag).
- **Tests the Deployment:** It extracts the deployed URL and performs a test request.
- **Additional Commands:** You can also use subcommands in the script to delete or describe the deployed function, or even clear all resources.

### Example config.yml

Create a `config.yml` file in the same folder as your Dockerfile. An example configuration:

```yaml
project_id: your-project-id
region: asia-east1
artifact_repo: crawl4ai
function_name: crawl4ai-t1
memory: "2048MB"
timeout: "540s"
local_image: "gcr.io/your-project-id/crawl4ai-t1:latest"
test_query_url: "https://example.com"
```

### How to Use deploy.py

- **Deploy the Function:**

  ```bash
  python deploy.py deploy
  ```

  The script will guide you through each step, display the output, and ask for confirmation before executing critical commands.

- **Describe the Function:**

  If you forget the function URL and want to retrieve it later:

  ```bash
  python deploy.py describe
  ```

- **Delete the Function:**

  To remove just the Cloud Function:

  ```bash
  python deploy.py delete
  ```

- **Clear All Resources:**

  To delete both the Cloud Function and the Artifact Registry repository:

  ```bash
  python deploy.py clear
  ```

---

## Conclusion

This guide has walked you through two deployment methods for Crawl4ai on Google Cloud Functions Gen2:

1. **Manual Deployment:** Building your Docker image, pushing it to Artifact Registry, deploying the Cloud Function, and setting up IAM.
2. **Automated Deployment:** Using `deploy.py` with a configuration file to handle the entire process interactively.

By following these instructions, you can deploy, test, and manage your Crawl4ai-based Cloud Function with ease. Enjoy using Crawl4ai in your cloud environment!

