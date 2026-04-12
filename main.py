from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="The Watcher API")

# This is the exact endpoint your React Native app will call
@app.get("/api/get_stream")
async def get_stream(tmdb_id: str, season: int = 1, episode: int = 1):
    print(f"Mobile app requested stream for TMDB ID: {tmdb_id}")
    
    try:
        # =========================================================
        # THIS IS WHERE YOUR EXTRACTION LOGIC WILL GO IN THE FUTURE
        # E.g., spinning up Playwright, extracting the .m3u8, etc.
        # =========================================================
        
        # For right now, we are just returning a fake video link to test the connection
        fake_video_url = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
        
        return {
            "status": "success",
            "tmdb_id": tmdb_id,
            "stream_url": fake_video_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# A simple health check to make sure the server is awake
@app.get("/")
async def root():
    return {"message": "The Watcher API is running!"}