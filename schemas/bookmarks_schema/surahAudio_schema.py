from pydantic import BaseModel
from typing import Optional
class addSurahBookmark(BaseModel):
    profileid:int
    surahid:int
    reciterid:int
    startayat:int
    endayat:int
    title: Optional[str] = None  