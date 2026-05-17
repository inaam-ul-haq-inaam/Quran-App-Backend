# routers/play_history_route.py
from fastapi import APIRouter
from database import get_connection
from schemas.play_history_schema import TrackPlaySchema

router = APIRouter()

@router.post("/trackPlay")
def track_play(data: TrackPlaySchema):
    conn = get_connection()
    if conn is None:
        return {"status": "error", "message": "Database connection failed"}

    try:
        cursor = conn.cursor()

        # ============================================================
        # SIMPLE INSERT ONLY - Har play ki nayi entry
        # Koi check nahi, koi update nahi, koi increment nahi
        # ============================================================
        insert_query = """
            INSERT INTO user_play_history (
                profileId, 
                content_type, 
                content_id, 
                range_start, 
                range_end, 
                current_position,
                voice_mode,
                completed,
                duration_seconds
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, (
            data.profileId,
            data.content_type,
            data.content_id,
            data.range_start or 1,
            data.range_end,
            data.current_position or 0,
            data.voice_mode or 0,
            data.completed or 0,
            data.duration_seconds or 0
        ))

        conn.commit()
        return {"status": "success", "message": "Play record saved"}

    except Exception as e:
        print(f"Error in track_play: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()