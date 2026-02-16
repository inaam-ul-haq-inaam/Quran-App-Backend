
WHISPER_PROMPT = (
    "quran, mushaf, surah, ayat, reciter, qari, mishary, sudais, "
    "play, chalao, sunao, start, resume, pause, ruko, stop, "
    "next, agli, forward, previous, pichli, back, "
    "open, kholo, go to, read, parho, "
    "bookmark, nishan, unmark, remove bookmark, "
    "save, mehfooz, store, "
    "bayan, lecture, "
    "chain, playlist, create, banao, new"
)


COMMANDS = {
    "play": ["play", "chalao", "sunao", "laga", "start", "resume", "continue"],
    "pause": ["pause", "ruko", "stop", "band", "wait", "hold"],
    "next": ["next", "agli", "age", "forward", "skip", "aagay"],
    "previous": ["previous", "pichli", "back", "peeche", "pichay"],
    "open": ["open", "kholo", "go to", "show", "le chalo", "dikhao"],
    "create": ["create", "banao", "new", "bana do"],
    "save": ["save", "mehfooz", "store", "save karo"],
    "bookmark": ["bookmark", "nishan", "mark"],
    "unmark": ["unmark", "remove bookmark", "nishan hatao", "delete mark"],
    "read": ["read", "parho", "tilawat", "text"]
}


TARGETS = {
    "quran": ["quran", "mushaf"],
    "bayan": ["bayan", "bayanat", "lecture"],
    "home": ["home", "main screen", "ghar"],
    "back": ["back", "wapis"],
    "chain": ["chain", "playlist"]
}