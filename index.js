const express = require('express');
const { MOVIES } = require('@consumet/extensions');
const cors = require('cors');

const app = express();
app.use(cors());

// Initialize the FlixHQ provider (the one Consumet uses for movies/TV)
const flixhq = new MOVIES.FlixHQ();

app.get('/', (req, res) => {
    res.send({ status: 'online', message: 'The Watcher Node Engine is Live' });
});

app.get('/api/get_stream', async (req, res) => {
    const { tmdb_id, media_type, season, episode } = req.query;
    console.log(`📡 Requesting: ${media_type} ${tmdb_id}`);

    try {
        // 1. Search for the movie on FlixHQ
        // Note: Consumet search usually works better with the title, 
        // but we can use the TMDB ID to verify the result.
        const searchResults = await flixhq.search(tmdb_id); 
        
        // If TMDB ID search fails, you might need a title-based search fallback
        if (searchResults.results.length === 0) {
            throw new Error("No results found on provider");
        }

        const media = searchResults.results[0];
        
        // 2. Get the internal Consumet ID for the specific episode
        const info = await flixhq.fetchMediaInfo(media.id);
        
        let episodeId = media.id;
        if (media_type === 'tv') {
            const targetEp = info.episodes.find(e => e.season == season && e.number == episode);
            if (!targetEp) throw new Error("Episode not found");
            episodeId = targetEp.id;
        }

        // 3. Extract the actual .m3u8 links!
        const sources = await flixhq.fetchEpisodeSources(episodeId, media.id);

        if (sources.sources && sources.sources.length > 0) {
            console.log("✅ Found link:", sources.sources[0].url);
            return res.json({
                status: 'success',
                stream_url: sources.sources[0].url,
                is_m3u8: true
            });
        }

        throw new Error("No sources found");

    } catch (error) {
        console.log("⚠️ Scraper failed, sending fallback:", error.message);
        // Safety Fallback (Same as before)
        const fallback = media_type === 'movie' 
            ? `https://vidsrc.me/embed/movie?tmdb=${tmdb_id}`
            : `https://vidsrc.me/embed/tv?tmdb=${tmdb_id}&s=${season}&e=${episode}`;
        
        res.json({ status: 'success', stream_url: fallback, is_m3u8: false });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));