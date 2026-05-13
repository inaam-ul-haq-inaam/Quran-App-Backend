# spellCheck.py - Main Spell Checking and Fuzzy Matching Logic
# Handles: Surah detection, Reciter detection, Ayat extraction, Bayan index extraction

import re
from thefuzz import process, fuzz

# Import all data from data.py
from Services.data import (
    SURAH_DB,
    RECITER_DB,
    COMMANDS,
    BAYAN_INDEX_MAP,
    TARGETS,
    WHISPER_PROMPT,
    normalize_text,
    PLAYER_COMMANDS,
    SKIP_ACTIONS
)


# ============================================================
# SURAH DETECTION (with fuzzy matching)
# ============================================================

def find_surah_id(text: str) -> int:
    """
    Find surah ID from text with multiple matching strategies:
    1. Exact match
    2. Direct word match
    3. Phrase match
    4. Fuzzy match (thefuzz library)
    """
    if not text:
        return None

    text = text.lower().strip()

    # 1️⃣ Exact full match (fastest)
    if text in SURAH_DB:
        print(f"📖 Exact Surah Match: '{text}' → ID: {SURAH_DB[text]}")
        return SURAH_DB[text]

    words = text.split()

    # 2️⃣ Direct word match (check each word)
    for word in words:
        if word in SURAH_DB:
            print(f"📖 Direct Word Match: '{word}' → ID: {SURAH_DB[word]}")
            return SURAH_DB[word]

    # 3️⃣ Multi-word phrase match
    for key in SURAH_DB.keys():
        if key in text:
            print(f"📖 Phrase Match: '{key}' → ID: {SURAH_DB[key]}")
            return SURAH_DB[key]

    # 4️⃣ Fuzzy fallback (for spelling mistakes)
    best_match, score = process.extractOne(
        text,
        SURAH_DB.keys(),
        scorer=fuzz.token_set_ratio
    )

    if score >= 70:
        print(f"📖 Fuzzy Surah Detect: '{best_match}' (Score: {score}%) → ID: {SURAH_DB[best_match]}")
        return SURAH_DB[best_match]
    else:
        print(f"⚠️ No surah match found for: '{text}' (Best score: {score}%)")

    return None


# ============================================================
# GET SURAH NAME FROM ID (NEW)
# ============================================================

def get_surah_name_from_id(surah_id: int) -> str:
    """
    Get surah name from ID
    Returns: surah name or None
    """
    if not surah_id:
        return None
    
    # Reverse lookup in SURAH_DB
    for name, sid in SURAH_DB.items():
        if sid == surah_id:
            # Return capitalized name
            return name.title()
    
    return None


# ============================================================
# GET SURAH NAME FROM TEXT (NEW - Most Important)
# ============================================================

def find_surah_name(text: str) -> str:
    """
    Find surah name from text (returns name, not ID)
    """
    if not text:
        return None
    
    surah_id = find_surah_id(text)
    if surah_id:
        return get_surah_name_from_id(surah_id)
    
    return None


# ============================================================
# RECITER DETECTION (with fuzzy matching)
# ============================================================

def find_reciter_id(text: str) -> int:
    """
    Find reciter ID from text
    Supports: Mishary, Sudais, Shuraim, Ghamdi, etc.
    """
    if not text:
        return None

    text = text.lower().strip()

    # 1️⃣ Exact match
    if text in RECITER_DB:
        print(f"🎤 Exact Reciter Match: '{text}' → ID: {RECITER_DB[text]}")
        return RECITER_DB[text]

    # 2️⃣ Phrase match (contains keyword)
    for key, reciter_id in RECITER_DB.items():
        if key in text:
            print(f"🎤 Phrase Reciter Match: '{key}' → ID: {reciter_id}")
            return reciter_id

    # 3️⃣ Fuzzy fallback
    best_match, score = process.extractOne(
        text,
        RECITER_DB.keys(),
        scorer=fuzz.token_set_ratio
    )

    if score >= 85:
        print(f"🎤 Fuzzy Reciter Detect: '{best_match}' (Score: {score}%) → ID: {RECITER_DB[best_match]}")
        return RECITER_DB[best_match]

    return None


# ============================================================
# AYAT NUMBER EXTRACTION
# ============================================================

def extract_ayat_number(text: str) -> int:
    """
    Extract ayat number from text
    Supports: "ayat 5", "aayat 15", "ayah 3", or just "5"
    """
    if not text:
        return None
    
    text = normalize_text(text)
    
    # Pattern 1: "ayat 5" or "ayat 15"
    match = re.search(r'ayat\s+(\d+)', text)
    if match:
        ayat_num = int(match.group(1))
        print(f"📖 Ayat number extracted: {ayat_num}")
        return ayat_num
    
    # Pattern 2: Single number without "ayat" word
    match = re.search(r'\b(\d+)\b', text)
    if match:
        num = int(match.group(1))
        if not re.search(rf'{num}\s+(?:to|se)\s+\d+', text):
            print(f"📖 Standalone number extracted as ayat: {num}")
            return num
    
    return None


# ============================================================
# AYAT RANGE EXTRACTION
# ============================================================

def extract_ayat_range(text: str) -> tuple:
    """
    Extract ayat range from text
    Returns: (from_ayat, to_ayat) or (None, None)
    """
    if not text:
        return None, None
    
    text = normalize_text(text)
    
    # Pattern 1: "ayat 3 to 8" or "ayat 1 se 5"
    match = re.search(r'ayat\s+(\d+)\s+(?:to|se)\s+(\d+)', text)
    if match:
        from_ayat = int(match.group(1))
        to_ayat = int(match.group(2))
        print(f"📖 Ayat range extracted: {from_ayat} to {to_ayat}")
        return from_ayat, to_ayat
    
    # Pattern 2: "3 to 8" or "1 se 5"
    match = re.search(r'(\d+)\s+(?:to|se)\s+(\d+)', text)
    if match:
        from_ayat = int(match.group(1))
        to_ayat = int(match.group(2))
        print(f"📖 Ayat range extracted (no keyword): {from_ayat} to {to_ayat}")
        return from_ayat, to_ayat
    
    return None, None


