#main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import router
from database import init_db

app = FastAPI()
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Microservice is up!"}
