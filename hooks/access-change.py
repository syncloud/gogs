import subprocess

print(subprocess.check_output('snap run gogs.access-change', shell=True))

