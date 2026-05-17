# routers/resume_position_route.py
from fastapi import APIRouter, HTTPException
from database import get_connection
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ResumePositionResponse(BaseModel):
    status: str
    position: int
    range_start: int
    range_end: Optional[int] = None
    completed: Optional[int] = 0
    played_at: Optional[str] = None

@router.get("/resume/{profileId}/{content_type}/{content_id}", response_model=ResumePositionResponse)
def get_resume_position(
    profileId: int,
    content_type: str,
    content_id: int,
    range_start: int = 1,
    range_end: int = None
):
    """
    Get the last saved position for resume functionality.
    Works for: Surah, Chain, Bayan (ALL content types)
    
    Returns the MOST RECENT position from play history
    (only from active/in-progress records, not completed ones)
    
    Example: /resume/1/surah/2?range_start=1&range_end=7
    """
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        # First try to get active (not completed) record
        query = """
            SELECT TOP 1 
                current_position, 
                range_start, 
                range_end,
                completed,
                played_at
            FROM user_play_history
            WHERE profileId = ?
              AND content_type = ?
              AND content_id = ?
              AND completed = 0
              AND range_start = ?
              AND (range_end = ? OR (range_end IS NULL AND ? IS NULL))
            ORDER BY played_at DESC
        """
        
        cursor.execute(query, (profileId, content_type, content_id, range_start, range_end, range_end))
        row = cursor.fetchone()

        if not row:
            # If no active record, get the most recent (even completed)
            query_all = """
                SELECT TOP 1 
                    current_position, 
                    range_start, 
                    range_end,
                    completed,
                    played_at
                FROM user_play_history
                WHERE profileId = ?
                  AND content_type = ?
                  AND content_id = ?
                  AND range_start = ?
                  AND (range_end = ? OR (range_end IS NULL AND ? IS NULL))
                ORDER BY played_at DESC
            """
            cursor.execute(query_all, (profileId, content_type, content_id, range_start, range_end, range_end))
            row = cursor.fetchone()

        if row:
            position = row[0]
            stored_start = row[1]
            stored_end = row[2]
            completed = row[3]
            played_at = str(row[4]) if row[4] else None
            
            print(f"📖 Resume found: {content_type} {content_id} - position: {position} (completed: {completed})")
        else:
            # No history – start from beginning
            position = 0
            stored_start = range_start
            stored_end = range_end
            completed = 0
            played_at = None
            print(f"📖 No resume found for {content_type} {content_id} - starting from beginning")

        return {
            "status": "success",
            "position": position,
            "range_start": stored_start,
            "range_end": stored_end,
            "completed": completed,
            "played_at": played_at
        }

    except Exception as e:
        print(f"Error in resume_position: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()