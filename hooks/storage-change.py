import subprocess

print(subprocess.check_output('snap run gogs.storage-change', shell=True))
