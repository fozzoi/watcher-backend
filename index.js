const express = require('express');
const { MOVIES } = require('@consumet/extensions');
const cors = require('cors');

const app = express();
app.use(cors());

// Initialize the FlixHQ provider
const flixhq = new MOVIES.FlixHQ();

app.get('/', (req, res) => {
    res.send({ status: 'online', message: 'The Watcher Node Engine is Live' });
});

app.get('/api/get_stream', async (req, res) => {
    const { tmdb_id, media_type, title, season, episode } = req.query;
    
    // Log what the phone is sending
    console.log(`📡 Request: ${media_type.toUpperCase()} | Title: "${title}" | ID: ${tmdb_id}`);

    try {
        if (!title) throw new Error("No title provided by the app");

        // 1. Search FlixHQ using the TITLE John provided
        console.log(`🔍 Searching FlixHQ for: "${title}"`);
        const searchResults = await flixhq.search(title);
        
        // 2. Find the best matching result
        const movie = searchResults.results.find(r => 
            r.title.toLowerCase().includes(title.toLowerCase())
        );

        if (movie) {
            console.log(`✅ Match found: ${movie.id}`);
            const movieInfo = await flixhq.fetchMediaInfo(movie.id);
            
            let epId = movie.id;
            // Handle TV Episode logic
            if (media_type === 'tv') {
                const ep = movieInfo.episodes.find(e => e.season == season && e.number == episode);
                if (ep) epId = ep.id;
            }

            // 3. Extract the actual .m3u8 sources
            const sources = await flixhq.fetchEpisodeSources(epId, movie.id);

            if (sources?.sources?.length > 0) {
                console.log("🎉 SUCCESS! Direct stream found.");
                return res.json({
                    status: 'success',
                    stream_url: sources.sources[0].url,
                    is_m3u8: true
                });
            }
        }

        throw new Error("No direct sources found for this title");

    } catch (error) {
        console.log("🛑 Scraper Error:", error.message);
        
        // Safety Fallback (Iframe)
        const fallback = media_type === 'movie' 
            ? `https://vidsrc.me/embed/movie?tmdb=${tmdb_id}`
            : `https://vidsrc.me/embed/tv?tmdb=${tmdb_id}&s=${season}&e=${episode}`;
        
        res.json({ 
            status: 'success', 
            stream_url: fallback, 
            is_m3u8: false,
            msg: "Using fallback due to scraper error" 
        });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));