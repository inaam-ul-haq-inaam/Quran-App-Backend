from fastapi import APIRouter
from database import get_connection
from config import BASE_IP

router = APIRouter()

# Wahi BASE_URL jo aapke working code mein hai
BASE_AUDIO_URL = f"{BASE_IP}/audio/Al-Afasy/"

@router.get("/getChainDetails/{chainId}")
def get_chain_details(chainId: int):
    conn = get_connection()
    if conn is None:
        return {"message": "fail to build connection"}

    try:
        cursor = conn.cursor()

        # 1. Screenshot ke mutabiq exact Table aur Column names
        # Table: ChainDetail, Columns: SurahID, ChainID, StartAyat, EndAyat, playOrder
        query = """
            SELECT 
                cd.SurahID, 
                s.NameEnglish, 
                cd.StartAyat, 
                cd.EndAyat, 
                c.ReciterID
            FROM dbo.ChainDetail cd
            JOIN dbo.Chain c ON cd.ChainID = c.ChainID
            JOIN dbo.Surah s ON cd.SurahID = s.SurahID
            WHERE cd.ChainID = ?
            ORDER BY cd.playOrder ASC
        """
        cursor.execute(query, (chainId,))
        rows = cursor.fetchall()

        if not rows:
            return {"message": "No details found for this chain", "data": []}

        playlist = []

        # 2. Range ko expand karne ki logic
        for row in rows:
            # row indexing: 0:SurahID, 1:NameEnglish, 2:StartAyat, 3:EndAyat, 4:ReciterID
            s_id, s_name, start, end, r_id = row
            
            # Ayat range ka loop
            for ayat_num in range(start, end + 1):
                
                # 3. Ayat ka data mangwayein (Wahi names jo aapke working code mein hain)
                ayat_query = """
                    SELECT 
                        a.arabicText, 
                        a.translationUrdu, 
                        aa.AudioURL 
                    FROM ayat a
                    LEFT JOIN ayataudio aa ON a.ayatID = aa.ayatID AND aa.reciterID = ?
                    WHERE a.surahID = ? AND a.AyatNumber = ?
                """
                cursor.execute(ayat_query, (r_id, s_id, ayat_num))
                res = cursor.fetchone()

                if res:
                    playlist.append({
                        "surahId": s_id,
                        "surahName": s_name,
                        "ayatNumber": ayat_num,
                        "ArabicText": res[0],
                        "urduText": res[1],
                        "audio": BASE_AUDIO_URL + res[2] 
                    })

        return {
            "message": "Chain details fetched successfully",
            "data": playlist
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"message": "Internal Server Error", "error": str(e)}
    finally:
        conn.close()