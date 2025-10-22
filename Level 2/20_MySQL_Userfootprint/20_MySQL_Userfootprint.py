import mysql.connector
from mysql.connector import Error
import argparse
import pyfiglet
import termcolor

asciiBanner = pyfiglet.figlet_format("MySQL User Footprint")
print(termcolor.colored(asciiBanner, 'blue'))

def parse_args():
    parser = argparse.ArgumentParser(description="Simple MySQL User Footprinting")
    parser.add_argument('-h', '--host', help='FTP server address', required=True)
    parser.add_argument('-u','--user', help='Usernames wordlist file', required=True)
    parser.add_argument('-p','--password', help='Passwords wordlist file', required=True)
    return parser.parse_args()

def check_mysql_user(username, password, host):
    try:
        connection = mysql.connector.connect(
            host = host,
            database = 'information_schema',
            user = 'user',
            password = 'password'
        )
        if connection.is_connected():
            mysql_server_info = connection.get_server_info()
            print("Username exists", mysql_server_info)
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            print("Success - connected to db: ", record) 
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

if __name__ == "__main__":
    args = parse_args()
    host = args.host
    
    try:
        with open(args.user, 'r') as f:
            username = f.read().splitlines()
        with open(args.password, 'r') as f:
            password = f.read().splitlines()
    except Exception as e:
        print(f"[ERROR] Reading wordlist files failed: {e}")

    for user, pw in username and password:
        check_mysql_user(user, pw, host)