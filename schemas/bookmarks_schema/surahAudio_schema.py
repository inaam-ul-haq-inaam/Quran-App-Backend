from pydantic import BaseModel
class addSurahBookmark(BaseModel):
    profileid:int
    surahid:int
    reciterid:int
    startayat:int
    endayat:int