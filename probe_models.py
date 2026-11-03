import time
from google import genai
from google.genai import types

client = genai.Client(http_options=types.HttpOptions(timeout=20000))

names = [m.name.replace("models/", "") for m in client.models.list()
         if "flash" in m.name.lower() and "image" not in m.name.lower()
         and "tts" not in m.name.lower() and "live" not in m.name.lower()]
print("candidates:", names, "\n")

for name in names:
    try:
        r = client.models.generate_content(
            model=name, contents="Reply with the single word OK",
            config=types.GenerateContentConfig(max_output_tokens=500))
        print("WORKS ", name, "->", repr(r.text))
    except Exception as e:
        print("FAILS ", name, "->", type(e).__name__, str(e)[:90])
    time.sleep(2)