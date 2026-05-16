# data.py - All Dictionaries for Voice Commands
# Complete with all features: Chain, Bookmark, Bayan, Range Playback, Player Controls
# Clean version – no duplicates, well-structured

import re

# ============================================================
# CHAIN KEYWORDS (for chain play & navigation)
# ============================================================
CHAIN_KEYWORDS = [
    "chain", "chains", "playlist", "list", "collection",
    "jane", "change", "chane", "chan"
]

# ============================================================
# CHAIN CREATION KEYWORDS
# ============================================================
CREATE_ACTION_KEYWORDS = ["create", "banao", "new", "banade", "nayi"]
ADD_ACTION_KEYWORDS = ["add", "add kar", "shamil karo", "daldo", "shamil kro"]
TARGET_LIST_KEYWORDS = ["list", "playlist", "chain list", "collection", "chains list"]

SELECT_ACTION_KEYWORDS = ["select", "choose", "pick", "chuno", "chune"]
SURAH_KEYWORDS = ["surah", "sura", "chapter", "para"]
AYAT_KEYWORDS = ["ayat", "aayat", "ayah", "aya", "ayaat"]

# ============================================================
# SURAH DATABASE (114 Surahs with multiple spellings)
# ============================================================
SURAH_DB = {
    # 1–10
    "fatiha": 1, "al fatiha": 1, "fateha": 1, "fathia": 1,
    "baqarah": 2, "baqara": 2, "bakra": 2, "bakarah": 2, "bakara": 2,
    "aal imran": 3, "imran": 3, "al imran": 3,
    "nisa": 4, "an nisa": 4, "neesa": 4, "nissa": 4,
    "maidah": 5, "maida": 5, "al maidah": 5,
    "anam": 6, "anaam": 6, "al anam": 6,
    "araf": 7, "aaraf": 7, "al araf": 7,
    "anfal": 8, "anfaal": 8, "al anfal": 8,
    "tawbah": 9, "tawba": 9, "tauba": 9, "al tawbah": 9,
    "yunus": 10, "younus": 10, "yunis": 10,

    # 11–20
    "hud": 11, "hood": 11,
    "yusuf": 12, "yousuf": 12, "joseph": 12,
    "rad": 13, "raad": 13, "al rad": 13,
    "ibrahim": 14, "ibraheem": 14, "abraheem": 14,
    "hijr": 15, "al hijr": 15,
    "nahl": 16, "al nahl": 16,
    "isra": 17, "bani israel": 17, "al isra": 17,
    "kahf": 18, "al kahf": 18, "kahaf": 18,
    "maryam": 19, "mariyam": 19, "marium": 19,
    "taha": 20, "ta ha": 20,

    # 21–30
    "anbiya": 21, "ambiya": 21, "al anbiya": 21,
    "hajj": 22, "haj": 22, "al hajj": 22,
    "muminun": 23, "mominoon": 23, "al muminun": 23,
    "nur": 24, "noor": 24, "al nur": 24,
    "furqan": 25, "al furqan": 25,
    "shuara": 26, "shuaraa": 26, "al shuara": 26,
    "naml": 27, "al naml": 27,
    "qasas": 28, "kasas": 28, "al qasas": 28,
    "ankabut": 29, "ankaboot": 29, "spider": 29, "al ankabut": 29,
    "rum": 30, "room": 30, "rome": 30, "al rum": 30,

    # 31–40
    "luqman": 31, "lukman": 31, "al luqman": 31,
    "sajdah": 32, "sajda": 32, "al sajdah": 32,
    "ahzab": 33, "al ahzab": 33,
    "saba": 34, "al saba": 34,
    "fatir": 35, "al fatir": 35,
    "yasin": 36, "yaseen": 36, "ya sin": 36,
    "saffat": 37, "al saffat": 37,
    "sad": 38, "saad": 38, "al sad": 38,
    "zumar": 39, "al zumar": 39,
    "ghafir": 40, "mumin": 40, "al ghafir": 40,

    # 41–50
    "fussilat": 41, "hamim sajdah": 41, "al fussilat": 41,
    "ash shura": 42, "shuraa": 42, "al shura": 42,
    "zukhruf": 43, "al zukhruf": 43,
    "dukhan": 44, "al dukhan": 44,
    "jathiyah": 45, "al jathiyah": 45,
    "ahqaf": 46, "al ahqaf": 46,
    "muhammad": 47, "al muhammad": 47,
    "fath": 48, "al fath": 48,
    "hujurat": 49, "al hujurat": 49,
    "qaf": 50, "qaaf": 50, "al qaf": 50,

    # 51–60
    "dhariyat": 51, "zariyat": 51, "al dhariyat": 51,
    "tur": 52, "toor": 52, "al tur": 52,
    "najm": 53, "al najm": 53,
    "qamar": 54, "al qamar": 54,
    "rahman": 55, "rehman": 55, "ar rahman": 55, "al rahman": 55,
    "waqiah": 56, "waqia": 56, "al waqiah": 56,
    "hadid": 57, "hadeed": 57, "al hadid": 57,
    "mujadilah": 58, "al mujadilah": 58,
    "hashr": 59, "al hashr": 59,
    "mumtahanah": 60, "al mumtahanah": 60,

    # 61–70
    "saff": 61, "al saff": 61,
    "jumuah": 62, "jumma": 62, "al jumuah": 62,
    "munafiqun": 63, "al munafiqun": 63,
    "taghabun": 64, "al taghabun": 64,
    "talaq": 65, "al talaq": 65,
    "tahrim": 66, "al tahrim": 66,
    "mulk": 67, "al mulk": 67,
    "qalam": 68, "al qalam": 68,
    "haqqah": 69, "al haqqah": 69,
    "maarij": 70, "al maarij": 70,

    # 71–80
    "nuh": 71, "nooh": 71,
    "jinn": 72, "al jinn": 72,
    "muzzammil": 73, "al muzzammil": 73,
    "muddathir": 74, "al muddathir": 74,
    "qiyamah": 75, "al qiyamah": 75,
    "insan": 76, "dahr": 76, "al insan": 76,
    "mursalat": 77, "al mursalat": 77,
    "naba": 78, "al naba": 78,
    "naziat": 79, "al naziat": 79,
    "abasa": 80, "al abasa": 80,

    # 81–90
    "takwir": 81, "al takwir": 81,
    "infitar": 82, "al infitar": 82,
    "mutaffifin": 83, "al mutaffifin": 83,
    "inshiqaq": 84, "al inshiqaq": 84,
    "buruj": 85, "al buruj": 85,
    "tariq": 86, "al tariq": 86,
    "ala": 87, "aala": 87, "al ala": 87,
    "ghashiyah": 88, "al ghashiyah": 88,
    "fajr": 89, "al fajr": 89,
    "balad": 90, "al balad": 90,

    # 91–100
    "shams": 91, "al shams": 91,
    "layl": 92, "lail": 92, "al layl": 92,
    "duha": 93, "wadduha": 93, "al duha": 93,
    "sharh": 94, "inshirah": 94, "al sharh": 94,
    "tin": 95, "teen": 95, "al tin": 95,
    "alaq": 96, "al alaq": 96,
    "qadr": 97, "al qadr": 97,
    "bayyinah": 98, "al bayyinah": 98,
    "zalzalah": 99, "al zalzalah": 99,
    "adiyat": 100, "al adiyat": 100,

    # 101–114
    "qariah": 101, "al qariah": 101,
    "takathur": 102, "al takathur": 102,
    "asr": 103, "al asr": 103,
    "humazah": 104, "al humazah": 104,
    "fil": 105, "elephant": 105, "al fil": 105,
    "quraysh": 106, "quraish": 106, "al quraysh": 106,
    "maun": 107, "al maun": 107,
    "kawthar": 108, "kausar": 108, "al kawthar": 108,
    "kafirun": 109, "al kafirun": 109,
    "nasr": 110, "al nasr": 110,
    "masad": 111, "lahab": 111, "al masad": 111,
    "ikhlas": 112, "ahad": 112, "al ikhlas": 112,
    "falaq": 113, "falak": 113, "al falaq": 113,
    "nas": 114, "naas": 114, "an nas": 114
}

