from fastapi import APIRouter
from database import get_connection
from schemas import bayan_schema
router=APIRouter()

@router.get("/AllBayan")
def get_AllBayan():
    conn=get_connection()

    if conn is None:
        return{"message":"conection not built"}
    cursor=conn.cursor()
    list=[]
    query="""SELECT 
            b.BayanID,
            b.Title,
            b.AudioURL,
            b.Duration,
            s.Name,
            su.NameArabic,
            b.StartAyatID,
            b.EndAyatID
        FROM Bayan b
        LEFT JOIN Scholar s ON b.ScholarID = s.ScholarID
        LEFT JOIN Surah su ON b.SurahID = su.SurahID"""
    
    cursor.execute(query)
    rows=cursor.fetchall()

    for row in rows:
        list.append({
            "BayanID":row[0],
            "Title":row[1],
            "AudioUrl":row[2],
            "Duration":row[3],
            "ScholorName":row[4],
            "SurahName":row[5],
            "StartAyatID":row[6],
             "EndAyatID":row[7]
        })
    return{
        "message":"List of All Bayan",
        "Bayans":list
    }    
