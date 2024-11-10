from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router as image_router

app = FastAPI(title="Image Processing API")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(image_router, prefix="/api")