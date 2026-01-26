from fastapi import APIRouter
from schemas import surah_schema
from database import get_connection
router=APIRouter()

@router.get("/Surah")
def surahList():
    conn=get_connection()
    if conn is None:
        return{
            "message":"Connection not build"
        }
    cursor=conn.cursor()

    query="select *from surah"
    cursor.execute(query)

    rows=cursor.fetchall()
    
    list=[]

    for row in rows:
        list.append({
            "surahNumber":row[1],
            "NameArabic":row[2],
            "NameEnglish":row[3],
            "TotalAyat":row[4]
        })
    return{
            "message":"surah list fetch success",
            "list":list
        }