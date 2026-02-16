from fastapi import APIRouter
from database import get_connection
from schemas.ayat_schema import ayats

router = APIRouter()

# 🔹 BASE URL of your audio folder
BASE_AUDIO_URL = "http://192.168.18.123:8000/audio/Al-Afasy/"

@router.post("/get_Surah_Ayats")
def get_Ayats(ayat: ayats):
    conn = get_connection()
    if conn is None:
        return {"message": "fail to build connection"}

    cursor = conn.cursor()

    
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
        s.NameEnglish  
    FROM ayat a
    JOIN ayataudio aa ON a.ayatID = aa.ayatID
    JOIN reciter r ON aa.reciterID = r.reciterID
    JOIN surah s ON a.surahID = s.surahID  
    WHERE a.surahID = ?
    """

    surah_ID = ayat.surah_ID
    fromAyat = ayat.fromAyat
    toAyat = ayat.toAyat

    params = [surah_ID]

   
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

   
    result = []
   
    main_surah_name = rows[0][8] 

    for row in rows:
        result.append({
            "AyatNumber": row[2],
            "ArabicText": row[3],
            "urduText": row[4],
            "englishText": row[5],
            "reciterName": row[6],
            "audio": BASE_AUDIO_URL + row[7],
            "NameEnglish": row[8] 
        })

    conn.close()

    return {
        "message": "Ayats fetched successfully",
        "surahName": main_surah_name, 
        "data": result
    }