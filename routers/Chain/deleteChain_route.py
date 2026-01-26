from fastapi import APIRouter
from database import get_connection

router = APIRouter()

@router.delete("/deleteChain/{chainId}")
def delete_chain(chainId: int):

    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built"}

    cursor = conn.cursor()

    cursor.execute("SELECT chainId FROM chain WHERE chainId=?", (chainId,))
    if not cursor.fetchone():
        conn.close()
        return {"message": "Chain not found"}

    cursor.execute(
        "DELETE FROM chainDetail WHERE chainId=?",
        (chainId,)
    )

    cursor.execute(
        "DELETE FROM chain WHERE chainId=?",
        (chainId,)
    )

    conn.commit()
    conn.close()

    return {
        "message": "Chain deleted successfully",
        "chainId": chainId
    }
