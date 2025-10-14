import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4.1-2025-04-14"

try:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Reply with the word: pong"}
        ],
        max_tokens=5,
    )
    print("Status: OK - model usable:", MODEL)
    print("Sample:", resp.choices[0].message.content)
except Exception as e:
    print("Status: FAIL - cannot use model:", MODEL)
    print(e)
