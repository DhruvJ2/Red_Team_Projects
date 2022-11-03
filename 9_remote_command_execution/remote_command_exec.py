import paramiko

outputfile="output.log"
def command_exec(hostname,command):
    print('operatins start')
    try:
        portno=22
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname,portno,username="user",password="pass")
        stdin,stdout,stderr = ssh.exec_command(command)
        result = stdout.readlines()
        print(f'log printing:::::: {command} :: {result}')

        with open(outputfile,"w+") as fs:
            fs.write(str(result))
        return outputfile
    finally:
        ssh.close()

command = ''
while(command!='exit'):
    command = input('> ')
    command_exec('ip',command)
