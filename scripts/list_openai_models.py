import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from openai import OpenAI
except Exception as e:
    print("OpenAI SDK not installed. Please install dependencies first.")
    sys.exit(1)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("OPENAI_API_KEY not set in environment.")
    sys.exit(2)

client = OpenAI(api_key=api_key)

try:
    models = client.models.list()
except Exception as e:
    print(f"Failed to list models: {e}")
    sys.exit(3)

ids = sorted(m.id for m in models.data)

# Heuristic filters for chat-capable conversational models
chat_like_prefixes = (
    "gpt-4o", "gpt-4.1", "gpt-4", "gpt-3.5",
    "o1", "o3"
)
chat_like = [mid for mid in ids if mid.startswith(chat_like_prefixes)]

print("Total models available:", len(ids))
print("\nLikely chat-capable models you can use:")
if chat_like:
    for mid in chat_like:
        print("-", mid)
else:
    print("(No chat-like models detected for this key; check your account access.)")
