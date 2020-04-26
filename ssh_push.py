import time
import os
from pathlib import Path
from shutil import make_archive
import paramiko

host = '192.168.1.74'
user = 'root'
secret = 'Sergey128'
remote_path = "/_srv/"

if __name__ == '__main__':

    port = 22
    local_file = Path("arch.zip").resolve()
    remote_file = remote_path + "arch.zip"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("connected to ", host, " as ", user)
    ssh.connect(host, username=user, password=secret)

    print("create local zip")
    make_archive(
        'arch',
        'zip',  # the archive format - or tar, bztar, gztar
        root_dir=None,  # root for archive - current working dir if None
        base_dir=None)  # start archiving from here - cwd if None too

    print("clear remote path")
    cmd = "rm -rf " + remote_path
    stdin, stdout, stderr = ssh.exec_command(cmd)
    while not stdout.channel.exit_status_ready():
        time.sleep(1)

    cmd = "mkdir " + remote_path
    stdin, stdout, stderr = ssh.exec_command(cmd)
    while not stdout.channel.exit_status_ready():
        time.sleep(1)

    print("copy zip to target")
    transport = paramiko.Transport((host, port))
    transport.connect(username=user, password=secret)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.put(local_file, remote_file)

    print("uzip on target")
    cmd = "unzip "+remote_file + " -d " + remote_path + " -x arch.zip"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    while not stdout.channel.exit_status_ready():
        time.sleep(1)

    try:
        os.remove(local_file)
        print("delete local zip")
    except FileNotFoundError: pass

    print("delete remote zip")
    cmd = "rm " + remote_file
    stdin, stdout, stderr = ssh.exec_command(cmd)
    while not stdout.channel.exit_status_ready():
        time.sleep(1)

    ssh.close()
    sftp.close()
    transport.close()

