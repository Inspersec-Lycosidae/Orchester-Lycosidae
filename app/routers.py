# routers.py
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from schemas import *
from typing import Optional

router = APIRouter(
    prefix="/route",
    tags=["route"]
)

###################################
##### Routers Functions Below #####
###################################

#Default function, change as needed
@router.get("")
async def root_func():
    return {"message": "Root function ran!"}

