import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="The Watcher API")

@app.get("/api/get_stream")
async def get_stream(tmdb_id: str, season: int = 1, episode: int = 1):
    # Added flush=True so this shows up in Render logs instantly!
    print(f"🎬 Mobile app requested stream for TMDB ID: {tmdb_id}", flush=True)
    
    try:
        # =================================================================
        # THE AGGREGATOR TARGET
        # You will replace this base URL with whatever public API you find
        # =================================================================
        # Example for a Movie:
        aggregator_url = f"https://api.example-indexer.com/movie/{tmdb_id}"
        
        # If it was a TV show, your logic might switch to this:
        # aggregator_url = f"https://api.example-indexer.com/tv/{tmdb_id}/{season}/{episode}"

        print(f"🔍 Searching aggregator: {aggregator_url}", flush=True)

        # We use an async client so your server stays lightning fast
        async with httpx.AsyncClient() as client:
            # We send a request to the aggregator API
            response = await client.get(aggregator_url)
            
            # If the aggregator responds successfully...
            if response.status_code == 200:
                data = response.json()
                
                # Every API formats their JSON differently. 
                # You might need to change 'stream_url' to match whatever the API calls it!
                if "stream_url" in data:
                    real_video_url = data["stream_url"]
                    print(f"✅ Found stream! Sending to app...", flush=True)
                    
                    return {
                        "status": "success",
                        "tmdb_id": tmdb_id,
                        "stream_url": real_video_url
                    }
            
            # If the API didn't have the movie or failed
            print(f"❌ Stream not found on aggregator.", flush=True)
            return {"status": "error", "message": "Stream not found"}
            
    except Exception as e:
        print(f"🔥 Server crash: {str(e)}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "The Watcher API is running!"}