# ============================================================
# HISTORY / STATS KEYWORDS
# ============================================================
HISTORY_KEYWORDS = {
    "last": ["last", "recent", "previous", "latest"],
    "items": ["items", "plays", "history", "list"],
    "surahs": ["surahs", "sura", "quran"],
    "bayans": ["bayans", "lectures", "bayanat"],
    "chains": ["chains", "playlists"],
    "most_played": ["most played", "favorite", "top", "most listened"],
    "count": ["times", "time", "count", "frequency"]
}

# ============================================================
# RECITER DATABASE
# ============================================================
RECITER_DB = {
    "afasy": 1, "al afasy": 1, "mishary": 1, "mishari": 1, "mishary al afasy": 1,
    "sudais": 2, "abdul rahman al sudais": 2,
    "shuraim": 3, "shuraym": 3,
    "ghamdi": 4, "al ghamdi": 4,
    "yassin": 5, "yaseen": 5, "sheikh yassin": 5
}

# ============================================================
# COMMANDS DICTIONARY (All possible spellings)
# ============================================================
COMMANDS = {
    "play": ["play", "pley", "pla", "chalao", "sunao", "laga", "start", "continue", "shuru"],
    "pause": ["pause", "paws", "ruko", "band", "wait", "hold", "thairo", "rok", "thahro"],
    "stop": ["stop", "stap", "band kar", "rok do", "khatam", "close", "end", "khatam karo"],
    "resume": ["resume", "rizoom", "continue", "agey", "aage se", "phir se", "dobara", "jari rakho"],
    "next": ["next", "nekst", "agla", "agli", "age", "aage", "forward", "skip", "aagay", "agla ayat", "next ayat"],
    "previous": ["previous", "preveyas", "pichla", "pichli", "back", "wapis", "peeche", "pichay", "return", "pichla ayat", "back ayat"],
    "create_chain": ["create chain", "banao chain", "new chain", "nayi chain", "chain banao"],
    "select_surah": ["select surah", "choose surah", "surah select", "surah choose", "chuno surah"],
    "select_ayat": ["select ayat", "choose ayat", "ayat select", "ayat choose", "chuno ayat"],
    "add_to_list": ["add to list", "list mein add", "add kar", "shamil karo", "list mein dalo", "add"],
    "save_chain": ["save chain", "chain save", "mehfooz chain", "store chain", "chain save karo"],
    "remove_last": ["remove last", "last remove", "akhri hatao", "pichla hatao", "last hatao"],
    "clear_all": ["clear all", "all clear", "sab hatao", "saf karo", "clear karo", "sab clear"],
    "show_list": ["show list", "list show", "list dikhao", "dikhao list", "kya hai"],
    "cancel_chain": ["cancel chain", "chain cancel", "cancel", "mansookh", "cancel karo"],
    "bookmark_surah": ["bookmark surah", "surah bookmark", "nishan surah", "save surah"],
    "bookmark_ayat": ["bookmark ayat", "ayat bookmark", "nishan ayat", "save ayat"],
    "bookmark_range": ["bookmark range", "range bookmark", "nishan range", "save range"],
    "show_bookmarks": ["show bookmarks", "my bookmarks", "bookmarks dikhao", "mere nishan", "bookmark list"],
    "bookmark_with_title": ["bookmark as", "save as", "nishan as"],
    "bayan": ["bayan", "bayaan", "baya", "beaan", "biyan", "bayn", "byan", "beyon", "beyond"],
    "ayat": ["ayat", "aayat", "ayah", "aya", "ayaat", "ayet", "ayath", "ayyat", "aiat", "ayatt"],
    "surah": ["surah", "sura", "sora", "sara", "chapter", "para"],
    "jump": ["jump", "jamp", "go to", "goto", "jao", "chalo", "le chalo", "lejao", "jump to"],
    "open": ["open", "kholo", "go to", "show", "le chalo", "dikhao"],
    "read": ["read", "reed", "parho", "tilawat", "text", "padho"],
    "play_range": ["play range", "range play", "ayat range"],
}

