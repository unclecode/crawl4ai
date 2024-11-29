from colorama import Fore, Style
import subprocess
import sys

def post_install():
    print(f"\n{Fore.YELLOW}{'='*40}")
    print(f"{Fore.RED}IMPORTANT: Run this command now:")
    print(f"{Fore.GREEN}python -m playwright install")
    print(f"{Fore.YELLOW}{'='*40}{Style.RESET_ALL}\n")