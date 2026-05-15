from fastapi import APIRouter
from database import get_connection
from schemas.bookmarks_schema.surahAudio_schema import addSurahBookmark
router = APIRouter()

@router.post("/surahBookmark")
def readBookmark(surah: addSurahBookmark):
    conn = get_connection()
    if conn is None:
        return {"message": "connection not build"}
    
    pid = surah.profileid
    sid = surah.surahid
    rid = surah.reciterid
    srt = surah.startayat
    end = surah.endayat
    title = getattr(surah, 'title', None)

    cursor = conn.cursor()
    
    # ============================================================
    # 1. Check if same surah + same title already exists
    # ============================================================
    if title:
        query = """SELECT * FROM bookmarkAudio 
                   WHERE profileid=? AND surahid=? AND reciterid=? 
                   AND startayat=? AND endayat=? AND title=?"""
        cursor.execute(query, (pid, sid, rid, srt, end, title))
        found = cursor.fetchone()
        
        if found:
            conn.close()
            return {"message": f"Bookmark with title '{title}' already exists", "already_exists": True}
    
    # ============================================================
    # 2. Check if same surah/ayat already bookmarked (any title)
    # ============================================================
    query = """SELECT * FROM bookmarkAudio 
               WHERE profileid=? AND surahid=? AND reciterid=? 
               AND startayat=? AND endayat=?"""
    cursor.execute(query, (pid, sid, rid, srt, end))
    found = cursor.fetchone()
    
    if found:
        existing_title = found[6] if len(found) > 6 else "Untitled"
        conn.close()
        return {
            "message": f"Surah already bookmarked as '{existing_title}'", 
            "already_exists": True,
            "existing_title": existing_title
        }
    
    # ============================================================
    # 3. Insert new bookmark
    # ============================================================
    query = """INSERT INTO bookmarkAudio (profileid, surahid, reciterid, startayat, endayat, title) 
               VALUES (?, ?, ?, ?, ?, ?)"""
    cursor.execute(query, (pid, sid, rid, srt, end, title))
    
    conn.commit()
    conn.close()

    return {"message": "Surah Bookmarked success", "title": title, "already_exists": False}