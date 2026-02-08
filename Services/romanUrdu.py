
WHISPER_PROMPT = (
    "quran play, surah fatiha, ayat, reciter mishary, sudais, qari, "
    "bayan, chain create, bookmark, save, home, go back, unmark, "
    "resume, pause, next, previous, open, read"
)

COMMANDS = {
    "play": ["play", "chalao", "sunao", "laga", "start", "resume"],
    "pause": ["pause", "ruko", "stop", "band", "wait"],
    "next": ["next", "agli", "age", "forward", "skip"],
    "previous": ["previous", "pichli", "back", "peeche"],
    "open": ["open", "kholo", "go to", "show", "le chalo"],
    "create": ["create", "banao", "new"],
    "save": ["save", "mehfooz", "store"],
    "bookmark": ["bookmark", "nishan"],
    "unmark": ["unmark", "remove bookmark", "nishan hatao"],
    "read": ["read", "parho", "text"]
}

TARGETS = {
    "quran": ["quran", "mushaf"],
    "bayan": ["bayan", "bayanat", "lecture"],
    "home": ["home", "main screen", "ghar"],
    "back": ["back", "wapis"],
    "chain": ["chain", "playlist"]
}