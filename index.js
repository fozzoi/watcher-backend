const express = require('express');
const { META, MOVIES } = require('@consumet/extensions');
const cors = require('cors');

const app = express();
app.use(cors());

// Initialize multiple providers
const tmdb = new META.TMDB();
const flixhq = new MOVIES.FlixHQ();

app.get('/', (req, res) => {
    res.send({ status: 'online', mode: 'Multi-Provider Engine' });
});

app.get('/api/get_stream', async (req, res) => {
    const { tmdb_id, media_type, season, episode } = req.query;
    console.log(`📡 Multi-Scrape Request: ${media_type} ${tmdb_id}`);

    try {
        // --- ATTEMPT 1: TMDB Meta (Best Quality) ---
        try {
            console.log("🔍 Attempting TMDB Meta...");
            let streamData;
            if (media_type === 'movie') {
                streamData = await tmdb.fetchEpisodeSources(tmdb_id, tmdb_id);
            } else {
                const info = await tmdb.fetchMediaInfo(tmdb_id, 'tv');
                const targetEp = info.episodes.find(e => e.season == season && e.number == episode);
                if (targetEp) streamData = await tmdb.fetchEpisodeSources(targetEp.id, tmdb_id);
            }

            if (streamData?.sources?.length > 0) {
                console.log("🎉 Success via TMDB Meta!");
                return res.json({ status: 'success', stream_url: streamData.sources[0].url, is_m3u8: true });
            }
        } catch (e) { console.log("⚠️ TMDB Meta Failed..."); }

        // --- ATTEMPT 2: Direct FlixHQ (Search by Title) ---
        // Sometimes the direct search works when the ID-mapping fails
        try {
            console.log("🔍 Attempting Direct FlixHQ Search...");
            // We need a title for search, but since we only have ID, we use TMDB to get the title first
            const info = await tmdb.fetchMediaInfo(tmdb_id, media_type === 'tv' ? 'tv' : 'movie');
            const searchResults = await flixhq.search(info.title);
            const movie = searchResults.results.find(r => r.releaseDate == info.releaseDate || r.title == info.title);

            if (movie) {
                const movieInfo = await flixhq.fetchMediaInfo(movie.id);
                let epId = movie.id;
                if (media_type === 'tv') {
                    const ep = movieInfo.episodes.find(e => e.season == season && e.number == episode);
                    if (ep) epId = ep.id;
                }
                const sources = await flixhq.fetchEpisodeSources(epId, movie.id);
                if (sources?.sources?.length > 0) {
                    console.log("🎉 Success via FlixHQ Search!");
                    return res.json({ status: 'success', stream_url: sources.sources[0].url, is_m3u8: true });
                }
            }
        } catch (e) { console.log("⚠️ FlixHQ Search Failed..."); }

        throw new Error("All scrapers exhausted");

    } catch (error) {
        console.log("🛑 All Scrapers Failed. Sending Iframe Fallback.");
        const fallback = media_type === 'movie' 
            ? `https://vidsrc.me/embed/movie?tmdb=${tmdb_id}`
            : `https://vidsrc.me/embed/tv?tmdb=${tmdb_id}&s=${season}&e=${episode}`;
        
        res.json({ status: 'success', stream_url: fallback, is_m3u8: false });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));