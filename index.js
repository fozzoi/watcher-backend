const express = require('express');
const { META } = require('@consumet/extensions'); // Use the META provider
const cors = require('cors');

const app = express();
app.use(cors());

// Initialize the TMDB Meta provider (This is the "Brain" of Consumet)
const tmdb = new META.TMDB();

app.get('/', (req, res) => {
    res.send({ status: 'online', message: 'The Watcher Node Meta-Engine is Live' });
});

app.get('/api/get_stream', async (req, res) => {
    const { tmdb_id, media_type, season, episode } = req.query;
    console.log(`📡 Requesting Meta-Stream for: ${media_type} ${tmdb_id}`);

    try {
        // 1. Fetch info and links directly using the TMDB ID
        // The Meta provider handles the searching and mapping for you!
        let streamData;
        
        if (media_type === 'movie') {
            // For movies, we can fetch sources directly using the TMDB ID
            streamData = await tmdb.fetchEpisodeSources(tmdb_id, tmdb_id);
        } else {
            // For TV shows, we need the internal "episode ID"
            // Step A: Get show info
            const info = await tmdb.fetchMediaInfo(tmdb_id, media_type === 'tv' ? 'tv' : 'movie');
            
            // Step B: Find the specific episode
            const targetEp = info.episodes.find(e => e.season == season && e.number == episode);
            if (!targetEp) throw new Error("Episode not found in Meta database");
            
            // Step C: Fetch the stream
            streamData = await tmdb.fetchEpisodeSources(targetEp.id, tmdb_id);
        }

        if (streamData && streamData.sources && streamData.sources.length > 0) {
            // Find the highest quality (or the first) .m3u8 link
            const bestSource = streamData.sources.find(s => s.quality === 'auto') || streamData.sources[0];
            
            console.log("🎉 SUCCESS! Found direct link:", bestSource.url);
            return res.json({
                status: 'success',
                stream_url: bestSource.url,
                is_m3u8: true
            });
        }

        throw new Error("No sources found for this ID");

    } catch (error) {
        console.log("⚠️ Meta-Scraper failed, sending fallback:", error.message);
        
        // Safety Fallback (Back to the iframe if the Meta-API is down)
        const fallback = media_type === 'movie' 
            ? `https://vidsrc.me/embed/movie?tmdb=${tmdb_id}`
            : `https://vidsrc.me/embed/tv?tmdb=${tmdb_id}&s=${season}&e=${episode}`;
        
        res.json({ 
            status: 'success', 
            stream_url: fallback, 
            is_m3u8: false,
            error_log: error.message 
        });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`🚀 Node Meta-Server running on port ${PORT}`));