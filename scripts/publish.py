import os
import subprocess

from dotenv import load_dotenv

load_dotenv("../.env")

API_KEY: str = os.environ["PYPI_TOKEN"]

input("Press any key to upload...")


subprocess.Popen(
    f'python -m twine upload --username __token__ --password "{API_KEY}" --repository pypi ../dist/*',
    shell=True
).wait()