# ============================================================
# BAYAN INDEX MAPPING (First, Second, Third, etc.)
# ============================================================
BAYAN_INDEX_MAP = {
    "first": 0, "pehla": 0, "1st": 0, "one": 0,
    "second": 1, "dosra": 1, "2nd": 1, "two": 1,
    "third": 2, "tesra": 2, "3rd": 2, "three": 2,
    "fourth": 3, "chautha": 3, "4th": 3, "four": 3,
    "fifth": 4, "panchwa": 4, "5th": 4, "five": 4,
    "sixth": 5, "6th": 5, "six": 5,
    "seventh": 6, "7th": 6, "seven": 6,
    "eighth": 7, "8th": 7, "eight": 7,
    "ninth": 8, "9th": 8, "nine": 8,
    "tenth": 9, "10th": 9, "ten": 9,
}

# ============================================================
# TARGETS (Categories for navigation)
# ============================================================
TARGETS = {
    "quran": ["quran", "mushaf", "qurane", "quran pak", "kuran"],
    "bayan": ["bayan", "bayanat", "lecture", "tafseer", "taqreer"],
    "home": ["home", "main screen", "ghar", "home screen", "start"],
    "back": ["back", "wapis", "peeche", "return", "pichay"],
    "chain": ["chain", "chains", "playlist", "list", "collection", "change", "jane", "chane", "chan"],
    "bookmark": ["bookmark", "bookmarks", "nishan", "mahfooz", "saved", "bukmark", "bokmark", "book mark", "buk mark", "bookmrk"],
}

