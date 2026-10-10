import json
import os
import re
from pathlib import Path

import ollama

ROOT = Path(__file__).parent
MODEL = os.environ.get("DIANA_MODEL", "qwen3:8b")
# Reasoning makes small models follow the rules and persona much better, but is slower on CPU.
THINK = os.environ.get("DIANA_THINK", "1") != "0"
# Ollama's default context is too small for the lore files plus a conversation.
CONTEXT_SIZE = 16384

SYSTEM_PROMPT = """You are Diana Burnwood, Agent 47's handler at the ICA.
You speak calmly, precisely and with dry British wit. You help the player with
the Hitman World of Assassination trilogy: missions, targets, achievements,
tactics and lore.

Rules:
- For any question about missions, targets or achievements, call a tool and
  answer from its result. Never guess these from memory.
- For game terms, mechanics, modes and story, answer from the background lore
  below. Hitman terms often have a game-specific meaning, so check the lore
  before answering.
- If neither the tools nor the lore cover it, say you don't have that intel.
  Never invent facts about the games.
- Stay in character as Diana, following "How Diana speaks" in the lore.
- Keep answers short unless asked for detail.
"""


def load_jsonc(path):
    text = path.read_text(encoding="utf-8")
    # Drop // comments (but not inside strings), then trailing commas.
    text = re.sub(r'("(?:\\.|[^"\\])*")|//[^\n]*', lambda m: m.group(1) or "", text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def load_targets():
    games = {}
    for path in sorted((ROOT / "targets").glob("*.jsonc")):
        games[path.stem] = load_jsonc(path)
    return games


def load_lore():
    lore_dir = ROOT / "lore"
    if not lore_dir.exists():
        return ""
    parts = [p.read_text(encoding="utf-8") for p in sorted(lore_dir.glob("*.md"))]
    return "\n\n".join(parts)


GAMES = load_targets()


def _entries():
    for game, locations in GAMES.items():
        for location, entry in locations.items():
            yield game, location, entry


def list_missions(game: str = "") -> str:
    """List all missions, optionally only for one game.

    Args:
        game: Optional game file name, e.g. "hitman1", "hitman2" or "hitman3". Empty for all games.
    """
    rows = [
        f"{g}: {location} - {entry['mission']}"
        for g, location, entry in _entries()
        if not game or g == game.lower().replace(" ", "")
    ]
    return "\n".join(rows) or "No missions found."


def get_mission(name: str) -> str:
    """Get the full details (game, location, mission, achievement, targets) of a mission.

    Args:
        name: Location or mission name, e.g. "Paris" or "The Showstopper".
    """
    query = name.lower()
    for game, location, entry in _entries():
        if query in location.lower() or query in entry["mission"].lower():
            return json.dumps({"game": game, "location": location, **entry}, ensure_ascii=False)
    return f"No mission matching '{name}'."


def find_target(name: str) -> str:
    """Find which mission a target appears in.

    Args:
        name: Full or partial target name, e.g. "Novikov".
    """
    query = name.lower()
    hits = [
        f"{target} - {game}, {location} ({entry['mission']})"
        for game, location, entry in _entries()
        for target in entry["targets"]
        if query in target.lower()
    ]
    return "\n".join(hits) or f"No target matching '{name}'."


TOOLS = {f.__name__: f for f in (list_missions, get_mission, find_target)}


def chat(messages):
    while True:
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=list(TOOLS.values()),
            think=THINK,
            options={"num_ctx": CONTEXT_SIZE},
        )
        messages.append(response.message)
        if not response.message.tool_calls:
            return response.message.content
        for call in response.message.tool_calls:
            func = TOOLS.get(call.function.name)
            result = func(**call.function.arguments) if func else f"Unknown tool {call.function.name}"
            messages.append({"role": "tool", "tool_name": call.function.name, "content": result})


def new_conversation():
    system = SYSTEM_PROMPT
    lore = load_lore()
    if lore:
        system += "\nBackground lore you may use:\n" + lore
    return [{"role": "system", "content": system}]
