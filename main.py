from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import interactions, hcp, agent
from database.db import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HCP CRM AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router, prefix="/api/interactions", tags=["interactions"])
app.include_router(hcp.router, prefix="/api/hcp", tags=["hcp"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])

@app.get("/")
def root():
    return {"message": "HCP CRM AI Backend Running"}