from colorama import Fore, Style
import subprocess
import sys
import distutils.log as log
from pathlib import Path

def main():
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
    except:
        print(f"\n{Fore.YELLOW}{'='*40}")
        print(f"{Fore.RED}IMPORTANT: Run this command now:")
        print(f"{Fore.GREEN}python -m playwright install")
        print(f"{Fore.YELLOW}{'='*40}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main()