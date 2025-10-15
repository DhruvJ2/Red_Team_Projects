import argparse
from ftplib import FTP
import pyfiglet
import termcolor

asciiBanner = pyfiglet.figlet_format("FTP User Footprint")
print(termcolor.colored(asciiBanner, 'blue'))

def parse_args():
    parser = argparse.ArgumentParser(description="Simple FTP User Footprinting")
    parser.add_argument('-i', '--ip', help='FTP server address', required=True)
    parser.add_argument('--user', help='Usernames wordlist file', required=True)
    return parser.parse_args()

def check_ftp_user(target, username, port=21, timeout=5):
    try:
        ftp = FTP()
        ftp.connect(target, port=port, timeout=timeout)
        response = ftp.sendcmd(f"User {username}")
        if "331" in response or "230" in response:
            print(f"Possible valid user: {username}")
        ftp.quit()
    except Exception as e:
        if "530" in str(e):
            print(f"Invalid user: {username}")
        else:
            print(f"Error with {username}: {e}")

if __name__ == "__main__":
    args = parse_args()
    host = args.ip
    port = 21

    try:
        with open(args.user, 'r') as f:
            usernames = f.read().splitlines()
    except Exception as e:
        print(f"[ERROR] Reading wordlist files failed: {e}")

    for user in usernames:
        check_ftp_user(host, user, port)

