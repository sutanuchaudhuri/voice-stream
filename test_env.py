import os
from dotenv import load_dotenv, find_dotenv

print("CWD:", os.getcwd())
print(".env exists:", os.path.exists('.env'))

load_dotenv(find_dotenv())
print("All loaded envs:", dict(os.environ))


key = os.getenv('OPENAI_API_KEY')
print(f'OPENAI_API_KEY: {key}')