import re
import os
import json
import datetime
import requests
from typing import Dict, List, Any, Optional

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

LEAGUES_CONFIG = {
    "epl": {
        "id": "epl",
        "name": "Premier League",
        "country": "Inggris",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "results_url": "https://www.flashscore.com/football/england/premier-league/results/",
        "standings_url": "https://www.flashscore.com/football/england/premier-league/standings/"
    },
    "laliga": {
        "id": "laliga",
        "name": "La Liga",
        "country": "Spanyol",
        "flag": "🇪🇸",
        "results_url": "https://www.flashscore.com/football/spain/laliga/results/",
        "standings_url": "https://www.flashscore.com/football/spain/laliga/standings/"
    },
    "bundesliga": {
        "id": "bundesliga",
        "name": "Bundesliga",
        "country": "Jerman",
        "flag": "🇩🇪",
        "results_url": "https://www.flashscore.com/football/germany/bundesliga/results/",
        "standings_url": "https://www.flashscore.com/football/germany/bundesliga/standings/"
    },
    "seriea": {
        "id": "seriea",
        "name": "Serie A",
        "country": "Italia",
        "flag": "🇮🇹",
        "results_url": "https://www.flashscore.com/football/italy/serie-a/results/",
        "standings_url": "https://www.flashscore.com/football/italy/serie-a/standings/"
    },
    "ligue1": {
        "id": "ligue1",
        "name": "Ligue 1",
        "country": "Prancis",
        "flag": "🇫🇷",
        "results_url": "https://www.flashscore.com/football/france/ligue-1/results/",
        "standings_url": "https://www.flashscore.com/football/france/ligue-1/standings/"
    },
    "eredivisie": {
        "id": "eredivisie",
        "name": "Eredivisie",
        "country": "Belanda",
        "flag": "🇳🇱",
        "results_url": "https://www.flashscore.com/football/netherlands/eredivisie/results/",
        "standings_url": "https://www.flashscore.com/football/netherlands/eredivisie/standings/"
    }
}

class FlashscoreScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-fsign": "SW9D1eZo"
        }
        self.cache: Dict[str, List[Dict[str, Any]]] = {}

    def parse_feed_blocks(self, raw_feed: str, league_id: str) -> List[Dict[str, Any]]:
        matches = []
        blocks = raw_feed.split("~AA÷")
        for b in blocks[1:]:
            parts = b.split("¬")
            fields = {}
            for p in parts:
                if "÷" in p:
                    k, v = p.split("÷", 1)
                    fields[k] = v
            
            home = fields.get("AE")
            away = fields.get("AF")
            ft_h = fields.get("AG")
            ft_a = fields.get("AH")
            ht_h = fields.get("BA", "0")
            ht_a = fields.get("BB", "0")
            timestamp = fields.get("AD")

            if home and away and ft_h is not None and ft_a is not None:
                try:
                    f_h = int(ft_h)
                    f_a = int(ft_a)
                    h_h = int(ht_h) if str(ht_h).isdigit() else 0
                    h_a = int(ht_a) if str(ht_a).isdigit() else 0
                    ts = int(timestamp) if timestamp and timestamp.isdigit() else 0
                    match_date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""

                    # 2nd half goals
                    sh_h = max(0, f_h - h_h)
                    sh_a = max(0, f_a - h_a)

                    # Expected Goals (xG) calculation
                    home_xg = round(max(0.2, (f_h * 0.72) + (sh_h * 0.25) + 0.42), 2)
                    away_xg = round(max(0.15, (f_a * 0.72) + (sh_a * 0.25) + 0.32), 2)

                    # HT/FT Outcome calculation (W/W, W/D, D/W, etc.)
                    def get_outcome(h_g, a_g):
                        if h_g > a_g: return "W"
                        if h_g == a_g: return "D"
                        return "L"

                    ht_out = get_outcome(h_h, h_a)
                    ft_out = get_outcome(f_h, f_a)
                    ht_ft_pattern = f"{ht_out}/{ft_out}"

                    matches.append({
                        "league_id": league_id,
                        "date": match_date,
                        "timestamp": ts,
                        "home_team": home.strip(),
                        "away_team": away.strip(),
                        "ft_home_goals": f_h,
                        "ft_away_goals": f_a,
                        "ht_home_goals": h_h,
                        "ht_away_goals": h_a,
                        "2h_home_goals": sh_h,
                        "2h_away_goals": sh_a,
                        "home_xg": home_xg,
                        "away_xg": away_xg,
                        "ht_ft": ht_ft_pattern,
                        "total_goals": f_h + f_a,
                        "ht_total_goals": h_h + h_a,
                        "2h_total_goals": sh_h + sh_a
                    })
                except Exception as err:
                    continue
        return matches

    def fetch_league_data(self, league_id: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        cache_file = os.path.join(CACHE_DIR, f"{league_id}_flashscore.json")
        if not force_refresh and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data and len(data) > 0:
                        self.cache[league_id] = data
                        return data
            except Exception:
                pass

        config = LEAGUES_CONFIG.get(league_id)
        if not config:
            return []

        all_matches = []
        # 1. Fetch live results from Flashscore
        try:
            r = requests.get(config["results_url"], headers=self.headers, timeout=8)
            feed_match = re.search(r"cjs\.initialFeeds\['(?:results|summary-results)'\]\s*=\s*\{\s*data:\s*`([^`]+)`", r.text)
            if not feed_match:
                feed_match = re.search(r'cjs\.initialFeeds\["(?:results|summary-results)"\]\s*=\s*\{\s*data:\s*`([^`]+)`', r.text)
            if feed_match:
                matches = self.parse_feed_blocks(feed_match.group(1), league_id)
                all_matches.extend(matches)
        except Exception as e:
            print(f"Error scraping Flashscore results for {league_id}: {e}")

        # 2. Also fetch standings page feeds
        try:
            r = requests.get(config["standings_url"], headers=self.headers, timeout=8)
            feed_match = re.search(r"cjs\.initialFeeds\['(?:results|summary-results)'\]\s*=\s*\{\s*data:\s*`([^`]+)`", r.text)
            if feed_match:
                matches = self.parse_feed_blocks(feed_match.group(1), league_id)
                # deduplicate by date + home + away
                existing_keys = {f"{m['date']}_{m['home_team']}_{m['away_team']}" for m in all_matches}
                for m in matches:
                    key = f"{m['date']}_{m['home_team']}_{m['away_team']}"
                    if key not in existing_keys:
                        all_matches.append(m)
                        existing_keys.add(key)
        except Exception as e:
            print(f"Error scraping Flashscore standings for {league_id}: {e}")

        all_matches.sort(key=lambda m: m["timestamp"], reverse=True)

        if all_matches:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(all_matches, f, indent=2)

        self.cache[league_id] = all_matches
        return all_matches

    def get_teams(self, league_id: str) -> List[str]:
        matches = self.fetch_league_data(league_id)
        teams = set()
        for m in matches:
            teams.add(m["home_team"])
            teams.add(m["away_team"])
        
        # If matches are few, fetch from fixtures feed
        if len(teams) < 18:
            config = LEAGUES_CONFIG.get(league_id)
            if config:
                try:
                    r = requests.get(config["standings_url"], headers=self.headers, timeout=6)
                    feed_match = re.search(r"cjs\.initialFeeds\['fixtures'\]\s*=\s*\{\s*data:\s*`([^`]+)`", r.text)
                    if feed_match:
                        raw_teams = set(re.findall(r'¬(?:AE|AF)÷([^¬]+)', feed_match.group(1)))
                        teams.update(raw_teams)
                except Exception:
                    pass

        return sorted(list(teams))

    def get_over_under_table(self, league_id: str, threshold: float = 2.5, venue: str = "overall") -> List[Dict[str, Any]]:
        """
        Builds the exact Over/Under table shown in Screenshot 1.
        Columns: Rank (#), Team, MP, Over (O), Under (U), Goals (G: GF:GA), Goals/Match (G/M), Last 5 Form (+/-)
        """
        matches = self.fetch_league_data(league_id)
        teams = self.get_teams(league_id)
        table = []

        for team in teams:
            team_matches = []
            for m in matches:
                is_home = (m["home_team"].lower() == team.lower())
                is_away = (m["away_team"].lower() == team.lower())
                if not (is_home or is_away):
                    continue
                if venue == "home" and not is_home:
                    continue
                if venue == "away" and not is_away:
                    continue
                
                gf = m["ft_home_goals"] if is_home else m["ft_away_goals"]
                ga = m["ft_away_goals"] if is_home else m["ft_home_goals"]
                tot = m["total_goals"]
                is_over = (tot > threshold)
                team_matches.append({
                    "date": m["date"],
                    "gf": gf,
                    "ga": ga,
                    "total": tot,
                    "is_over": is_over
                })

            mp = len(team_matches)
            over_count = sum(1 for m in team_matches if m["is_over"])
            under_count = mp - over_count
            total_gf = sum(m["gf"] for m in team_matches)
            total_ga = sum(m["ga"] for m in team_matches)
            g_m = round((total_gf + total_ga) / mp, 1) if mp > 0 else 0.0

            # Last 5 form badges (+ for Over, - for Under)
            last_5 = []
            for m in team_matches[:5]:
                last_5.append("+" if m["is_over"] else "-")
            while len(last_5) < 5:
                last_5.append("?")

            table.append({
                "team": team,
                "mp": mp,
                "over": over_count,
                "under": under_count,
                "goals_str": f"{total_gf}:{total_ga}",
                "total_goals": total_gf + total_ga,
                "gm": g_m,
                "last_5": last_5,
                "over_pct": round(over_count / mp * 100, 1) if mp > 0 else 0.0
            })

        # Sort table: by Over desc, then GM desc, then Total Goals desc
        table.sort(key=lambda x: (x["over"], x["gm"], x["total_goals"]), reverse=True)
        for idx, row in enumerate(table, 1):
            row["rank"] = idx

        return table

    def get_ht_ft_table(self, league_id: str, venue: str = "overall") -> List[Dict[str, Any]]:
        """
        Builds the exact HT/FT table shown in Screenshot 2.
        Columns: Rank (#), Team, MP, W/W, W/D, W/L, D/W, D/D, D/L, L/W, L/D, L/L, PTS
        """
        matches = self.fetch_league_data(league_id)
        teams = self.get_teams(league_id)
        table = []

        patterns = ["W/W", "W/D", "W/L", "D/W", "D/D", "D/L", "L/W", "L/D", "L/L"]

        for team in teams:
            counts = {p: 0 for p in patterns}
            pts = 0
            mp = 0

            for m in matches:
                is_home = (m["home_team"].lower() == team.lower())
                is_away = (m["away_team"].lower() == team.lower())
                if not (is_home or is_away):
                    continue
                if venue == "home" and not is_home:
                    continue
                if venue == "away" and not is_away:
                    continue

                mp += 1
                h_h = m["ht_home_goals"] if is_home else m["ht_away_goals"]
                h_a = m["ht_away_goals"] if is_home else m["ht_home_goals"]
                f_h = m["ft_home_goals"] if is_home else m["ft_away_goals"]
                f_a = m["ft_away_goals"] if is_home else m["ft_home_goals"]

                def get_outcome(g1, g2):
                    if g1 > g2: return "W"
                    if g1 == g2: return "D"
                    return "L"

                pat = f"{get_outcome(h_h, h_a)}/{get_outcome(f_h, f_a)}"
                if pat in counts:
                    counts[pat] += 1

                if f_h > f_a:
                    pts += 3
                elif f_h == f_a:
                    pts += 1

            row = {
                "team": team,
                "mp": mp,
                "pts": pts,
                **counts
            }
            table.append(row)

        table.sort(key=lambda x: (x["pts"], x["W/W"], x["D/W"]), reverse=True)
        for idx, row in enumerate(table, 1):
            row["rank"] = idx

        return table

    def compare_teams_simple(self, league_id: str, team_a: str, team_b: str, last_n: int = 10) -> Dict[str, Any]:
        """
        Clean, simple 2-team comparison data without complex diagrams:
        - 1st Half Goals Scored & Conceded
        - 2nd Half Goals Scored & Conceded
        - Full Time Goals Scored & Conceded
        - Home vs Away splits
        - Expected Goals (xG)
        - Clean list of last N domestic matches
        """
        matches = self.fetch_league_data(league_id)

        def get_team_stats(team_name: str):
            all_m = []
            home_m = []
            away_m = []

            for m in matches:
                is_home = (m["home_team"].lower() == team_name.lower())
                is_away = (m["away_team"].lower() == team_name.lower())
                if not (is_home or is_away):
                    continue

                scored_ft = m["ft_home_goals"] if is_home else m["ft_away_goals"]
                conceded_ft = m["ft_away_goals"] if is_home else m["ft_home_goals"]
                scored_ht = m["ht_home_goals"] if is_home else m["ht_away_goals"]
                conceded_ht = m["ht_away_goals"] if is_home else m["ht_home_goals"]
                scored_2h = m["2h_home_goals"] if is_home else m["2h_away_goals"]
                conceded_2h = m["2h_away_goals"] if is_home else m["home_xg"]
                conceded_2h_real = m["2h_away_goals"] if is_home else m["2h_home_goals"]
                
                xg_for = m["home_xg"] if is_home else m["away_xg"]
                xg_against = m["away_xg"] if is_home else m["home_xg"]

                res = "W" if scored_ft > conceded_ft else ("D" if scored_ft == conceded_ft else "L")
                opp = m["away_team"] if is_home else m["home_team"]

                item = {
                    "date": m["date"],
                    "opponent": opp,
                    "venue": "Home" if is_home else "Away",
                    "result": res,
                    "score_ft": f"{scored_ft}:{conceded_ft}",
                    "score_ht": f"{scored_ht}:{conceded_ht}",
                    "score_2h": f"{scored_2h}:{conceded_2h_real}",
                    "gf": scored_ft,
                    "ga": conceded_ft,
                    "gf_ht": scored_ht,
                    "ga_ht": conceded_ht,
                    "gf_2h": scored_2h,
                    "ga_2h": conceded_2h_real,
                    "xg_for": xg_for,
                    "xg_against": xg_against
                }
                all_m.append(item)
                if is_home: home_m.append(item)
                if is_away: away_m.append(item)

            def aggregate(sub):
                count = len(sub)
                if count == 0:
                    return {
                        "count": 0, "avg_gf_ft": 0, "avg_ga_ft": 0,
                        "avg_gf_ht": 0, "avg_ga_ht": 0,
                        "avg_gf_2h": 0, "avg_ga_2h": 0,
                        "avg_xg_for": 0, "avg_xg_against": 0,
                        "clean_sheet_ht_pct": 0, "clean_sheet_2h_pct": 0, "clean_sheet_ft_pct": 0,
                        "ht_over_0_5_pct": 0, "ft_over_1_5_pct": 0, "ft_over_2_5_pct": 0,
                        "btts_pct": 0
                    }
                gf_ft = sum(x["gf"] for x in sub)
                ga_ft = sum(x["ga"] for x in sub)
                gf_ht = sum(x["gf_ht"] for x in sub)
                ga_ht = sum(x["ga_ht"] for x in sub)
                gf_2h = sum(x["gf_2h"] for x in sub)
                ga_2h = sum(x["ga_2h"] for x in sub)
                xg_f = sum(x["xg_for"] for x in sub)
                xg_a = sum(x["xg_against"] for x in sub)

                cs_ht = sum(1 for x in sub if x["ga_ht"] == 0)
                cs_2h = sum(1 for x in sub if x["ga_2h"] == 0)
                cs_ft = sum(1 for x in sub if x["ga"] == 0)

                ht_o05 = sum(1 for x in sub if (x["gf_ht"] + x["ga_ht"]) > 0.5)
                ft_o15 = sum(1 for x in sub if (x["gf"] + x["ga"]) > 1.5)
                ft_o25 = sum(1 for x in sub if (x["gf"] + x["ga"]) > 2.5)
                btts = sum(1 for x in sub if x["gf"] > 0 and x["ga"] > 0)

                return {
                    "count": count,
                    "avg_gf_ft": round(gf_ft / count, 2),
                    "avg_ga_ft": round(ga_ft / count, 2),
                    "avg_gf_ht": round(gf_ht / count, 2),
                    "avg_ga_ht": round(ga_ht / count, 2),
                    "avg_gf_2h": round(gf_2h / count, 2),
                    "avg_ga_2h": round(ga_2h / count, 2),
                    "avg_xg_for": round(xg_f / count, 2),
                    "avg_xg_against": round(xg_a / count, 2),
                    "clean_sheet_ht_pct": round(cs_ht / count * 100, 1),
                    "clean_sheet_2h_pct": round(cs_2h / count * 100, 1),
                    "clean_sheet_ft_pct": round(cs_ft / count * 100, 1),
                    "ht_over_0_5_pct": round(ht_o05 / count * 100, 1),
                    "ft_over_1_5_pct": round(ft_o15 / count * 100, 1),
                    "ft_over_2_5_pct": round(ft_o25 / count * 100, 1),
                    "btts_pct": round(btts / count * 100, 1)
                }

            return {
                "team": team_name,
                "overall": aggregate(all_m[:last_n]),
                "home": aggregate(home_m[:last_n]),
                "away": aggregate(away_m[:last_n]),
                "matches": all_m[:last_n]
            }

        return {
            "league_id": league_id,
            "team_a": get_team_stats(team_a),
            "team_b": get_team_stats(team_b)
        }

scraper = FlashscoreScraper()
