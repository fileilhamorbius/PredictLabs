import os
import json
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.data_engine import engine, LEAGUES_CONFIG, SEASONS

app = FastAPI(
    title="PredictLabs API",
    description="Football Goal & xG Comparison Matrix with Advanced Statistical Predictions",
    version="3.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.get("/api/seasons")
async def get_seasons():
    """Returns available season filters."""
    return {"status": "success", "data": SEASONS}

@app.get("/api/leagues")
async def get_leagues():
    """Returns list of supported 6 top domestic leagues."""
    return {"status": "success", "data": list(LEAGUES_CONFIG.values())}

@app.get("/api/teams")
async def get_teams(
    league: str = Query("epl", description="League ID (epl, laliga, bundesliga, seriea, ligue1, eredivisie)"),
    season: str = Query("2026/2027", description="Season filter: 2026/2027 or 2025/2026")
):
    """Returns all domestic teams in the selected league for that season."""
    if league not in LEAGUES_CONFIG:
        raise HTTPException(status_code=404, detail="League not supported")
    teams = engine.get_teams(league, season=season)
    return {
        "status": "success",
        "league": LEAGUES_CONFIG[league],
        "season": season,
        "count": len(teams),
        "data": teams
    }

@app.get("/api/matrix-compare")
async def get_matrix_compare(
    league: str = Query("epl", description="League ID"),
    season: str = Query("2026/2027", description="Season: 2026/2027 or 2025/2026"),
    team1: str = Query(..., description="Team 1 Name"),
    venue1: str = Query("home", description="Venue for Team 1: home, away, overall"),
    team2: str = Query(..., description="Team 2 Name"),
    venue2: str = Query("away", description="Venue for Team 2: home, away, overall"),
    last_n: int = Query(10, ge=1, le=38, description="Last N matches (e.g. 3, 5, 10)")
):
    """
    Computes Symmetrical Mean & Median Matrix for Team 1 & Team 2
    strictly filtered by season (2026/2027 or 2025/2026).
    """
    if league not in LEAGUES_CONFIG:
        raise HTTPException(status_code=404, detail="League not supported")

    stats1 = engine.get_team_matrix_stats(league, team1, venue=venue1, last_n=last_n, season=season)
    stats2 = engine.get_team_matrix_stats(league, team2, venue=venue2, last_n=last_n, season=season)

    return {
        "status": "success",
        "league": LEAGUES_CONFIG[league],
        "season": season,
        "last_n": last_n,
        "team1": stats1,
        "team2": stats2
    }

@app.get("/api/predict")
async def get_prediction(
    league: str = Query("epl", description="League ID"),
    season: str = Query("2026/2027", description="Season: 2026/2027 or 2025/2026"),
    team1: str = Query(..., description="Team 1 Name"),
    team2: str = Query(..., description="Team 2 Name"),
    last_n: int = Query(10, ge=1, le=38, description="Last N matches")
):
    """
    Advanced Statistical Poisson & xG-weighted Over/Under Predictions:
    - HT, 2HT, FT
    - Individual Team Goals and Match Totals
    - Venue-Specific (Home vs Away) & Overall + Standings
    - Analytical reasoning explanations
    """
    if league not in LEAGUES_CONFIG:
        raise HTTPException(status_code=404, detail="League not supported")

    preds = engine.get_full_predictions(league, team1, team2, season=season, last_n=last_n)
    return {
        "status": "success",
        "league": LEAGUES_CONFIG[league],
        "data": preds
    }

@app.post("/api/refresh")
async def refresh_data(league: str = Query("epl")):
    """Force re-scrapes latest match data for the league."""
    if league not in LEAGUES_CONFIG:
        raise HTTPException(status_code=404, detail="League not supported")
    engine.load_league_matches(league, force_refresh=True)
    return {"status": "success", "message": f"Data for {league} refreshed successfully"}

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
