"""
Agent CLI Tester
Send a message directly to the chatbot agent from the terminal, bypassing Streamlit UI.
- Lets you pick bot type (emotional/cognitive/motivational/control)
- Prints the exact system prompt being used
- Sends your user message and prints the model's reply

Defaults:
- Does NOT save to the database by default. Use --save to persist.

Usage (PowerShell):
    # Basic (no DB writes)
    python scripts/agent_cli.py --message "hello there"

    # Choose a specific bot
    python scripts/agent_cli.py --message "how do you feel today?" --bot emotional

    # Print the exact messages sent to the model
    python scripts\agent_cli.py --message "debug payload" --debug-print-messages

    # Show full system prompt
    python scripts\agent_cli.py --message "check the prompt" --show-full-prompt

    # Persist to DB explicitly
    python scripts/agent_cli.py --message "record this" --save

    # Use a different model (optional)
    python scripts/agent_cli.py --message "..." --model gpt-4o

Environment:
    - OPENAI_API_KEY must be set (env var or .env file)
    - DATABASE_URL optional; only used when --save is provided
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv()

# Add project root for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager
from src.chatbot.bot_manager import BotManager

BOT_CHOICES = ["emotional", "cognitive", "motivational", "control"]


def _load_config(config_path: str = "config/app_config.yaml") -> dict:
    import yaml
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Test chatbot agent from terminal")
    parser.add_argument("--message", "-m", required=True, help="User message to send to the agent")
    parser.add_argument("--bot", "-b", choices=BOT_CHOICES, help="Which empathy style to use")
    parser.add_argument("--model", help="Override model (e.g., gpt-4o)")
    # Saving behavior: default is NO SAVE; --save opt-in. Keep --no-save for compatibility.
    parser.add_argument("--save", action="store_true", help="Persist participant and messages to the database")
    parser.add_argument("--no-save", action="store_true", help="(Deprecated) Do not write anything to the database (default)")
    parser.add_argument("--show-full-prompt", action="store_true", help="Print the entire system prompt, not just an excerpt")
    parser.add_argument(
        "--debug-print-messages",
        action="store_true",
        help="Print the exact message payload (system/history/user) sent to the model"
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not call the model; only print prompts/messages")
    args = parser.parse_args()

    # Load config and optionally override bot/model
    config = _load_config()
    if args.model:
        config.setdefault("api", {})
        config["api"]["model"] = args.model

    # Determine whether to save
    should_save = bool(args.save) and not bool(args.no_save)

    # Initialize DB (use in-memory SQLite when not saving to avoid touching remote DB)
    if should_save:
        db_path = config.get("database", {}).get("path", "data/database/conversations.db")
        db = DatabaseManager(db_path)
    else:
        db = DatabaseManager(db_url="sqlite:///:memory:")
    bot = BotManager(db, config)

    # Create a session and force bot_type if provided
    sess = bot.create_new_session()
    if args.bot:
        bot.sessions[sess["session_id"]]["bot_type"] = args.bot

    # Show the prompt that will be used
    bot_type = bot.sessions[sess["session_id"]]["bot_type"]
    prompt = bot.prompts.get(bot_type, "")
    print("== Agent Setup ==")
    print(f"Bot type: {bot_type}")
    print(f"Model: {bot.model}")
    if args.show_full_prompt:
        print("System prompt (FULL):")
        print("-" * 40)
        print(prompt or "<EMPTY>")
        print("-" * 40)
    else:
        print("System prompt (first 400 chars):")
        print("-" * 40)
        print(prompt[:400] + ("..." if len(prompt) > 400 else ""))
        print("-" * 40)

    # Persist participant and first message unless --no-save
    message_num = 1
    participant_id = sess["participant_id"]
    if should_save:
        db.create_participant(participant_id, bot_type)

    # Optionally print the exact request payload
    if args.debug_print_messages:
        messages_dbg = []
        if prompt:
            messages_dbg.append({"role": "system", "content": prompt})
        messages_dbg.append({"role": "user", "content": args.message})
        print("\n== Debug: request messages (what the model sees) ==")
        for i, m in enumerate(messages_dbg):
            preview = (m.get("content") or "")
            print(f"[{i}] {m.get('role')}: {preview[:200]}" + ("..." if len(preview) > 200 else ""))

    if args.dry_run:
        print("\n--dry-run: skipping model call.")
        return 0

    # Send the message
    print("\n== Sending user message ==")
    print(args.message)
    response = bot.get_bot_response(sess["session_id"], args.message, message_num)

    # Save messages if needed
    if should_save:
        db.save_message(participant_id, message_num, "user", args.message)
        db.save_message(participant_id, message_num, "bot", response["bot_response"], contains_crisis_keyword=response.get("crisis_detected", False))
        db.mark_participant_completed(participant_id)

    # Print the reply and crisis info
    print("\n== Agent reply ==")
    print(response["bot_response"]) 
    if response.get("crisis_detected"):
        print("\n[!] Crisis keyword detected.")
        if response.get("detected_keyword"):
            print(f"Keyword: {response['detected_keyword']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
