import time

import paramiko
import os
from pathlib import Path


host = '192.168.1.196'
user = 'root'
secret = 'Sergey128'
port = 22
local_files = []
local_dirs = []


def get_files(path):
    for root, dirs, files in os.walk(path, topdown=True):
        for name in files:
            # if name.count("git") != 0: continue
            tmp = str(next(Path(path).rglob(name)))
            if tmp.count('.git') != 0: continue
            tmp = tmp.replace("\\", "/")
            local_files.append(tmp)
            # print("file - ", tmp)

    for root, dirs, files in os.walk(path, topdown=True):
        for name in dirs:
            # if ".git" in name: continue
            tmp = str(next(Path(path).rglob(name)))
            if tmp.count('git') != 0: continue
            tmp = tmp.replace("\\", "/")
            local_dirs.append(tmp)
            # print("dir - ", tmp)




if __name__ == '__main__':

    local_path  = "D:/Sergey_work/_pyrepos/lab_srv/testbench_server/"
    remote_path = "/_srv/"

   #  local_path  = "D:/moxalinux/dst/"
   #  remote_path = "/_drv/"

    get_files(local_path)


    ind = len(local_path)
    remote_files = list(map(lambda x: remote_path + x[ind:], local_files))
    remote_dirs = list(map(lambda x:  remote_path + x[ind:], local_dirs))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(host, username=user, password=secret)
    print("connected to ", host, " as ", user)

    print("clear target path")
    cmd = "rm -rf " + remote_path
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print("make dir ", remote_path)
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
        if el.count('.git') != 0: continue
        if el.count('.idea') != 0: continue

        print("Make dir: ", el[0:])
        sftp.mkdir(el[0:])
    for i in range(len(local_files)):
        if local_files[i].count('.git') != 0: continue
        print(local_files[i])
        sftp.put(local_files[i], remote_files[i])
        time.sleep(0.1);
    sftp.close()
    transport.close()


