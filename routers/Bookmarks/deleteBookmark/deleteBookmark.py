from fastapi import APIRouter
from database import get_connection

router = APIRouter()

# ============================================================
# DELETE BOOKMARK BY ID
# ============================================================
@router.delete("/deleteBookmark/{bookmarkId}")
def delete_bookmark(bookmarkId: int):
    """
    Delete a bookmark by its ID
    Example: DELETE /deleteBookmark/5
    """
    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built", "success": False}
    
    try:
        cursor = conn.cursor()
        
        # Check if bookmark exists
        cursor.execute("SELECT bookmarkId, title FROM bookmarkAudio WHERE bookmarkId = ?", (bookmarkId,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {"message": f"Bookmark with ID {bookmarkId} not found", "success": False}
        
        bookmark_title = row[1] if row[1] else "Bookmark"
        
        # Delete the bookmark
        cursor.execute("DELETE FROM bookmarkAudio WHERE bookmarkId = ?", (bookmarkId,))
        
        conn.commit()
        conn.close()
        
        return {
            "message": f"Bookmark '{bookmark_title}' deleted successfully",
            "bookmarkId": bookmarkId,
            "success": True
        }
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"message": f"Error deleting bookmark: {str(e)}", "success": False}


# ============================================================
# DELETE ALL BOOKMARKS FOR A USER (Optional)
# ============================================================
@router.delete("/deleteAllBookmarks/{profileId}")
def delete_all_bookmarks(profileId: int):
    """
    Delete all bookmarks for a specific user
    Example: DELETE /deleteAllBookmarks/1
    """
    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built", "success": False}
    
    try:
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM bookmarkAudio WHERE profileId = ?", (profileId,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            conn.close()
            return {"message": "No bookmarks found to delete", "success": False}
        
        # Delete all bookmarks for user
        cursor.execute("DELETE FROM bookmarkAudio WHERE profileId = ?", (profileId,))
        
        conn.commit()
        conn.close()
        
        return {
            "message": f"Successfully deleted {count} bookmarks",
            "count": count,
            "success": True
        }
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"message": f"Error deleting bookmarks: {str(e)}", "success": False}