from fastapi import APIRouter
from database import get_connection
from schemas.ayat_schema import ayats
from config import BASE_IP
router = APIRouter()

BASE_AUDIO_URL = f"{BASE_IP}/audio/Al-Afasy/"

@router.post("/get_Surah_Ayats")
def get_Ayats(ayat: ayats):
    conn = get_connection()
    if conn is None:
        return {"message": "fail to build connection"}

    cursor = conn.cursor()

    # ============================================================
    # 1️⃣ GET SURAH INFO
    # ============================================================
    
    surah_query = """
        SELECT 
            s.SurahID,
            s.NameEnglish,
            s.NameArabic,
            s.TotalAyats
        FROM surah s
        WHERE s.SurahID = ?
    """
    
    cursor.execute(surah_query, (ayat.surah_ID,))
    surah_row = cursor.fetchone()
    
    if not surah_row:
        conn.close()
        return {"message": "Surah not found"}

    # ============================================================
    # 2️⃣ GET RECITER INFO
    # ============================================================
    
    reciter_id = getattr(ayat, 'reciterid', 1)
    
    reciter_query = """
        SELECT 
            ReciterID,
            Name
        FROM reciter 
        WHERE ReciterID = ?
    """
    cursor.execute(reciter_query, (reciter_id,))
    reciter_row = cursor.fetchone()
    
    reciter_name = reciter_row[1] if reciter_row else "Mishary Al-Afasy"

    # ============================================================
    # 3️⃣ GET AYATS WITH RANGE
    # ============================================================
    
    query = """
        SELECT 
            a.AyatNumber,
            a.arabicText,
            a.translationUrdu,
            a.TranslationEnglish,
            aa.AudioURL
        FROM ayat a
        JOIN ayataudio aa ON a.ayatID = aa.ayatID AND aa.reciterID = ?
        WHERE a.surahID = ?
    """

    fromAyat = ayat.fromAyat
    toAyat = ayat.toAyat

    params = [reciter_id, ayat.surah_ID]

    if fromAyat is not None and toAyat is not None:
        query += " AND a.AyatNumber BETWEEN ? AND ?"
        params.extend([fromAyat, toAyat])
    elif fromAyat is not None:
        query += " AND a.AyatNumber >= ?"
        params.append(fromAyat)
    elif toAyat is not None:
        query += " AND a.AyatNumber <= ?"
        params.append(toAyat)

    query += " ORDER BY a.AyatNumber ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return {"message": "No ayats found"}

    # ============================================================
    # 4️⃣ BUILD SIMPLE RESPONSE
    # ============================================================
    
    ayats_list = []
    for row in rows:
        ayats_list.append({
            "number": row[0],
            "arabic": row[1],
            "urdu": row[2],
            "english": row[3],
            "audio": BASE_AUDIO_URL + row[4] if row[4] else None
        })

    # Calculate range
    range_from = fromAyat if fromAyat else 1
    range_to = toAyat if toAyat else surah_row[3]

    # ============================================================
    # 5️⃣ SUPER SIMPLE RESPONSE (Flat structure)
    # ============================================================
    
    return {
        "status": "success",
        "surah_id": surah_row[0],
        "surah_name": surah_row[1],
        "surah_name_arabic": surah_row[2],
        "surah_total_ayats": surah_row[3],
        "reciter_id": reciter_id,
        "reciter_name": reciter_name,
        "range_from": range_from,
        "range_to": range_to,
        "total_ayats_in_range": len(rows),
        "ayats": ayats_list
    }