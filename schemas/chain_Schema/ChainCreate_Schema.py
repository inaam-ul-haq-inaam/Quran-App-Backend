from pydantic import BaseModel
from typing import List

class ChainDetailSchema(BaseModel):
    surahId: int
    startAyat: int
    endAyat: int
    playOrder: int  # 👈 YEH LINE ADD KAREIN

class ChainCreateSchema(BaseModel):
    profileid: int        
    reciterId: int        
    title: str
    details: List[ChainDetailSchema]