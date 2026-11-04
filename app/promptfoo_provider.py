import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from app.bot import ask

def call_api(prompt, options, context):
    try:
        return {"output": ask(prompt)}
    except Exception as e:
        return {"error": str(e)}