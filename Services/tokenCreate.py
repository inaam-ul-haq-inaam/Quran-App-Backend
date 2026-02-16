import re
from typing import Any, Dict, Union, List
from Services.spellCheck import find_surah_id


def create_command_token(text: Union[str, List[str]]) -> Dict[str, Any]:

    # --- 1️⃣ Normalize Input ---
    if isinstance(text, list):
        text = " ".join(str(x) for x in text)

    if not text:
        text = ""

    text = str(text).strip().lower()

    # --- 2️⃣ Response Structure ---
    response: Dict[str, Any] = {
        "player": None,
        "surah": None,
        "from": None,
        "to": None
    }

    # --- 3️⃣ Unified Command Dictionary (English + Roman Urdu) ---
    COMMANDS = {
        "pause": ["pause", "stop", "ruko", "band", "wait", "thahro","pass"],
        "next": ["next", "agla", "age", "aage", "skip", "forward"],
        "previous": ["previous", "pichla", "peeche", "back", "wapis", "return"],
        "play": ["play", "chalao", "sunao", "laga", "start", "resume", "open"]
    }

    # --- 4️⃣ Detect Action (WORD SAFE MATCH) ---
    for action, keywords in COMMANDS.items():
        pattern = r"\b(" + "|".join(map(re.escape, keywords)) + r")\b"
        if re.search(pattern, text):
            response["player"] = action
            break

    # --- 5️⃣ Remove Command Words Before Surah Detection ---
    text_for_surah = text

    for keywords in COMMANDS.values():
        for word in keywords:
            text_for_surah = re.sub(
                rf"\b{re.escape(word)}\b", 
                "", 
                text_for_surah
            )

    clean_text = text_for_surah.strip()

    # --- 6️⃣ Surah Detection ---
    if len(clean_text) >= 3:
        surah_id = find_surah_id(clean_text)
    else:
        surah_id = None

    if surah_id:
        response["surah"] = surah_id
        # Agar sirf surah bola ho (no action), auto play
        if response["player"] is None:
            response["player"] = "play"

    # --- 7️⃣ Ayat Extraction ---
    numbers = [int(n) for n in re.findall(r"\b\d+\b", text)]

    if len(numbers) >= 1:
        response["from"] = numbers[0]

    if len(numbers) >= 2:
        response["to"] = numbers[1]

    return response
