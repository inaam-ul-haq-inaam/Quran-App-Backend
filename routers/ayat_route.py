from fastapi import APIRouter
from database import get_connection
from schemas.ayat_schema import ayats

router = APIRouter()

# 🔹 BASE URL of your audio folder (Change this to your server IP)
BASE_AUDIO_URL = "http://192.168.30.150:8000/audio/Al-Afasy/"

@router.post("/get_Surah_Ayats")
def get_Ayats(ayat: ayats):
    conn = get_connection()
    if conn is None:
        return {"message": "fail to build connection"}

    cursor = conn.cursor()

    # 🔹 Query to fetch ayats with audio
    query = """
    SELECT 
        a.ayatID,
        a.surahID,
        a.AyatNumber,
        a.arabicText,
        a.translationUrdu,
        a.TranslationEnglish,
        r.Name,
        aa.AudioURL
    FROM ayat a
    JOIN ayataudio aa ON a.ayatID = aa.ayatID
    JOIN reciter r ON aa.reciterID = r.reciterID
    WHERE a.surahID = ?
    """

    surah_ID = ayat.surah_ID
    fromAyat = ayat.fromAyat
    toAyat = ayat.toAyat

    params = [surah_ID]

    # 🔹 Optional filters
    if fromAyat is not None and toAyat is not None:
        query += " AND a.AyatNumber BETWEEN ? AND ?"
        params.extend([fromAyat, toAyat])
    elif fromAyat is not None:
        query += " AND a.AyatNumber >= ?"
        params.append(fromAyat)
    elif toAyat is not None:
        query += " AND a.AyatNumber <= ?"
        params.append(toAyat)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows:
        return {"message": "No ayats found"}

    # 🔹 Build result with full audio URL
    result = []
    for row in rows:
        result.append({
            "ArabicText": row[3],
            "urduText": row[4],
            "englishText": row[5],
            "reciterName": row[6],
            "audio": BASE_AUDIO_URL + row[7]   # 👈 full URL
        })

    conn.close()

    return {
        "message": "Ayats fetched successfully",
        "data": result
    }
