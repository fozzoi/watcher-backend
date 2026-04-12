import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="The Watcher - Archive Engine")

@app.get("/api/get_stream")
async def get_stream(archive_id: str):
    # For testing, you can use: 'night_of_the-living-dead' or 'TheGeneral'
    print(f"🎬 Requesting Public Domain movie: {archive_id}", flush=True)
    
    try:
        # The Internet Archive Metadata API
        url = f"https://archive.org/metadata/{archive_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code != 200:
                return {"status": "error", "message": "Movie not found in Archive"}
            
            data = response.json()
            server = data.get("server")
            dir = data.get("dir")
            files = data.get("files", [])

            # We search for the first high-quality .mp4 file
            video_file = next((f["name"] for f in files if f["name"].endswith(".mp4")), None)

            if video_file:
                # Construct the direct streaming URL
                real_video_url = f"https://{server}{dir}/{video_file}"
                print(f"✅ Found real file: {real_video_url}", flush=True)
                
                return {
                    "status": "success",
                    "movie": archive_id,
                    "stream_url": real_video_url
                }
            
            return {"status": "error", "message": "No playable video found"}

    except Exception as e:
        print(f"🔥 Error: {str(e)}", flush=True)
        raise HTTPException(status_code=500, detail="Internal server error")