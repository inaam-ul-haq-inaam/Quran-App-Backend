from fastapi import APIRouter
from database import get_connection
from schemas.ayat_schema import ayats

router = APIRouter()

# 🔹 BASE URL of your audio folder
BASE_AUDIO_URL = "http://10.194.143.234:8000/audio/Al-Afasy/"

@router.post("/get_Surah_Ayats")
def get_Ayats(ayat: ayats):
    conn = get_connection()
    if conn is None:
        return {"message": "fail to build connection"}

    cursor = conn.cursor()

    # 🔹 UPDATED QUERY: Added JOIN with 'surah' table to get the name
    query = """
    SELECT 
        a.ayatID,
        a.surahID,
        a.AyatNumber,
        a.arabicText,
        a.translationUrdu,
        a.TranslationEnglish,
        r.Name as reciterName,
        aa.AudioURL,
        s.NameEnglish  -- 👈 Farz karein column ka naam 'surahName' hai
    FROM ayat a
    JOIN ayataudio aa ON a.ayatID = aa.ayatID
    JOIN reciter r ON aa.reciterID = r.reciterID
    JOIN surah s ON a.surahID = s.surahID  -- 👈 Surah table join kiya
    WHERE a.surahID = ?
    """

    surah_ID = ayat.surah_ID
    fromAyat = ayat.fromAyat
    toAyat = ayat.toAyat

    params = [surah_ID]

    # 🔹 Optional filters logic
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
        conn.close()
        return {"message": "No ayats found"}

    # 🔹 Result build karein
    result = []
    # Pehli row se Surah ka naam utha lein taake main response mein bhej saken
    main_surah_name = rows[0][8] 

    for row in rows:
        result.append({
            "AyatNumber": row[2],
            "ArabicText": row[3],
            "urduText": row[4],
            "englishText": row[5],
            "reciterName": row[6],
            "audio": BASE_AUDIO_URL + row[7],
            "NameEnglish": row[8]  # 👈 Har ayat ke data mein bhi naam maujood hai
        })

    conn.close()

    return {
        "message": "Ayats fetched successfully",
        "surahName": main_surah_name,  # 👈 Frontend ke liye asaan access
        "data": result
    }