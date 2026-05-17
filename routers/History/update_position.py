# routers/update_position_route.py
from fastapi import APIRouter, HTTPException
from database import get_connection
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

class UpdatePositionSchema(BaseModel):
    profileId: int
    content_type: str           # 'surah', 'bayan', 'chain'
    content_id: int
    current_position: int       # For surah/chain: ayat index, For bayan: seconds
    range_start: Optional[int] = 1
    range_end: Optional[int] = None

@router.put("/updatePlayPosition")
def update_play_position(data: UpdatePositionSchema):
    """
    UPDATE existing play record's current_position
    Works for: Surah, Chain, Bayan (ALL content types)
    
    Called when:
    - User seeks to different position
    - Periodic auto-save (every 5 seconds)
    - User pauses playback
    - App unmounts/closes
    - Ayat changes (for surah/chain)
    
    This enables cross-device resume functionality.
    """
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        # Get the latest (most recent) play record for this content
        # That is NOT completed (still in progress)
        get_latest_query = """
            SELECT TOP 1 id 
            FROM user_play_history
            WHERE profileId = ? 
              AND content_type = ? 
              AND content_id = ?
              AND completed = 0
            ORDER BY played_at DESC
        """
        cursor.execute(get_latest_query, (data.profileId, data.content_type, data.content_id))
        row = cursor.fetchone()

        if not row:
            # If no active record found, try to get any record (even completed)
            get_any_query = """
                SELECT TOP 1 id 
                FROM user_play_history
                WHERE profileId = ? 
                  AND content_type = ? 
                  AND content_id = ?
                ORDER BY played_at DESC
            """
            cursor.execute(get_any_query, (data.profileId, data.content_type, data.content_id))
            row = cursor.fetchone()
            
            if not row:
                return {
                    "status": "error", 
                    "message": "No play record found to update. Please play content first."
                }

        record_id = row[0]

        # Update the position and last_updated timestamp
        update_query = """
            UPDATE user_play_history
            SET current_position = ?,
                last_updated = GETDATE()
            WHERE id = ?
        """
        cursor.execute(update_query, (data.current_position, record_id))
        conn.commit()

        print(f"✅ Updated position: {data.content_type} {data.content_id} -> position {data.current_position}")

        return {
            "status": "success", 
            "message": "Position updated",
            "record_id": record_id,
            "position": data.current_position
        }

    except Exception as e:
        print(f"Error in update_play_position: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()