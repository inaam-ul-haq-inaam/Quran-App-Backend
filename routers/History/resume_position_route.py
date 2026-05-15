# routers/resume_position_route.py
from fastapi import APIRouter, HTTPException
from database import get_connection
from schemas.play_history_schema import ResumePositionResponse

router = APIRouter()

@router.get("/resume/{profileId}/{content_type}/{content_id}", response_model=ResumePositionResponse)
def get_resume_position(
    profileId: int,
    content_type: str,
    content_id: int,
    range_start: int = 1,
    range_end: int = None
):
    """
    Get the last saved position for a specific item.
    If range_end is not provided, it will match NULL range_end (full surah/whole bayan).
    Example: /api/play-history/resume/1/surah/1?range_start=1&range_end=7
    """
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        # Query for the specific record (unique constraint)
        query = """
            SELECT current_position, range_start, range_end
            FROM user_play_history
            WHERE profileId = ?
              AND content_type = ?
              AND content_id = ?
              AND range_start = ?
              AND (range_end = ? OR (range_end IS NULL AND ? IS NULL))
        """
        cursor.execute(query, (profileId, content_type, content_id, range_start, range_end, range_end))
        row = cursor.fetchone()

        if row:
            position = row[0]
            stored_start = row[1]
            stored_end = row[2]
        else:
            # No history – start from beginning
            position = 0
            stored_start = range_start
            stored_end = range_end

        return {
            "status": "success",
            "position": position,
            "range_start": stored_start,
            "range_end": stored_end
        }

    except Exception as e:
        print(f"Error in resume_position: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()