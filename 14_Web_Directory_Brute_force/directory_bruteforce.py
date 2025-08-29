import requests
import argparse, pyfiglet

asciiBanner = pyfiglet.figlet_format("Directory Brute Force")
print(asciiBanner)

parser = argparse.ArgumentParser(description="Simple directory brute force tool")
parser.add_argument('-u', '--url', help='Enter url to brute force', default='http://testhtml5.vulnweb.com')
parser.add_argument('-w', '--wordlist', help='Enter wordlist', default='./common.txt')
args = parser.parse_args()

directoryPath = args.wordlist

with open(directoryPath, 'r') as f:
    wordlist = f.read().splitlines()

for directory in wordlist:
    directoryUrl = args.url + '/' + directory
    response = requests.get(directoryUrl)
    if response.status_code == 200:
        print(f'[+] Found Directory: {directoryUrl}')


## make it multi threaded