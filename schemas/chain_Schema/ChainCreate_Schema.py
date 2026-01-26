from pydantic import BaseModel
from typing import List


class ChainDetailSchema(BaseModel):
    surahId: int
    startAyat: int
    endAyat: int
    
class ChainCreateSchema(BaseModel):
    profileid: int        
    reciterId: int        
    title: str
    details: List[ChainDetailSchema]

