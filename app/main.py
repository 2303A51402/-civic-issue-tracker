from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import models
from .database import engine
from .routers import auth, reports

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Civic Issue Tracker API",
    description="Report and track local civic issues (potholes, garbage, streetlights, etc.) "
                 "with a public map view and an admin analytics dashboard.",
    version="1.0.0",
)

# CORS — allow your Netlify/Vercel frontend to talk to this API.
# Replace "*" with your actual frontend URL once deployed, for security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {"message": "Civic Issue Tracker API is running. Visit /docs for Swagger UI."}
