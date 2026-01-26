from fastapi import APIRouter
from database import get_connection

router = APIRouter()

@router.post("/getBayanBookmarks/{profile_id}")
def get_bookmarks(profile_id: int):
    conn = get_connection()
    if conn is None:
        return {"message": "Connection build failed"}

    cursor = conn.cursor()
    
    query = """
    SELECT b.BayanID, b.title, b.startAyatID, b.endAyatID, s.scholarID, s.name
    FROM BookmarkBayan bb
    JOIN Bayan b ON bb.BayanID = b.BayanID
    JOIN Scholar s ON b.scholarID = s.scholarID
    WHERE bb.profileID = ?
    """
    cursor.execute(query, (profile_id,))
    results = cursor.fetchall()
    
   
    bookmarks = []
    for row in results:
        bookmarks.append({
            "bayanID": row[0],
            "title": row[1],
            "startAyat": row[2],
            "endAyat": row[3],
            "scholarID": row[4],
            "scholarName": row[5]
        })

    return {"bookmarks": bookmarks}
