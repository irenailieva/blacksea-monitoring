from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["API"])

@router.get("/hello")
def hello():
    return {"msg": "Hello from FastAPI :)"}