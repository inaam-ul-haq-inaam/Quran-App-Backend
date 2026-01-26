from pydantic import BaseModel
from typing import Optional

class BayanResponse(BaseModel):
    BayanID: int
    Title: str
    AudioURL: str
    Duration: Optional[str]
    ScholarID: Optional[int]
    SurahID: Optional[int]
    StartAyatID: Optional[int]
    EndAyatID: Optional[int]
    CreatedAt: Optional[str]
