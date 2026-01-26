from pydantic import BaseModel

class SurahList(BaseModel):
    surahNumber:int
    NameArabic:str
    NameEnglish:str
    TotalAyat:int