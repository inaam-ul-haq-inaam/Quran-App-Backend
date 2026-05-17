# routers/History/most_played_route.py
from fastapi import APIRouter, HTTPException, Query
from database import get_connection
from schemas.play_history_schema import MostPlayedResponse

router = APIRouter()

@router.get("/most_played/{profileId}", response_model=MostPlayedResponse)
def most_played(
    profileId: int,
    content_type: str = Query("surah", pattern="^(surah|bayan|chain)$")
):
    """
    Get the most played item for a given content type.
    Example: /most_played/1?content_type=surah
    
    UPDATED: Now uses COUNT(*) instead of play_count column
    """
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        # ============================================================
        # UPDATED: Use COUNT(*) to get play frequency
        # Table has multiple entries per content, so we COUNT them
        # ============================================================
        query = """
            SELECT TOP 1 
                content_id, 
                COUNT(*) as play_count
            FROM user_play_history
            WHERE profileId = ? AND content_type = ?
            GROUP BY content_id
            ORDER BY play_count DESC
        """
        cursor.execute(query, (profileId, content_type))
        row = cursor.fetchone()

        if not row:
            # No history for this type – return a fallback response
            return {
                "status": "success",
                "content_id": 0,
                "play_count": 0,
                "name": f"No {content_type} played yet",
                "subtitle": ""
            }

        content_id = row[0]
        play_count = row[1]
        name = ""
        subtitle = ""

        # Fetch name/subtitle from the respective table
        if content_type == "surah":
            cursor.execute("SELECT NameEnglish, NameArabic FROM surah WHERE SurahID = ?", (content_id,))
            surah = cursor.fetchone()
            if surah:
                name = surah[0]
                subtitle = surah[1]
            else:
                name = f"Surah {content_id}"
                subtitle = ""
                
        elif content_type == "bayan":
            cursor.execute("SELECT Title, ScholarName FROM Bayan WHERE BayanID = ?", (content_id,))
            bayan = cursor.fetchone()
            if bayan:
                name = bayan[0]
                subtitle = bayan[1] if bayan[1] else "Bayan"
            else:
                name = f"Bayan {content_id}"
                subtitle = ""
                
        elif content_type == "chain":
            cursor.execute("SELECT title FROM chain WHERE ChainID = ?", (content_id,))
            chain = cursor.fetchone()
            if chain:
                name = chain[0]
                subtitle = "Chain"
            else:
                name = f"Chain {content_id}"
                subtitle = ""

        return {
            "status": "success",
            "content_id": content_id,
            "play_count": play_count,
            "name": name,
            "subtitle": subtitle
        }

    except Exception as e:
        print(f"Error in most_played: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()