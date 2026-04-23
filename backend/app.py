import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from api.routes import router
from api.startup import lifespan

# Load environment
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Vulcan OmniPro 220 Agent",
    description="Multimodal reasoning agent for welding technical support",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve extracted images
if not os.path.exists("static/images"):
    os.makedirs("static/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="static/images"), name="images")


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True, log_level="info")