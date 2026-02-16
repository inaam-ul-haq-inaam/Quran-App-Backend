from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from Services.tokenCreate import create_command_token

router = APIRouter(prefix="/voice", tags=["Voice Command"])


# 📌 Request Body Model
class VoiceTextRequest(BaseModel):
    text: str


@router.post("/command")
async def process_voice_command(data: VoiceTextRequest):

    try:
        received_text = data.text.strip()
        print(f"🎤 SERVER RECEIVED TEXT: '{received_text}'")

        if not received_text:
            return {
                "status": "error",
                "message": "Empty text received"
            }

        # 🎯 Create Token
        final_token = create_command_token(received_text)

        return {
            "status": "success",
            "token": final_token
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
