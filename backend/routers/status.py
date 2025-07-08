from fastapi import APIRouter
from typing import List

from models import StatusCheck, StatusCheckCreate
from database import Database

router = APIRouter(prefix="/api")

@router.get("/")
async def root():
    return {"message": "XToPDF API - Convert LaTeX to PDF"}

@router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    db = Database.get_db()
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    db = Database.get_db()
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]