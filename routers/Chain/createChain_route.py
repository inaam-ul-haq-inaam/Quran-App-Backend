from fastapi import APIRouter
from database import get_connection
from schemas.chain_Schema.ChainCreate_Schema import ChainCreateSchema

router = APIRouter()

@router.post("/createChain")
def create_chain(data: ChainCreateSchema):
    conn = get_connection()
    if conn is None:
        return {"message": "Connection not built"}

    try:
        cursor = conn.cursor()

        profileId = data.profileid
        reciterId = data.reciterId
        title = data.title
        details = data.details

        # 1. Check if chain already exists
        cursor.execute(
            "SELECT chainId FROM chain WHERE profileId=? AND title=?",
            (profileId, title)
        )
        if cursor.fetchone():
            return {"message": "Chain with this title already exists for this user"}

        # 2. Insert into chain
        cursor.execute(
            "INSERT INTO chain (profileId, reciterId, title) VALUES (?, ?, ?)",
            (profileId, reciterId, title)
        )

        # 3. Get the latest chainId
        cursor.execute(
            "SELECT TOP 1 chainId FROM chain WHERE profileId=? AND title=? ORDER BY chainId DESC",
            (profileId, title)
        )
        row = cursor.fetchone()
        if not row:
            return {"message": "Failed to get new chainId"}

        chainId = row[0]

        # 4. Insert details (🛠️ YAHAN PLAYORDER ADD KIYA HAI)
        insert_detail = """
            INSERT INTO chainDetail (surahId, chainId, startAyat, endAyat, playOrder)
            VALUES (?, ?, ?, ?, ?)
        """

        for item in details:
            cursor.execute(
                insert_detail,
                # Ensure karein ke 'playOrder' aapki Pydantic schema mein mojood ho
                (item.surahId, chainId, item.startAyat, item.endAyat, item.playOrder) 
            )

        # 5. Agar sab perfectly ho jaye toh changes confirm (commit) karo
        conn.commit()

        return {
            "message": "Chain created successfully",
            "chainId": chainId,
            "reciterId": reciterId
        }

    except Exception as e:
        # ⚠️ Agar database phatay, toh jo aadha data save hua hai usko undo (rollback) kardo
        conn.rollback()
        return {"error": str(e)}

    finally:
        # 🔒 Database connection HAR HAAL mein close karo
        conn.close()