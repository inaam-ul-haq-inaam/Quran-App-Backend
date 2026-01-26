from pydantic import BaseModel

class BayanBookmarkCreate(BaseModel):
    profileid: int
    bayanid: int

class bayanBookmarkGet(BaseModel):
    title:str
    