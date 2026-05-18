# routers/History/last_played_route.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from database import get_connection
from schemas.play_history_schema import LastPlayedItemsResponse, PlayHistoryItem

router = APIRouter()

@router.get("/last_played/{profileId}", response_model=LastPlayedItemsResponse)
def last_played_items(
    profileId: int,
    limit: int = 4,
    content_type: Optional[str] = Query(None, pattern="^(surah|bayan|chain)$")
):
    """
    Get last N played items for a user.
    - If content_type is provided, returns only that type
    - Otherwise returns mixed items
    
    UPDATED: Now uses simple ORDER BY played_at DESC
    (play_count column removed)
    """
    # Validate limit
    if limit <= 0:
        limit = 4

    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        
        # ============================================================
        # UPDATED: Simple query - no play_count needed
        # ORDER BY played_at DESC gives most recent first
        # ============================================================
        query = """
            SELECT TOP (?)
                id, 
                profileId, 
                content_type, 
                content_id, 
                range_start, 
                range_end,
                current_position, 
                played_at,
                voice_mode,
                completed,
                duration_seconds
            FROM user_play_history
            WHERE profileId = ?
        """
        params = [limit, profileId]
        
        # Add content_type filter only if provided
        if content_type:
            query += " AND content_type = ?"
            params.append(content_type)
        
        query += " ORDER BY played_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            item = PlayHistoryItem(
                id=row[0],
                profileId=row[1],
                content_type=row[2],
                content_id=row[3],
                range_start=row[4],
                range_end=row[5],
                current_position=row[6],
                played_at=row[7],
                voice_mode=row[8],
                completed=row[9],
                duration_seconds=row[10]
            )
            
            # Enrich with name/subtitle from respective table
            if item.content_type == "surah":
                cursor.execute("SELECT NameEnglish, NameArabic FROM surah WHERE SurahID = ?", (item.content_id,))
                surah = cursor.fetchone()
                if surah:
                    item.name = surah[0]
                    item.subtitle = surah[1]
                else:
                    item.name = f"Surah {item.content_id}"
                    item.subtitle = ""
                    
            elif item.content_type == "bayan":
                cursor.execute("SELECT Title FROM Bayan WHERE BayanID = ?", (item.content_id,))
                bayan = cursor.fetchone()
                if bayan:
                    item.name = bayan[0]
                    item.subtitle = "Dr. Israr Ahmed"
                else:
                    item.name = f"Bayan {item.content_id}"
                    item.subtitle = "Dr. Israr Ahmed"
                    
            elif item.content_type == "chain":
                cursor.execute("SELECT title FROM chain WHERE ChainID = ?", (item.content_id,))
                chain = cursor.fetchone()
                if chain:
                    item.name = chain[0]
                    item.subtitle = "Chain"
                else:
                    item.name = f"Chain {item.content_id}"
                    item.subtitle = ""
            
            items.append(item)
        
        return {"status": "success", "items": items}
        
    except Exception as e:
        print(f"Error in last_played_items: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()