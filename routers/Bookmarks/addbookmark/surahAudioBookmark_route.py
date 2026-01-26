from fastapi import APIRouter
from database import get_connection
from schemas.bookmarks_schema.surahAudio_schema import addSurahBookmark
router=APIRouter()

@router.post("/surahBookmark")
def readBookmark(surah:addSurahBookmark):
    conn=get_connection()
    if conn is None:
        return{"message":"connection not build "}
    pid=surah.profileid
    sid=surah.surahid
    rid=surah.reciterid
    srt=surah.startayat
    end=surah.endayat

    cursor=conn.cursor()
    query="select *from bookmarkAudio where profileid=? and surahid=? and reciterid=? and startayat=? and endayat=?"
    cursor.execute(query,(pid,sid,rid,srt,end))
    found=cursor.fetchone()
    
    if found:
        return{"message":"Surah already Bookmarked"}
    
    query="insert into bookmarkAudio (profileid,surahid,reciterid,startayat,endayat)values(?,?,?,?,?)"
    # markid=str(pid)+str(sid)+str(rid)
    cursor.execute(query,(pid,sid,rid,srt,end))
    conn.commit()

    return{"message":"Surah Bookmarked succcess"}
