from fastapi import APIRouter
from database import get_connection

router = APIRouter()

@router.post("/getSurahbookmarks/{profile_id}")
def get_bookmarks(profile_id: int):
    conn = get_connection()
    if conn is None:
        return {"message": "Connection build failed"}

    cursor = conn.cursor()
    
    # 🆕 Added 'ba.title' in select
    query = """
    SELECT 
        s.namearabic,
        s.nameenglish,
        s.totalayats,
        ba.startayat,
        ba.endayat,
        ba.title           -- 👈 TITLE COLUMN ADDED
    FROM bookmarkAudio ba 
    JOIN surah s ON s.surahid = ba.surahid 
    WHERE ba.profileid = ?
    """
    cursor.execute(query, (profile_id,))
    results = cursor.fetchall()
    
    # Also get bookmarkId for delete functionality
    query_with_id = """
    SELECT 
        ba.bookmarkId,
        s.namearabic,
        s.nameenglish,
        s.totalayats,
        ba.startayat,
        ba.endayat,
        ba.title
    FROM bookmarkAudio ba 
    JOIN surah s ON s.surahid = ba.surahid 
    WHERE ba.profileid = ?
    ORDER BY ba.bookmarkId DESC
    """
    cursor.execute(query_with_id, (profile_id,))
    rows = cursor.fetchall()

    bookmarks = []
    for row in rows:
        bookmarks.append({
            "bookmarkId": row[0],
            "NameArabic": row[1],
            "NameEnglish": row[2],
            "TotalAyats": row[3],
            "FromAyat": row[4],
            "ToAyat": row[5],
            "title": row[6] if row[6] else f"{row[2]} - Ayat {row[4]}"  # 👈 Default title if null
        })

    return {"bookmarks": bookmarks}