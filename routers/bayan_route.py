from fastapi import APIRouter
from database import get_connection
from schemas import bayan_schema
from config import BASE_IP
router=APIRouter()

@router.get("/AllBayan")
def get_AllBayan():
    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built"}
    
    try:
        cursor = conn.cursor()
        # Humne query wahi rakhi hai jo aapne likhi
        query = """SELECT 
                    b.BayanID, b.Title, b.AudioURL, b.Duration, 
                    s.Name, su.NameEnglish, b.StartAyatID, b.EndAyatID
                FROM Bayan b
                LEFT JOIN Scholar s ON b.ScholarID = s.ScholarID
                LEFT JOIN Surah su ON b.SurahID = su.SurahID"""
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        bayan_list = []
        
        base_audio_url = f"{BASE_IP}/audio/Dr_Israr/" 

        for row in rows:
            bayan_list.append({
                "BayanID": row[0],
                "Title": row[1],
                "AudioUrl": f"{base_audio_url}{row[2]}", 
                "Duration": row[3],
                "ScholarName": row[4], 
                "SurahName": row[5],
                "StartAyatID": row[6],
                "EndAyatID": row[7]
            })
        
        return {
            "message": "List of All Bayans",
            "Bayans": bayan_list
        }
    
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        # Ye sabse zaroori hai: Connection hamesha band karein
        conn.close()




@router.get("/BayanBySurah/{surah_id}")
def get_Bayan_By_Surah(surah_id: int):
    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built"}
    
    try:
        cursor = conn.cursor()
        
        # 🛠️ NAYI QUERY: Yahan humne 'WHERE b.SurahID = ?' lagaya hai
        query = """SELECT 
                    b.BayanID, b.Title, b.AudioURL, b.Duration, 
                    s.Name, su.NameEnglish, b.StartAyatID, b.EndAyatID
                FROM Bayan b
                LEFT JOIN Scholar s ON b.ScholarID = s.ScholarID
                LEFT JOIN Surah su ON b.SurahID = su.SurahID
                WHERE b.SurahID = ?"""
        
        cursor.execute(query, (surah_id,))
        rows = cursor.fetchall()
        
        bayan_list = []
        base_audio_url = f"{BASE_IP}/audio/Dr_Israr/" 

        for row in rows:
            bayan_list.append({
                "BayanID": row[0],
                "Title": row[1],
                "AudioUrl": f"{base_audio_url}{row[2]}", 
                "Duration": row[3],
                "ScholarName": row[4], 
                "SurahName": row[5],
                "StartAyatID": row[6],
                "EndAyatID": row[7]
            })
        
        return {
            "message": f"Bayans for Surah {surah_id}",
            "Bayans": bayan_list
        }
    
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        conn.close()