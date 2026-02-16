from thefuzz import process, fuzz

SURAH_DB = {
    # 1–10
    "fatiha": 1, "al fatiha": 1,
    "baqarah": 2, "baqara": 2, "bakra": 2,
    "aal imran": 3, "imran": 3,
    "nisa": 4, "an nisa": 4, "neesa": 4,
    "maidah": 5, "maida": 5,
    "anam": 6, "anaam": 6,
    "araf": 7, "aaraf": 7,
    "anfal": 8, "anfaal": 8,
    "tawbah": 9, "tawba": 9, "tauba": 9,
    "yunus": 10, "younus": 10,

    # 11–20
    "hud": 11, "hood": 11,
    "yusuf": 12, "yousuf": 12, "joseph": 12,
    "rad": 13, "raad": 13,
    "ibrahim": 14, "ibraheem": 14,
    "hijr": 15,
    "nahl": 16,
    "isra": 17, "bani israel": 17,
    "kahf": 18,
    "maryam": 19, "mariyam": 19,
    "taha": 20, "ta ha": 20,

    # 21–30
    "anbiya": 21, "ambiya": 21,
    "hajj": 22, "haj": 22,
    "muminun": 23, "mominoon": 23,
    "nur": 24, "noor": 24,
    "furqan": 25,
    "shuara": 26,
    "naml": 27,
    "qasas": 28, "kasas": 28,
    "ankabut": 29, "ankaboot": 29, "spider": 29,
    "rum": 30, "room": 30, "rome": 30,

    # 31–40
    "luqman": 31, "lukman": 31,
    "sajdah": 32, "sajda": 32,
    "ahzab": 33,
    "saba": 34,
    "fatir": 35,
    "yasin": 36, "yaseen": 36,
    "saffat": 37,
    "sad": 38, "saad": 38,
    "zumar": 39,
    "ghafir": 40, "mumin": 40,

    # 41–50
    "fussilat": 41, "hamim sajdah": 41,
    "ash shura": 42, "shuraa": 42,
    "zukhruf": 43,
    "dukhan": 44,
    "jathiyah": 45,
    "ahqaf": 46,
    "muhammad": 47,
    "fath": 48,
    "hujurat": 49,
    "qaf": 50, "qaaf": 50,

    # 51–60
    "dhariyat": 51, "zariyat": 51,
    "tur": 52, "toor": 52,
    "najm": 53,
    "qamar": 54,
    "rahman": 55, "rehman": 55,
    "waqiah": 56, "waqia": 56,
    "hadid": 57, "hadeed": 57,
    "mujadilah": 58,
    "hashr": 59,
    "mumtahanah": 60,

    # 61–70
    "saff": 61,
    "jumuah": 62, "jumma": 62,
    "munafiqun": 63,
    "taghabun": 64,
    "talaq": 65,
    "tahrim": 66,
    "mulk": 67,
    "qalam": 68,
    "haqqah": 69,
    "maarij": 70,

    # 71–80
    "nuh": 71, "nooh": 71,
    "jinn": 72,
    "muzzammil": 73,
    "muddathir": 74,
    "qiyamah": 75,
    "insan": 76, "dahr": 76,
    "mursalat": 77,
    "naba": 78,
    "naziat": 79,
    "abasa": 80,

    # 81–90
    "takwir": 81,
    "infitar": 82,
    "mutaffifin": 83,
    "inshiqaq": 84,
    "buruj": 85,
    "tariq": 86,
    "ala": 87, "aala": 87,
    "ghashiyah": 88,
    "fajr": 89,
    "balad": 90,

    # 91–100
    "shams": 91,
    "layl": 92, "lail": 92,
    "duha": 93, "wadduha": 93,
    "sharh": 94, "inshirah": 94,
    "tin": 95, "teen": 95,
    "alaq": 96,
    "qadr": 97,
    "bayyinah": 98,
    "zalzalah": 99,
    "adiyat": 100,

    # 101–114
    "qariah": 101,
    "takathur": 102,
    "asr": 103,
    "humazah": 104,
    "fil": 105, "elephant": 105,
    "quraysh": 106, "quraish": 106,
    "maun": 107,
    "kawthar": 108, "kausar": 108,
    "kafirun": 109,
    "nasr": 110,
    "masad": 111, "lahab": 111,
    "ikhlas": 112, "ahad": 112,
    "falaq": 113,
    "nas": 114, "naas": 114
}

RECITER_DB = {
    "afasy": 1,
    "al afasy": 1,
    "mishary": 1,
    "mishari": 1,
    "mishary al afasy": 1
}

def find_surah_id(text: str):

    if not text:
        return None

    text = text.lower().strip()

    # 1️⃣ Exact full match (fastest)
    if text in SURAH_DB:
        print(f"📖 Exact Surah Match: {text}")
        return SURAH_DB[text]

    words = text.split()

    # 2️⃣ Direct word match
    for word in words:
        if word in SURAH_DB:
            print(f"📖 Direct Word Match: {word}")
            return SURAH_DB[word]

    # 3️⃣ Multi-word match check (like 'al fatiha')
    for key in SURAH_DB.keys():
        if key in text:
            print(f"📖 Phrase Match: {key}")
            return SURAH_DB[key]

    # 4️⃣ Fuzzy fallback (safer scorer)
    best_match, score = process.extractOne(
        text,
        SURAH_DB.keys(),
        scorer=fuzz.token_set_ratio
    )

    if score >= 70:
        print(f"📖 Fuzzy Surah Detect: '{best_match}' Score: {score}%")
        return SURAH_DB[best_match]

    return None


def find_reciter_id(text: str):

    if not text:
        return None

    text = text.lower().strip()

    # Exact match
    if text in RECITER_DB:
        return RECITER_DB[text]

    # Phrase match
    for key in RECITER_DB.keys():
        if key in text:
            return RECITER_DB[key]

    # Fuzzy fallback
    best_match, score = process.extractOne(
        text,
        RECITER_DB.keys(),
        scorer=fuzz.token_set_ratio
    )

    if score >= 85:
        print(f"🎤 Fuzzy Reciter Detect: '{best_match}' Score: {score}%")
        return RECITER_DB[best_match]

    return None
