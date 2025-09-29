from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import routes

app = FastAPI(title="Black Sea Aquatic Parameters API")

#Razreshavane zayavki ot frontenda
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], #adresa na Vite dev servera
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)

@app.get("/")
def root():
    return {"message":"Backend API is running! :)"}