# ============================================================
# WHISPER PROMPT (For frontend speech recognition)
# ============================================================
WHISPER_PROMPT = (
    "quran, mushaf, surah, ayat, reciter, qari, mishary, sudais, "
    "play, chalao, sunao, start, pause, ruko, stop, "
    "next, agli, forward, previous, pichli, back, "
    "open, kholo, go to, read, parho, "
    "bookmark, nishan, unmark, remove bookmark, "
    "save, mehfooz, store, "
    "bayan, bayaan, beyon, beyond, tafseer, bayern, "
    "chain, playlist, create, banao, new, jane, "
    "first, second, third, pehla, dosra, tesra, "
    "ayat, aayat, ayah, aya, ayaat, "
    "create chain, select surah, select ayat, add to list, save chain, "
    "bookmark surah, bookmark ayat, show bookmarks"
)

# ============================================================
# AYAT SPELLING VARIANTS (regex patterns with word boundaries)
# ============================================================
AYAT_PATTERNS = [
    (re.compile(r'\b(?:aayat|ayah|aya|ayaat|ayet|ayath|ayyat|aiat|ayatt)\b', re.IGNORECASE), 'ayat')
]

BAYAN_PATTERNS = [
    (re.compile(r'\b(?:bayaan|baya|beaan|biyan|bayn|byan|beyond|bian|beyon|bayern)\b', re.IGNORECASE), 'bayan')
]

