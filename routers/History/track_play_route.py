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

        # Check if record exists with same unique key
        check_query = """
            SELECT id, play_count FROM user_play_history
            WHERE profileId = ? AND content_type = ? AND content_id = ?
            AND (range_start = ?) AND (range_end = ? OR (range_end IS NULL AND ? IS NULL))
        """
        cursor.execute(check_query, (
            data.profileId, data.content_type, data.content_id,
            data.range_start, data.range_end, data.range_end
        ))
        existing = cursor.fetchone()

        if existing:
            # Update existing record
            new_play_count = existing[1] + (1 if data.increment else 0)
            update_query = """
                UPDATE user_play_history
                SET current_position = ?,
                    played_at = GETDATE(),
                    play_count = ?
                WHERE id = ?
            """
            cursor.execute(update_query, (data.current_position, new_play_count, existing[0]))
        else:
            # Insert new record
            insert_query = """
                INSERT INTO user_play_history (profileId, content_type, content_id, range_start, range_end, current_position, play_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                data.profileId, data.content_type, data.content_id,
                data.range_start, data.range_end, data.current_position,
                1 if data.increment else 0
            ))

        conn.commit()
        return {"status": "success", "message": "Play tracked"}

    except Exception as e:
        print(f"Error in track_play: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()