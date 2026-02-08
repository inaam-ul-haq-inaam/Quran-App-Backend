import whisper
import os
from Services.romanUrdu import WHISPER_PROMPT


print("Loading Whisper Model...")
model = whisper.load_model("small")
print("Whisper Model Loaded!")

def transcribe_audio(file_path: str) -> str:
   
    try:
        result = model.transcribe(
            file_path,
            fp16=False,     
            language="en",  
            initial_prompt=WHISPER_PROMPT
        )
        return result["text"].strip().lower()
    except Exception as e:
        print(f"❌ Whisper Error: {e}")
        return ""