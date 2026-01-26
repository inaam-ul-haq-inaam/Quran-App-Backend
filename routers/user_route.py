from database import get_connection
from fastapi import APIRouter
from models.user_model import UserCreate,UserLogin



router=APIRouter()

@router.post("/register")
def register_user(user:UserCreate):
    conn=get_connection()

    if conn is None:
        return{"message":"Error in Bulding connection"}
    
    cursor =conn.cursor()

    query="select profileid from profile where email=?"
    cursor.execute(query,(user.email))
    if cursor.fetchone():
        conn.close()
        return{"message":"already exist this email"}
    
    query=("insert into profile(name,email,password)values(?,?,?)")
    cursor.execute(query,(user.name,user.email,user.password))
    conn.commit()
    conn.close()
    return{"message:":"User Registered Successfully!"}


 

@router.post("/login")
def login_User(user:UserLogin):
    conn=get_connection()
    if conn is None:
        return{"message":"Error in building connection"}
    
    cursor=conn.cursor()
    query="select profileid, name, email, password, profilepic, voicemode from profile where email=? and password=?"
    cursor.execute(query,(user.email,user.password))
    row=cursor.fetchone()

    if not row:
        return{"message":"invalid email or password"}
    
    profileid, name, email, password, profilepic, voicemode = row

    return{
        "message":"login success!",
        "data": {
            "profileid": profileid,
            "name": name,
            "email": email,
            "profilepic": profilepic,
            "voicemode": voicemode
        }
    }
