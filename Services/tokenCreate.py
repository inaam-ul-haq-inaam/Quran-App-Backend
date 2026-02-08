import re
from Services.spellCheck import find_surah_id, find_reciter_id
from Services.romanUrdu import COMMANDS, TARGETS

def extract_ayat_range(text):
    """
    Finds numbers like: "Ayat 5 to 10" or "Ayat 5"
    """
    numbers = re.findall(r'\d+', text)
    if len(numbers) == 1: return int(numbers[0]), None
    elif len(numbers) >= 2: return int(numbers[0]), int(numbers[1])
    return None, None

def create_command_token(text):
    text = text.lower()
    
    # --- OUTPUT STRUCTURE (Bilkul Simple) ---
    token = {
        "intent": "unknown",     # navigation | play_audio | control | bookmark
        "data": {
            "surah_id": None,
            "ayat_from": None,
            "ayat_to": None,
            "reciter_id": None,
            "target_screen": None,  # For navigation
            "action": None          # For pause/next/resume
        },
        "raw_text": text
    }

    # --- 1. DATA EXTRACTION (Jo mila nikaal lo) ---
    token["data"]["surah_id"] = find_surah_id(text)
    token["data"]["reciter_id"] = find_reciter_id(text)
    token["data"]["ayat_from"], token["data"]["ayat_to"] = extract_ayat_range(text)

    # --- 2. INTENT DETECTION (Maqsad dhundo) ---

    # PRIORITY 1: NAVIGATION (Open X)
    if "open" in text or "go to" in text or "kholo" in text:
        token["intent"] = "navigation"
        # Check target screen
        for screen, keywords in TARGETS.items():
            if any(w in text for w in keywords):
                token["data"]["target_screen"] = screen
                return token # Yahi return kr do, aage check krne ki zaroorat nahi

    # PRIORITY 2: PLAYING SURAH (Agar Surah ID mili hai)
    if token["data"]["surah_id"]:
        if "bookmark" in text:
            token["intent"] = "bookmark"
        elif "read" in text:
            token["intent"] = "read_mode"
        else:
            token["intent"] = "play_audio" # Default action for Surah
        return token

    # PRIORITY 3: PLAYER CONTROLS (Pause, Next, etc.)
    # Check if any command keyword exists in text
    for cmd, keywords in COMMANDS.items():
        if cmd in ["play", "pause", "next", "previous"]: # Sirf controls check kro
            if any(w in text for w in keywords):
                token["intent"] = "control"
                token["data"]["action"] = cmd
                return token

    return token