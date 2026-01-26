from pydantic import BaseModel
from typing import Optional
class ayats(BaseModel):
    surah_ID: int
    fromAyat: Optional[int] = None
    toAyat: Optional[int] = None
    reciterid:int