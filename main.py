from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import user_route,surah_route,ayat_route,bayan_route
from routers.Chain import createChain_route, deleteChain_route,showChain_route
from routers.Bookmarks.addbookmark import bayanbookmark_route,surahAudioBookmark_route
from routers.Bookmarks.getBookmark import getBayanBookmark,getSurahBookmark

app = FastAPI()
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

#user router
app.include_router(user_route.router)
#surah router
app.include_router(surah_route.router)
#ayat router
app.include_router(ayat_route.router)
#bayan router
app.include_router(bayan_route.router)
#bayan Bookmark router
app.include_router(bayanbookmark_route.router)
#get bayan bookmark router
app.include_router(getBayanBookmark.router)
#add surah bookmark router
app.include_router(surahAudioBookmark_route.router)
#get surah bookmark router
app.include_router(getSurahBookmark.router)
#create chain
app.include_router(createChain_route.router)
#show chain
app.include_router(showChain_route.router)
#delete chain
app.include_router(deleteChain_route.router)

@app.get("/")
def home():
    return {"message": "Audio Quran API Running"}
