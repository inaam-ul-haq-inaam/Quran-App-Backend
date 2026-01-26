from fastapi import APIRouter
from database import get_connection
from schemas.chain_Schema.ChainCreate_Schema import ChainCreateSchema

router = APIRouter()

@router.post("/createChain")
def create_chain(data: ChainCreateSchema):

  
    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built"}

    cursor = conn.cursor()

    profileId = data.profileid
    reciterId = data.reciterId
    title = data.title
    details = data.details

  
    cursor.execute(
        "SELECT chainId FROM chain WHERE profileId=? AND title=?",
        (profileId, title)
    )
    if cursor.fetchone():
        conn.close()
        return {"message": "Chain with this title already exists for this user"}

   
    cursor.execute(
        "INSERT INTO chain (profileId, reciterId, title) VALUES (?, ?, ?)",
        (profileId, reciterId, title)
    )

    
    cursor.execute(
        "SELECT TOP 1 chainId FROM chain WHERE profileId=? AND title=? ORDER BY chainId DESC",
        (profileId, title)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"message": "Failed to get new chainId"}

    chainId = row[0]

    
    insert_detail = """
        INSERT INTO chainDetail (surahId, chainId, startAyat, endAyat)
        VALUES (?, ?, ?, ?)
    """

    for item in details:
        cursor.execute(
            insert_detail,
            (item.surahId, chainId, item.startAyat, item.endAyat)
        )

   
    conn.commit()
    conn.close()

   
    return {
        "message": "Chain created successfully",
        "chainId": chainId,
        "reciterId": reciterId
    }
