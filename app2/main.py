from fastapi import FastAPI



from app_tools import UserPyd
from database_tools import User, create_user


app = FastAPI()

@app.get("/")
async def join_page():
    #petqa return anenq static/join_page
    pass




@app.post("/create-user")
async def create_user(user: UserPyd):
    user = User(username=user.username, password=user.password)
    create_user(user)
    #grel tokeni kod
    return {"status": "ok"}


