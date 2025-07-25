#!/usr/bin/env python3
"""Test script for verifying Test PyPI and Docker releases"""

import subprocess
import sys

def test_pypi():
    print("=== Testing Test PyPI Package ===")
    print("1. Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "test_env"], check=True)
    
    print("2. Installing from Test PyPI...")
    pip_cmd = "./test_env/bin/pip" if sys.platform != "win32" else "test_env\\Scripts\\pip"
    subprocess.run([
        pip_cmd, "install", "-i", "https://test.pypi.org/simple/", 
        "--extra-index-url", "https://pypi.org/simple/",  # For dependencies
        "crawl4ai==0.7.1"
    ], check=True)
    
    print("3. Testing import...")
    python_cmd = "./test_env/bin/python" if sys.platform != "win32" else "test_env\\Scripts\\python"
    result = subprocess.run([
        python_cmd, "-c", 
        "from crawl4ai import AsyncWebCrawler; print('✅ Import successful!'); print(f'Version: {__import__(\"crawl4ai\").__version__}')"
    ], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    
    print("4. Cleaning up...")
    import shutil
    shutil.rmtree("test_env")
    print("✅ Test PyPI package test passed!\n")
    return True

def test_docker():
    print("=== Testing Docker Image ===")
    print("1. Pulling test image...")
    subprocess.run(["docker", "pull", "unclecode/crawl4ai:test-0.7.1"], check=True)
    
    print("2. Running version check...")
    result = subprocess.run([
        "docker", "run", "--rm", "unclecode/crawl4ai:test-0.7.1",
        "python", "-c", "import crawl4ai; print(f'Version: {crawl4ai.__version__}')"
    ], capture_output=True, text=True)
    print(result.stdout)
    
    print("3. Testing crawl4ai-doctor command...")
    result = subprocess.run([
        "docker", "run", "--rm", "unclecode/crawl4ai:test-0.7.1",
        "crawl4ai-doctor"
    ], capture_output=True, text=True)
    print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
    
    print("✅ Docker image test passed!\n")
    return True

if __name__ == "__main__":
    print("🧪 Testing Crawl4AI Release Artifacts\n")
    
    pypi_ok = False
    docker_ok = False
    
    try:
        pypi_ok = test_pypi()
    except Exception as e:
        print(f"❌ Test PyPI test failed: {e}")
    
    try:
        docker_ok = test_docker()
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
    
    print("\n📊 Summary:")
    print(f"Test PyPI: {'✅ Passed' if pypi_ok else '❌ Failed'}")
    print(f"Docker Hub: {'✅ Passed' if docker_ok else '❌ Failed'}")
    
    if pypi_ok and docker_ok:
        print("\n🎉 All tests passed! Ready for production release.")
    else:
        print("\n⚠️ Some tests failed. Please fix before production release.")
        sys.exit(1)