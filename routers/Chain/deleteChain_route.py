from fastapi import APIRouter
from database import get_connection
from urllib.parse import unquote

router = APIRouter()

# ============================================================
# DELETE CHAIN BY ID
# ============================================================
@router.delete("/deleteChain/{chainId}")
def delete_chain(chainId: int):
    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built", "success": False}

    try:
        cursor = conn.cursor()

        # Check if chain exists
        cursor.execute("SELECT chainId, title FROM chain WHERE chainId = ?", (chainId,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {"message": f"Chain with ID {chainId} not found", "success": False}

        chain_title = row[1]

        # Delete chain details first (foreign key constraint)
        cursor.execute("DELETE FROM chainDetail WHERE chainId = ?", (chainId,))
        
        # Then delete chain
        cursor.execute("DELETE FROM chain WHERE chainId = ?", (chainId,))

        conn.commit()
        conn.close()

        return {
            "message": f"Chain '{chain_title}' deleted successfully",
            "chainId": chainId,
            "chainName": chain_title,
            "success": True
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return {"message": f"Error deleting chain: {str(e)}", "success": False}


# ============================================================
# DELETE CHAIN BY NAME (NEW - For voice commands)
# ============================================================
@router.delete("/deleteChainByName/{chainName}")
def delete_chain_by_name(chainName: str):
    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built", "success": False}

    try:
        cursor = conn.cursor()
        
        # Decode URL encoded string
        decoded_name = unquote(chainName).strip()
        
        # Find chain by name (case insensitive)
        cursor.execute("SELECT chainId, title FROM chain WHERE LOWER(title) = LOWER(?)", (decoded_name,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {"message": f"Chain '{decoded_name}' not found", "success": False}

        chain_id = row[0]
        chain_title = row[1]

        # Delete chain details
        cursor.execute("DELETE FROM chainDetail WHERE chainId = ?", (chain_id,))
        
        # Delete chain
        cursor.execute("DELETE FROM chain WHERE chainId = ?", (chain_id,))

        conn.commit()
        conn.close()

        return {
            "message": f"Chain '{chain_title}' deleted successfully",
            "chainId": chain_id,
            "chainName": chain_title,
            "success": True
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return {"message": f"Error deleting chain: {str(e)}", "success": False}


# ============================================================
# DELETE ALL CHAINS (Optional - with caution)
# ============================================================
@router.delete("/deleteAllChains/{profileId}")
def delete_all_chains(profileId: int):
    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built", "success": False}

    try:
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM chain WHERE profileId = ?", (profileId,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            conn.close()
            return {"message": "No chains found to delete", "success": False}

        # Delete all chain details for user's chains
        cursor.execute("""
            DELETE cd FROM chainDetail cd
            INNER JOIN chain c ON cd.chainId = c.chainId
            WHERE c.profileId = ?
        """, (profileId,))
        
        # Delete all chains
        cursor.execute("DELETE FROM chain WHERE profileId = ?", (profileId,))

        conn.commit()
        conn.close()

        return {
            "message": f"Successfully deleted {count} chains",
            "count": count,
            "success": True
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return {"message": f"Error deleting chains: {str(e)}", "success": False}