# ============================================================
# BAYAN INDEX EXTRACTION
# ============================================================

def extract_bayan_index(text: str) -> int:
    """
    Extract bayan index from text
    Supports: "first", "second", "third", "pehla", "dosra", "tesra", etc.
    Returns: 0-based index or None
    """
    if not text:
        return None
    
    text = text.lower()
    
    for word, index in BAYAN_INDEX_MAP.items():
        if word in text:
            print(f"📖 Bayan index extracted: '{word}' → {index}")
            return index
    
    return None


# ============================================================
# COMMAND MATCHING
# ============================================================

def match_command(text: str) -> str:
    """
    Match command text to action
    Returns: action name or None
    """
    if not text:
        return None
    
    text = text.lower().strip()
    
    for action, keywords in COMMANDS.items():
        for keyword in keywords:
            if keyword in text:
                print(f"🎯 Command matched: '{keyword}' → {action}")
                return action
    
    return None


# ============================================================
# TARGET MATCHING
# ============================================================

def match_target(text: str) -> str:
    """
    Match target category from text
    """
    if not text:
        return None
    
    text = text.lower().strip()
    
    for target, keywords in TARGETS.items():
        for keyword in keywords:
            if keyword in text:
                print(f"🎯 Target matched: '{keyword}' → {target}")
                return target
    
    return None


# ============================================================
# CHAIN NAME EXTRACTION
# ============================================================

def extract_chain_name(text: str) -> str:
    """
    Extract chain name from text
    """
    if not text:
        return None
    
    text = text.lower().strip()
    
    # Pattern 1: "play chain daily"
    match = re.search(r'(?:play|sunao|chalao)\s+chain\s+(\w+(?:\s+\w+)?)', text)
    if match:
        chain_name = match.group(1).strip()
        print(f"📖 Chain name extracted: '{chain_name}'")
        return chain_name
    
    # Pattern 2: "daily chain play"
    match = re.search(r'(\w+(?:\s+\w+)?)\s+chain\s+(?:play|sunao|chalao)', text)
    if match:
        chain_name = match.group(1).strip()
        print(f"📖 Chain name extracted (reverse): '{chain_name}'")
        return chain_name
    
    return None


# ============================================================
# BOOKMARK TITLE EXTRACTION
# ============================================================

def extract_bookmark_title(text: str) -> str:
    """
    Extract custom bookmark title from text
    """
    if not text:
        return None
    
    text = text.lower().strip()
    
    match = re.search(r'bookmark\s+([a-z]+)\s+as\s+(.+)', text)
    if match:
        surah_name = match.group(1)
        title = match.group(2).strip()
        full_title = f"{surah_name.capitalize()} - {title}"
        print(f"📖 Bookmark title extracted: '{full_title}'")
        return full_title
    
    return None


# ============================================================
# VALIDATE AND CLEAN TEXT
# ============================================================

def is_valid_command(text: str) -> bool:
    """
    Check if text contains any valid command
    """
    if not text:
        return False
    
    text = text.lower().strip()
    
    for keywords in COMMANDS.values():
        for keyword in keywords:
            if keyword in text:
                return True
    
    return False


def clean_text(text: str) -> str:
    """
    Remove extra spaces, punctuation, and normalize
    """
    if not text:
        return text
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = text.strip()
    
    return text


# ============================================================
# COMPLETE VOICE COMMAND PARSING (FIXED)
# ============================================================

def parse_voice_command(text: str) -> dict:
    """
    Complete voice command parsing - one stop solution
    Returns dict with all extracted information
    """
    if not text:
        return None
    
    # Normalize and clean
    original = text
    text = normalize_text(text)
    text = clean_text(text)
    
    # Extract surah ID first
    surah_id = find_surah_id(text)
    surah_name = get_surah_name_from_id(surah_id) if surah_id else None
    
    result = {
        "original": original,
        "normalized": text,
        "command": match_command(text),
        "target": match_target(text),
        "surah_id": surah_id,
        "surah_name": surah_name,           # 🔥 FIXED: Now will have value
        "reciter_id": find_reciter_id(text),
        "ayat_number": extract_ayat_number(text),
        "ayat_from": None,
        "ayat_to": None,
        "bayan_index": extract_bayan_index(text),
        "chain_name": extract_chain_name(text),
        "bookmark_title": extract_bookmark_title(text),
        "is_valid": is_valid_command(text)
    }
    
    # Extract range
    from_ayat, to_ayat = extract_ayat_range(text)
    result["ayat_from"] = from_ayat
    result["ayat_to"] = to_ayat
    
    # If ayat range found, override single ayat number
    if result["ayat_from"] and result["ayat_to"]:
        result["ayat_number"] = None
    
    print(f"📊 Parsed Result: surah_id={result['surah_id']}, surah_name={result['surah_name']}")
    
    return result


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'find_surah_id',
    'find_surah_name',           # NEW
    'get_surah_name_from_id',    # NEW
    'find_reciter_id',
    'extract_ayat_number',
    'extract_ayat_range',
    'extract_bayan_index',
    'extract_chain_name',
    'extract_bookmark_title',
    'match_command',
    'match_target',
    'is_valid_command',
    'clean_text',
    'parse_voice_command',
    'normalize_text',
    'WHISPER_PROMPT',
    'PLAYER_COMMANDS',
    'SKIP_ACTIONS'
]