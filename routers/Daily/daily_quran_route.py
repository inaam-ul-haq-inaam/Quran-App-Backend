from fastapi import APIRouter, HTTPException
from database import get_connection
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

# ============================================================
# 1. GET - Get saved progress
# ============================================================
class DailyQuranProgressResponse(BaseModel):
    status: str
    profileId: int
    current_surah_id: int
    current_ayat_index: int
    updated_at: Optional[str] = None

@router.get("/daily/quran/{profileId}", response_model=DailyQuranProgressResponse)
def get_daily_quran_progress(profileId: int):
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        query = """
            SELECT current_surah_id, current_ayat_index, updated_at
            FROM daily_quran
            WHERE profileId = ?
        """
        cursor.execute(query, (profileId,))
        row = cursor.fetchone()

        if row:
            return {
                "status": "success",
                "profileId": profileId,
                "current_surah_id": row[0],
                "current_ayat_index": row[1],
                "updated_at": str(row[2]) if row[2] else None
            }
        else:
            # No progress found, return defaults
            return {
                "status": "success",
                "profileId": profileId,
                "current_surah_id": 1,
                "current_ayat_index": 0,
                "updated_at": None
            }
    except Exception as e:
        print(f"Error in get_daily_quran_progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# 2. POST - Save/Update progress
# ============================================================
class DailyQuranSaveSchema(BaseModel):
    profileId: int
    current_surah_id: int
    current_ayat_index: int

@router.post("/daily/quran")
def save_daily_quran_progress(data: DailyQuranSaveSchema):
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        
        # Check if record exists
        check_query = "SELECT id FROM daily_quran WHERE profileId = ?"
        cursor.execute(check_query, (data.profileId,))
        existing = cursor.fetchone()

        if existing:
            # Update existing
            update_query = """
                UPDATE daily_quran 
                SET current_surah_id = ?, 
                    current_ayat_index = ?, 
                    updated_at = GETDATE()
                WHERE profileId = ?
            """
            cursor.execute(update_query, (data.current_surah_id, data.current_ayat_index, data.profileId))
        else:
            # Insert new
            insert_query = """
                INSERT INTO daily_quran (profileId, current_surah_id, current_ayat_index, updated_at)
                VALUES (?, ?, ?, GETDATE())
            """
            cursor.execute(insert_query, (data.profileId, data.current_surah_id, data.current_ayat_index))

        conn.commit()
        return {"status": "success", "message": "Progress saved"}

    except Exception as e:
        print(f"Error in save_daily_quran_progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============================================================
# 3. DELETE - Reset progress
# ============================================================
@router.delete("/daily/quran/{profileId}")
def reset_daily_quran_progress(profileId: int):
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        
        # Delete record
        delete_query = "DELETE FROM daily_quran WHERE profileId = ?"
        cursor.execute(delete_query, (profileId,))
        conn.commit()

        return {"status": "success", "message": "Progress reset"}

    except Exception as e:
        print(f"Error in reset_daily_quran_progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()