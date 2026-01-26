from fastapi import APIRouter
from database import get_connection
from schemas.bookmarks_schema.bayan_schema import BayanBookmarkCreate

router=APIRouter()

@router.post("/AddbayanBookmark")
def bayanBookmark(bayan:BayanBookmarkCreate):
    conn=get_connection()
    if conn is None:
        return{"message":"connection build fail"}
    cursor=conn.cursor()

    bid=bayan.bayanid
    pid=bayan.profileid

    query="select *from BookmarkBayan where profileID=? and BayanID=?"
    cursor.execute(query,(pid,bid))
    found=cursor.fetchone()
    if found:
        return{"message":"already Bookmarked this bayan"}
    
    query="insert into BookmarkBayan(bookmarkID,profileID,BayanID) values(?,?,?)"
    markid=str(pid)+str(bid)
    cursor.execute(query,(markid,pid,bid))
    conn.commit()

    return{"message":"Bookmarked succcess"}