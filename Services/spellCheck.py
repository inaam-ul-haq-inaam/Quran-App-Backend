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
    # Use token_set_ratio for better partial matching
    best_match, score = process.extractOne(
        text,
        SURAH_DB.keys(),
        scorer=fuzz.token_set_ratio
    )

    if score >= 70:  # 70% confidence threshold
        print(f"📖 Fuzzy Surah Detect: '{best_match}' (Score: {score}%) → ID: {SURAH_DB[best_match]}")
        return SURAH_DB[best_match]
    else:
        print(f"⚠️ No surah match found for: '{text}' (Best score: {score}%)")

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
    
    # First normalize text (handles aayat, ayah, etc.)
    text = normalize_text(text)
    
    # Pattern 1: "ayat 5" or "ayat 15"
    match = re.search(r'ayat\s+(\d+)', text)
    if match:
        ayat_num = int(match.group(1))
        print(f"📖 Ayat number extracted: {ayat_num}")
        return ayat_num
    
    # Pattern 2: Single number without "ayat" word (but not if it's part of range)
    # Check if it's a standalone number
    match = re.search(r'\b(\d+)\b', text)
    if match:
        # Make sure it's not part of a larger number sequence
        num = int(match.group(1))
        # Avoid extracting numbers that are part of range (like 3 in "3 to 5")
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
    Supports: "ayat 3 to 8", "ayat 1 se 5", "3 to 8"
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
# BAYAN INDEX EXTRACTION (First, Second, Third...)
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
# TARGET MATCHING (Quran, Bayan, Home, Back, Chain, Bookmark)
# ============================================================

def match_target(text: str) -> str:
    """
    Match target category from text
    Returns: target name or None
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
    Supports: "play chain mychain", "chain sunao daily"
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
    Supports: "bookmark fatiha as my favorite"
    """
    if not text:
        return None
    
    text = text.lower().strip()
    
    # Pattern: "bookmark fatiha as my favorite"
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
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    
    # Trim
    text = text.strip()
    
    return text


# ============================================================
# COMPLETE VOICE COMMAND PARSING
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
    
    result = {
        "original": original,
        "normalized": text,
        "command": None,
        "target": None,
        "surah_id": None,
        "surah_name": None,
        "reciter_id": None,
        "ayat_number": None,
        "ayat_from": None,
        "ayat_to": None,
        "bayan_index": None,
        "chain_name": None,
        "bookmark_title": None,
        "is_valid": False
    }
    
    # Extract components
    result["command"] = match_command(text)
    result["target"] = match_target(text)
    result["surah_id"] = find_surah_id(text)
    result["reciter_id"] = find_reciter_id(text)
    result["ayat_number"] = extract_ayat_number(text)
    result["ayat_from"], result["ayat_to"] = extract_ayat_range(text)
    result["bayan_index"] = extract_bayan_index(text)
    result["chain_name"] = extract_chain_name(text)
    result["bookmark_title"] = extract_bookmark_title(text)
    result["is_valid"] = is_valid_command(text)
    
    # If ayat range found, override single ayat number
    if result["ayat_from"] and result["ayat_to"]:
        result["ayat_number"] = None
    
    return result


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'find_surah_id',
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