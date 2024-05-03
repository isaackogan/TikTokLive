import os
import subprocess

from dotenv import load_dotenv

load_dotenv('./.env')

input("Press any key to upload...")

commands = [
    "cd package",
    f"npm config set _authToken={os.environ['NPM_TOKEN']}",
    f'npm publish --access public --registry https://registry.npmjs.org/',
]

subprocess.Popen(
    " && ".join(commands),
    shell=True
).wait()
