from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os

from Services.AudioToText import transcribe_audio
from Services.tokenCreate import create_command_token

router = APIRouter(prefix="/voice", tags=["Voice Command"])

@router.post("/command")
async def process_voice_command(audio: UploadFile = File(...)):
    
    temp_filename = f"temp_{audio.filename}"
    
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        transcribed_text = transcribe_audio(temp_filename)
        
        if not transcribed_text:
            return {"status": "error", "message": "No voice detected"}

        final_token = create_command_token(transcribed_text)
        
        return {
            "status": "success",
            "token": final_token
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)