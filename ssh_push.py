import time

import paramiko
import os
from pathlib import Path


host = '192.168.1.74'
user = 'root'
secret = 'Sergey128'
port = 22
local_files = []
local_dirs = []


def get_files(path):
    for root, dirs, files in os.walk(path, topdown=True):
        for name in files:
            local_files.append(str(next(Path(path).rglob(name))))
        for name in dirs:
            local_dirs.append(str(next(Path(path).rglob(name))))




if __name__ == '__main__':

    local_path  = "/home/sergey/PycharmProjects/MySite/_srv/"
    remote_path = "/home/elvis/tornado-chart/_srv/"
    get_files(local_path)

    ind = len(local_path)
    remote_files = list(map(lambda x: remote_path+x[ind:], local_files))
    remote_dirs = list(map(lambda x: remote_path + x[ind:], local_dirs))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(host, username=user, password=secret)

    print("clear target path")
    cmd = "rm -rf " + remote_path

    stdin, stdout, stderr = ssh.exec_command(cmd)

    cmd = "mkdir " + remote_path

    stdin, stdout, stderr = ssh.exec_command(cmd)

    while not stdout.channel.exit_status_ready():
        time.sleep(1)
    ssh.close()

    print("copy files to target")
    transport = paramiko.Transport((host, port))
    transport.connect(username=user, password=secret)
    sftp = paramiko.SFTPClient.from_transport(transport)
    for el in remote_dirs:
        if ".git" in el: continue
        print("Make dir: ", el)
        sftp.mkdir(el)
    for i in range(len(local_files)):
        if ".git" in local_files[i]: continue
        print(local_files[i])
        sftp.put(local_files[i], remote_files[i])
    sftp.close()
    transport.close()