COMMAND_PATTERNS = [
    (re.compile(r'\b(?:chalao|sunao|laga)\b', re.IGNORECASE), 'play'),
    (re.compile(r'\b(?:ruko|band|thairo)\b', re.IGNORECASE), 'pause'),
    (re.compile(r'\b(?:band kar|rok do|khatam)\b', re.IGNORECASE), 'stop'),
    (re.compile(r'\b(?:agla|agli|aage)\b', re.IGNORECASE), 'next'),
    (re.compile(r'\b(?:pichla|pichli|wapis)\b', re.IGNORECASE), 'previous'),
    (re.compile(r'\b(?:banao|bana do)\b', re.IGNORECASE), 'create'),
    (re.compile(r'\b(?:mehfooz|bachao|rakho)\b', re.IGNORECASE), 'save'),
    (re.compile(r'\b(?:nishan|mark)\b', re.IGNORECASE), 'bookmark'),
    (re.compile(r'\b(?:kholo|dikhao)\b', re.IGNORECASE), 'open'),
]

# ============================================================
# NUMBER WORDS TO DIGITS CONVERSION
# ============================================================
NUMBER_WORDS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
    'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
    'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
    'eighteen': 18, 'nineteen': 19, 'twenty': 20,
    'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60,
    'seventy': 70, 'eighty': 80, 'ninety': 90,
}

def convert_number_words_to_digits(text: str) -> str:
    if not text:
        return text
    words = text.split()
    converted = []
    for w in words:
        if w.lower() in NUMBER_WORDS:
            converted.append(str(NUMBER_WORDS[w.lower()]))
        else:
            converted.append(w)
    return ' '.join(converted)

# ============================================================
# NORMALIZATION FUNCTION (word-boundary safe)
# ============================================================
def normalize_text(text: str) -> str:
    """Complete text normalization using word-boundary replacements."""
    if not text:
        return text

    original = text
    text = text.lower().strip()

    # 1. Convert number words to digits
    text = convert_number_words_to_digits(text)

    # 2. Replace BAYAN variants (whole words only)
    for pattern, replacement in BAYAN_PATTERNS:
        text = pattern.sub(replacement, text)

    # 3. Replace AYAT variants (whole words only)
    for pattern, replacement in AYAT_PATTERNS:
        text = pattern.sub(replacement, text)

    # 4. Replace command words (whole words only)
    for pattern, replacement in COMMAND_PATTERNS:
        text = pattern.sub(replacement, text)

    if original != text:
        print(f"📝 Normalized: '{original}' → '{text}'")

    return text

# ============================================================
# ADD THE MISSING LISTS REQUIRED BY tokenCreate.py
# ============================================================
PLAYER_COMMANDS = ["play", "pause", "stop", "resume", "next", "previous", "jump"]

SKIP_ACTIONS = [
    "select_surah", "select_ayat", "add_to_list", "set_title", "save_chain",
    "remove_last", "clear_all", "show_list", "cancel_chain", "open_chain_builder",
    "bookmark_surah", "bookmark_ayat", "bookmark_range", "bookmark_with_title",
    "show_bookmarks", "play_range", "play_chain", "next", "previous", "pause",
    "resume", "stop", "jump", "play"
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_surah_id(name: str) -> int:
    return SURAH_DB.get(name.lower(), None)

def get_reciter_id(name: str) -> int:
    return RECITER_DB.get(name.lower(), None)

def get_bayan_index(word: str) -> int:
    return BAYAN_INDEX_MAP.get(word.lower(), None)

# ============================================================
# EXPORTS (what other files can import)
# ============================================================
__all__ = [
    'SURAH_DB',
    'RECITER_DB',
    'COMMANDS',
    'BAYAN_INDEX_MAP',
    'TARGETS',
    'WHISPER_PROMPT',
    'normalize_text',
    'get_surah_id',
    'get_reciter_id',
    'get_bayan_index',
    'PLAYER_COMMANDS',
    'SKIP_ACTIONS',
    'HISTORY_KEYWORDS',
    # Additional lists that might be used elsewhere
    'CHAIN_KEYWORDS',
    'CREATE_ACTION_KEYWORDS',
    'ADD_ACTION_KEYWORDS',
    'TARGET_LIST_KEYWORDS',
    'SELECT_ACTION_KEYWORDS',
    'SURAH_KEYWORDS',
    'AYAT_KEYWORDS',
]