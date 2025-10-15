# bot_manager.py
"""
Unified BotManager
- Manages sessions (create_new_session / get_bot_response / end_session)
- Loads empathy prompts (cognitive/emotional/motivational/control)
- Calls provider APIs (OpenAI, Gemini, Anthropic) using modern patterns
- Crisis detection: short-circuits to crisis response
"""

import os
import uuid
import random
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try imports for flexible project layouts
try:
    from crisis_detector import CrisisDetector
except Exception:
    CrisisDetector = None  # Will disable if module not present

# ---- Utility helpers ---------------------------------------------------------

def _get_cfg(cfg: dict, path: List[str], default=None):
    cur = cfg or {}
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur

def _first_existing_path(paths: List[str]) -> Optional[str]:
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None

def _read_text(paths: List[str]) -> str:
    fp = _first_existing_path(paths)
    if not fp:
        return ""
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

# ---- BotManager --------------------------------------------------------------

class BotManager:
    def __init__(self, db_manager, config: dict):
        self.db = db_manager
        self.config = config or {}

        # API settings (OpenAI only)
        self.api_provider = "openai"
        self.model = _get_cfg(self.config, ["api", "model"], "gpt-4")
        self.temperature = float(_get_cfg(self.config, ["api", "temperature"], 0.7))
        self.max_tokens = int(_get_cfg(self.config, ["api", "max_tokens"], 1024))

        # Paths (support both ./config and project root)
        self.app_cfg_path = _first_existing_path(["config/app_config.yaml", "app_config.yaml"])
        self.crisis_text_path = _first_existing_path(["config/crisis_response.txt", "crisis_response.txt"])
        self.prompts = {
            "cognitive": _read_text(["config/cognitive_empathy_prompt.txt", "cognitive_empathy_prompt.txt"]),
            "emotional": _read_text(["config/emotional_empathy_prompt.txt", "emotional_empathy_prompt.txt"]),
            "motivational": _read_text(["config/motivational_empathy_prompt.txt", "motivational_empathy_prompt.txt"]),
            "control": ""  # neutral baseline
        }
        self.bot_types = ["cognitive", "emotional", "motivational", "control"]

        # Sessions (in memory)
        self.sessions: Dict[str, Dict[str, Any]] = {}

        # Crisis detector (optional)
        self.crisis = None
        if CrisisDetector is not None and self.app_cfg_path:
            try:
                self.crisis = CrisisDetector(config_path=self.app_cfg_path)
            except Exception:
                self.crisis = None

        # Initialize provider client
        self._init_client()

    # ---------- Public API expected by app.py ----------

    def create_new_session(self) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        participant_id = f"P{str(uuid.uuid4())[:8].upper()}"
        bot_type = random.choice(self.bot_types)
        self.sessions[session_id] = {
            "participant_id": participant_id,
            "bot_type": bot_type,
            "history": []  # [{"role":"user"/"assistant", "content": "..."}]
        }
        return {"session_id": session_id, "participant_id": participant_id, "bot_type": bot_type}

    def get_bot_response(self, session_id: str, user_message: str, message_num: int) -> Dict[str, Any]:
        sess = self.sessions.get(session_id)
        if not sess:
            raise ValueError(f"Session not found: {session_id}")

        # Crisis short-circuit (if configured)
        if self.crisis:
            try:
                is_crisis, detected_keyword = self.crisis.check_message(user_message)
            except Exception:
                is_crisis, detected_keyword = False, None
            if is_crisis:
                return {
                    "bot_response": self._crisis_text(),
                    "crisis_detected": True,
                    "detected_keyword": detected_keyword,
                }

        bot_type = sess["bot_type"]
        system_prompt = self.prompts.get(bot_type, "")

        # Build messages (system + history + current)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        # include limited history (last 10 exchanges)
        hist = sess["history"][-20:]
        messages.extend(hist)
        messages.append({"role": "user", "content": user_message})

        # Call the model
        reply = self._call_model(messages)

        # Update history
        sess["history"].append({"role": "user", "content": user_message})
        sess["history"].append({"role": "assistant", "content": reply})

        return {
            "bot_response": reply,
            "crisis_detected": False,
            "detected_keyword": None,
        }

    def end_session(self, session_id: str, completed: bool = True):
        # Nothing fancy; just drop in-memory state
        if session_id in self.sessions:
            del self.sessions[session_id]

    # ---------- Provider clients ----------

    def _init_client(self):
        # Initialize OpenAI client only
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # Fallback to Streamlit secrets when running on Streamlit Cloud
                try:
                    import streamlit as st  # type: ignore
                    api_key = st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None
                except Exception:
                    api_key = None
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self._client = OpenAI(api_key=api_key)
            self._provider = "openai"
        except Exception as e:
            raise RuntimeError(f"Failed to init OpenAI client: {e}")

    def _call_model(self, messages: List[Dict[str, str]]) -> str:
        try:
            # OpenAI only - simplified
            resp = self._client.chat.completions.create(
                model=self.model or "gpt-4",
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()



        except Exception as e:
            return f"I’m sorry, I ran into an error: {e}"

    # ---------- Crisis text helper ----------

    def _crisis_text(self) -> str:
        # Prefer CrisisDetector's configured response if available
        if self.crisis and hasattr(self.crisis, "get_crisis_response"):
            try:
                return self.crisis.get_crisis_response()
            except Exception:
                pass
        # Fallback: read file directly
        txt = _read_text([self.crisis_text_path] if self.crisis_text_path else [])
        return txt or (
            "I'm concerned about your safety. If you are in immediate danger, please call your local emergency number. "
            "You can also reach out to a trusted person or a professional helpline available in your area."
        )
