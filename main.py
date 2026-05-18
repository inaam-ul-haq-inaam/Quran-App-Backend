from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import user_route,surah_route,ayat_route,bayan_route
from routers.Chain import createChain_route, deleteChain_route,showChain_route
from routers.Bookmarks.addbookmark import bayanbookmark_route,surahAudioBookmark_route
from routers.Bookmarks.getBookmark import getBayanBookmark,getSurahBookmark
from routers.Bookmarks.getBookmark import getBayanBookmark,getSurahBookmark
from routers.Bookmarks.deleteBookmark import deleteBookmark
from routers.History import track_play_route
from routers.History import last_played_route
from routers.History import resume_position_route
from routers.History import most_played_route
from routers.History import update_position
from routers.Daily import daily_quran_route


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
#delete boolmark surah
app.include_router(deleteBookmark.router)
#create chain
app.include_router(createChain_route.router)
#show chain
app.include_router(showChain_route.router)
#delete chain
app.include_router(deleteChain_route.router)
#play_history router
app.include_router(track_play_route.router)
#last played router
app.include_router(last_played_route.router)
#resume content router
app.include_router(resume_position_route.router)
#most played content router
app.include_router(most_played_route.router)
#update position 
app.include_router(update_position.router)
#daily quran 
app.include_router(daily_quran_route.router)

from routers.Voice import voice_route
from routers.Chain import showChainDetails
app.include_router(voice_route.router)
app.include_router(showChainDetails.router)

@app.get("/")
def home():
    return {"message": "Audio Quran API Running"}
