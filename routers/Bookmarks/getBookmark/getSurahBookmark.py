from fastapi import APIRouter
from database import get_connection

router = APIRouter()

@router.post("/getSurahbookmarks/{profile_id}")
def get_bookmarks(profile_id: int):
    conn = get_connection()
    if conn is None:
        return {"message": "Connection build failed"}

    cursor = conn.cursor()
    
    query = """
    select s.namearabic,s.nameenglish,s.totalayats,ba.startayat,ba.endayat from bookmarkAudio ba 
    join surah s on s.surahid=ba.surahid where ba.profileid=?
    """
    cursor.execute(query, (profile_id,))
    results = cursor.fetchall()
    

    bookmarks = []
    for row in results:
        bookmarks.append({
            "NameArabic": row[0],
            "NameEnglish": row[1],
            # "TotalAyats": row[2],
            "FromAyat":row[3],
            "To":row[4]
            
        })

    return {"bookmarks": bookmarks}
