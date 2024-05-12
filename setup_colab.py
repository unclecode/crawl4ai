import os

def install_crawl4ai():
    print("Installing Crawl4AI and its dependencies...")
    
    # Install dependencies
    !pip install -U 'spacy[cuda12x]'
    !apt-get update -y
    !apt install chromium-chromedriver -y
    !pip install chromedriver_autoinstaller
    !pip install git+https://github.com/unclecode/crawl4ai.git@new-release-0.0.2
    
    # Install ChromeDriver
    import chromedriver_autoinstaller
    chromedriver_autoinstaller.install()
    
    # Download the reuters model
    repo_url = "https://github.com/unclecode/crawl4ai.git"
    branch = "new-release-0.0.2"
    folder_path = "models/reuters"
    
    !git clone -b {branch} {repo_url}
    !mkdir -p models
    
    repo_folder = "crawl4ai"
    source_folder = os.path.join(repo_folder, folder_path)
    destination_folder = "models"
    
    !mv "{source_folder}" "{destination_folder}"
    !rm -rf "{repo_folder}"
    
    print("Installation and model download completed successfully!")

# Run the installer
install_crawl4ai()