from fastapi import APIRouter
from database import get_connection

router = APIRouter()

@router.get("/getChains/{profileId}")
def get_chains(profileId: int):

  
    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built"}

    cursor = conn.cursor()

  
    cursor.execute(
        "SELECT chainId, title, reciterId FROM chain WHERE profileId=?",
        (profileId,)
    )
    chains = cursor.fetchall()

    if not chains:
        conn.close()
        return {"message": "No chains found for this user", "data": []}

    result = []

  
    for chain in chains:
        chainId, title, reciterId = chain

        cursor.execute(
            "SELECT surahId, startAyat, endAyat FROM chainDetail WHERE chainId=?",
            (chainId,)
        )
        details = cursor.fetchall()

        detail_list = [
            {
                "surahId": d[0],
                "startAyat": d[1],
                "endAyat": d[2]
            }
            for d in details
        ]

        result.append({
            "chainId": chainId,
            "title": title,
            "reciterId": reciterId,   
            "details": detail_list
        })

    conn.close()

    return {
        "message": "Chains fetched successfully",
        "data": result
    }
