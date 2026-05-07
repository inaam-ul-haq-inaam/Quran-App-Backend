from fastapi import APIRouter
from database import get_connection
from config import BASE_IP
from urllib.parse import unquote

router = APIRouter()
BASE_AUDIO_URL = f"{BASE_IP}/audio/Al-Afasy/"

# ============================================================
# EXISTING ENDPOINT (by ID) - Already hai tumhare paas
# ============================================================
@router.get("/getChainDetails/{chainId}")
def get_chain_details(chainId: int):
    # ... tumhara existing code ...
    pass

# ============================================================
# 🆕 NEW ENDPOINT (by Name) - YEH ADD KARO
# ============================================================
@router.get("/getChainByName/{chainName}")
def get_chain_by_name(chainName: str):
    conn = get_connection()
    if conn is None:
        return {"message": "fail to build connection", "data": []}

    try:
        cursor = conn.cursor()
        
        # Decode URL encoded string
        decoded_name = unquote(chainName).strip()
        print(f"🔍 Searching chain by name: '{decoded_name}'")
        
        # Search by title (exact match, case insensitive)
        name_query = """
            SELECT TOP 1 ChainID 
            FROM dbo.Chain 
            WHERE LOWER(title) = LOWER(?)
        """
        cursor.execute(name_query, (decoded_name,))
        row = cursor.fetchone()
        
        # If not found, try partial match
        if not row:
            name_query = """
                SELECT TOP 1 ChainID 
                FROM dbo.Chain 
                WHERE LOWER(title) LIKE ?
            """
            cursor.execute(name_query, (f"%{decoded_name.lower()}%",))
            row = cursor.fetchone()
        
        if not row:
            print(f"❌ No chain found with name: '{decoded_name}'")
            return {"message": "Chain not found", "data": []}
        
        chain_id = row[0]
        print(f"✅ Found chain ID: {chain_id} for name: '{decoded_name}'")
        
        # Fetch chain details (same as existing logic)
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
        cursor.execute(query, (chain_id,))
        rows = cursor.fetchall()

        if not rows:
            return {"message": "No details found for this chain", "data": []}

        playlist = []

        for row in rows:
            s_id, s_name, start, end, r_id = row
            
            for ayat_num in range(start, end + 1):
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
                        "audio": BASE_AUDIO_URL + res[2] if res[2] else None
                    })

        return {
            "message": "Chain details fetched successfully",
            "data": playlist
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"message": "Internal Server Error", "error": str(e), "data": []}
    finally:
        conn.close()