import os
import json
import math
import statistics
import datetime
import requests
from typing import Dict, List, Any, Optional
from backend.statistical_predictor import calculate_statistical_prediction

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

SEASONS = [
    {"id": "2026/2027", "name": "2026/2027 (Musim Ini)"},
    {"id": "2025/2026", "name": "2025/2026 (1 Musim Lalu)"}
]

LEAGUES_CONFIG = {
    "epl": {
        "id": "epl",
        "name": "Premier League",
        "country": "Inggris",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "flashscore_results": "https://www.flashscore.com/football/england/premier-league/results/",
        "flashscore_standings": "https://www.flashscore.com/football/england/premier-league/standings/",
        "archive_url": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/en.1.json"
    },
    "laliga": {
        "id": "laliga",
        "name": "La Liga",
        "country": "Spanyol",
        "flag": "🇪🇸",
        "flashscore_results": "https://www.flashscore.com/football/spain/laliga/results/",
        "flashscore_standings": "https://www.flashscore.com/football/spain/laliga/standings/",
        "archive_url": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/es.1.json"
    },
    "bundesliga": {
        "id": "bundesliga",
        "name": "Bundesliga",
        "country": "Jerman",
        "flag": "🇩🇪",
        "flashscore_results": "https://www.flashscore.com/football/germany/bundesliga/results/",
        "flashscore_standings": "https://www.flashscore.com/football/germany/bundesliga/standings/",
        "archive_url": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/de.1.json"
    },
    "seriea": {
        "id": "seriea",
        "name": "Serie A",
        "country": "Italia",
        "flag": "🇮🇹",
        "flashscore_results": "https://www.flashscore.com/football/italy/serie-a/results/",
        "flashscore_standings": "https://www.flashscore.com/football/italy/serie-a/standings/",
        "archive_url": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/it.1.json"
    },
    "ligue1": {
        "id": "ligue1",
        "name": "Ligue 1",
        "country": "Prancis",
        "flag": "🇫🇷",
        "flashscore_results": "https://www.flashscore.com/football/france/ligue-1/results/",
        "flashscore_standings": "https://www.flashscore.com/football/france/ligue-1/standings/",
        "archive_url": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/fr.1.json"
    },
    "eredivisie": {
        "id": "eredivisie",
        "name": "Eredivisie",
        "country": "Belanda",
        "flag": "🇳🇱",
        "flashscore_results": "https://www.flashscore.com/football/netherlands/eredivisie/results/",
        "flashscore_standings": "https://www.flashscore.com/football/netherlands/eredivisie/standings/",
        "archive_url": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/nl.1.json"
    }
}

class PredictLabsEngine:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-fsign": "SW9D1eZo"
        }
        self.cache: Dict[str, List[Dict[str, Any]]] = {}

    def parse_flashscore_feed(self, raw_feed: str, league_id: str, season: str = "2026/2027") -> List[Dict[str, Any]]:
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

                    sh_h = max(0, f_h - h_h)
                    sh_a = max(0, f_a - h_a)

                    home_xg = round(max(0.2, (f_h * 0.72) + (sh_h * 0.25) + 0.42), 2)
                    away_xg = round(max(0.15, (f_a * 0.72) + (sh_a * 0.25) + 0.32), 2)
                    home_xg_ht = round(home_xg * 0.44, 2)
                    away_xg_ht = round(away_xg * 0.44, 2)
                    home_xg_2h = round(home_xg - home_xg_ht, 2)
                    away_xg_2h = round(away_xg - away_xg_ht, 2)

                    matches.append({
                        "league_id": league_id,
                        "season": season,
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
                        "home_xg_ht": home_xg_ht,
                        "away_xg_ht": away_xg_ht,
                        "home_xg_2h": home_xg_2h,
                        "away_xg_2h": away_xg_2h,
                        "source": "flashscore"
                    })
                except Exception:
                    continue
        return matches

    def load_league_matches(self, league_id: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        if not force_refresh and league_id in self.cache and len(self.cache[league_id]) > 0:
            return self.cache[league_id]

        cache_file = os.path.join(CACHE_DIR, f"{league_id}_combined.json")
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
        try:
            r = requests.get(config["flashscore_results"], headers=self.headers, timeout=5)
            import re
            feed_match = re.search(r"cjs\.initialFeeds\['(?:results|summary-results)'\]\s*=\s*\{\s*data:\s*`([^`]+)`", r.text)
            if not feed_match:
                feed_match = re.search(r'cjs\.initialFeeds\["(?:results|summary-results)"\]\s*=\s*\{\s*data:\s*`([^`]+)`', r.text)
            if feed_match:
                fs_matches = self.parse_flashscore_feed(feed_match.group(1), league_id, season="2026/2027")
                all_matches.extend(fs_matches)
        except Exception as e:
            print(f"Flashscore scrape error for {league_id}: {e}")

        try:
            r = requests.get(config["flashscore_standings"], headers=self.headers, timeout=5)
            import re
            feed_match = re.search(r"cjs\.initialFeeds\['(?:results|summary-results)'\]\s*=\s*\{\s*data:\s*`([^`]+)`", r.text)
            if feed_match:
                fs_matches = self.parse_flashscore_feed(feed_match.group(1), league_id, season="2026/2027")
                existing_keys = {f"{m['season']}_{m['date']}_{m['home_team']}_{m['away_team']}" for m in all_matches}
                for m in fs_matches:
                    k = f"{m['season']}_{m['date']}_{m['home_team']}_{m['away_team']}"
                    if k not in existing_keys:
                        all_matches.append(m)
                        existing_keys.add(k)
        except Exception as e:
            print(f"Flashscore standings error for {league_id}: {e}")

        try:
            r = requests.get(config["archive_url"], headers=self.headers, timeout=5)
            if r.status_code == 200:
                archive_data = r.json().get("matches", [])
                existing_keys = {f"{m['season']}_{m['date']}_{m['home_team']}_{m['away_team']}" for m in all_matches}
                for item in archive_data:
                    score = item.get("score")
                    if not score or "ft" not in score or not score["ft"]:
                        continue
                    ft = score["ft"]
                    ht = score.get("ht", [0, 0]) or [math.floor(ft[0] * 0.45), math.floor(ft[1] * 0.45)]
                    f_h, f_a = int(ft[0]), int(ft[1])
                    h_h, h_a = int(ht[0]), int(ht[1])
                    sh_h, sh_a = max(0, f_h - h_h), max(0, f_a - h_a)

                    h_team = item.get("team1", "").replace(" FC", "").replace(" AFC", "").replace(" CF", "").strip()
                    a_team = item.get("team2", "").replace(" FC", "").replace(" AFC", "").replace(" CF", "").strip()
                    raw_date = item.get("date", "")
                    
                    try:
                        dt = datetime.datetime.strptime(raw_date, "%Y-%m-%d")
                        ts = int(dt.timestamp())
                    except Exception:
                        ts = 0

                    k = f"2025/2026_{raw_date}_{h_team}_{a_team}"
                    if k not in existing_keys:
                        home_xg = round(max(0.2, (f_h * 0.72) + (sh_h * 0.25) + 0.42), 2)
                        away_xg = round(max(0.15, (f_a * 0.72) + (sh_a * 0.25) + 0.32), 2)
                        home_xg_ht = round(home_xg * 0.44, 2)
                        away_xg_ht = round(away_xg * 0.44, 2)
                        home_xg_2h = round(home_xg - home_xg_ht, 2)
                        away_xg_2h = round(away_xg - away_xg_ht, 2)

                        all_matches.append({
                            "league_id": league_id,
                            "season": "2025/2026",
                            "date": raw_date,
                            "timestamp": ts,
                            "home_team": h_team,
                            "away_team": a_team,
                            "ft_home_goals": f_h,
                            "ft_away_goals": f_a,
                            "ht_home_goals": h_h,
                            "ht_away_goals": h_a,
                            "2h_home_goals": sh_h,
                            "2h_away_goals": sh_a,
                            "home_xg": home_xg,
                            "away_xg": away_xg,
                            "home_xg_ht": home_xg_ht,
                            "away_xg_ht": away_xg_ht,
                            "home_xg_2h": home_xg_2h,
                            "away_xg_2h": away_xg_2h,
                            "source": "archive"
                        })
                        existing_keys.add(k)
        except Exception as e:
            print(f"Archive load error for {league_id}: {e}")

        all_matches.sort(key=lambda m: m["timestamp"], reverse=True)

        if all_matches:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(all_matches, f, indent=2)

        self.cache[league_id] = all_matches
        return all_matches

    def _normalize_name(self, name: str) -> str:
        return name.lower().replace(" fc", "").replace(" afc", "").replace(" cf", "").replace("1. ", "").strip()

    def get_teams(self, league_id: str, season: Optional[str] = None) -> List[str]:
        matches = self.load_league_matches(league_id)
        teams = set()
        for m in matches:
            if season and m.get("season") != season:
                continue
            teams.add(m["home_team"])
            teams.add(m["away_team"])

        if (not season or season == "2026/2027") and len(teams) < 18:
            config = LEAGUES_CONFIG.get(league_id)
            if config:
                try:
                    import re
                    r = requests.get(config["flashscore_standings"], headers=self.headers, timeout=5)
                    feed_match = re.search(r"cjs\.initialFeeds\['fixtures'\]\s*=\s*\{\s*data:\s*`([^`]+)`", r.text)
                    if feed_match:
                        raw_teams = set(re.findall(r'¬(?:AE|AF)÷([^¬]+)', feed_match.group(1)))
                        teams.update(raw_teams)
                except Exception:
                    pass

        return sorted(list(teams))

    def get_standings_ranks(self, league_id: str, season: str = "2026/2027") -> Dict[str, int]:
        matches = self.load_league_matches(league_id)
        table = {}
        for m in matches:
            if m.get("season") != season:
                continue
            h, a = m["home_team"], m["away_team"]
            if h not in table: table[h] = {"pts": 0, "gd": 0, "gf": 0}
            if a not in table: table[a] = {"pts": 0, "gd": 0, "gf": 0}

            fh, fa = m["ft_home_goals"], m["ft_away_goals"]
            table[h]["gf"] += fh
            table[a]["gf"] += fa
            table[h]["gd"] += (fh - fa)
            table[a]["gd"] += (fa - fh)

            if fh > fa:
                table[h]["pts"] += 3
            elif fa > fh:
                table[a]["pts"] += 3
            else:
                table[h]["pts"] += 1
                table[a]["pts"] += 1

        sorted_teams = sorted(
            table.keys(),
            key=lambda t: (table[t]["pts"], table[t]["gd"], table[t]["gf"]),
            reverse=True
        )

        ranks = {}
        for idx, t in enumerate(sorted_teams, start=1):
            ranks[self._normalize_name(t)] = idx
        return ranks

    def get_team_matrix_stats(self, league_id: str, team_name: str, venue: str = "overall", last_n: int = 10, season: str = "2026/2027") -> Dict[str, Any]:
        """
        Computes Mean & Median for Goal, xG, Bobol, xGA, and Asian Over/Under lines:
        0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75, 4.25, 4.75, 5.25, 5.75
        """
        matches = self.load_league_matches(league_id)
        norm_target = self._normalize_name(team_name)

        filtered_matches = []
        for m in matches:
            if m.get("season") != season:
                continue

            h_norm = self._normalize_name(m["home_team"])
            a_norm = self._normalize_name(m["away_team"])
            is_home = (norm_target in h_norm or h_norm in norm_target)
            is_away = (norm_target in a_norm or a_norm in norm_target)

            if not (is_home or is_away):
                continue
            if venue == "home" and not is_home:
                continue
            if venue == "away" and not is_away:
                continue

            gf_ft = m["ft_home_goals"] if is_home else m["ft_away_goals"]
            ga_ft = m["ft_away_goals"] if is_home else m["ft_home_goals"]
            gf_ht = m["ht_home_goals"] if is_home else m["ht_away_goals"]
            ga_ht = m["ht_away_goals"] if is_home else m["ht_home_goals"]
            gf_2h = m["2h_home_goals"] if is_home else m["2h_away_goals"]
            ga_2h = m["2h_away_goals"] if is_home else m["2h_home_goals"]

            xg_f_ft = m["home_xg"] if is_home else m["away_xg"]
            xg_a_ft = m["away_xg"] if is_home else m["home_xg"]
            xg_f_ht = m["home_xg_ht"] if is_home else m["away_xg_ht"]
            xg_a_ht = m["away_xg_ht"] if is_home else m["home_xg_ht"]
            xg_f_2h = m["home_xg_2h"] if is_home else m["away_xg_2h"]
            xg_a_2h = m["away_xg_2h"] if is_home else m["home_xg_2h"]

            tot_ht = gf_ht + ga_ht
            tot_2h = gf_2h + ga_2h
            tot_ft = gf_ft + ga_ft

            filtered_matches.append({
                "date": m["date"],
                "opponent": m["away_team"] if is_home else m["home_team"],
                "venue": "Home" if is_home else "Away",
                "gf_ht": gf_ht, "ga_ht": ga_ht, "tot_ht": tot_ht,
                "gf_2h": gf_2h, "ga_2h": ga_2h, "tot_2h": tot_2h,
                "gf_ft": gf_ft, "ga_ft": ga_ft, "tot_ft": tot_ft,
                "xg_f_ht": xg_f_ht, "xg_a_ht": xg_a_ht,
                "xg_f_2h": xg_f_2h, "xg_a_2h": xg_a_2h,
                "xg_f_ft": xg_f_ft, "xg_a_ft": xg_a_ft
            })

            if len(filtered_matches) >= last_n:
                break

        count = len(filtered_matches)
        asian_keys = ["o025", "o075", "o125", "o175", "o225", "o275", "o325", "o375", "o425", "o475", "o525", "o575"]

        if count == 0:
            empty_row = {"mean": {"ht": 0.0, "2ht": 0.0, "ft": 0.0}, "median": {"ht": 0.0, "2ht": 0.0, "ft": 0.0}}
            metrics_dict = {"goal": empty_row, "xg": empty_row, "bobol": empty_row, "xga": empty_row}
            for ak in asian_keys:
                metrics_dict[ak] = empty_row
            return {"team": team_name, "season": season, "venue": venue, "count": 0, "metrics": metrics_dict}

        def calc_row(ht_list, sh_list, ft_list):
            def m_med(lst):
                if not lst: return 0.0, 0.0
                mean_v = round(sum(lst) / len(lst), 2)
                try:
                    med_v = round(statistics.median(lst), 2)
                except Exception:
                    med_v = mean_v
                return mean_v, med_v

            m_ht, med_ht = m_med(ht_list)
            m_sh, med_sh = m_med(sh_list)
            m_ft, med_ft = m_med(ft_list)
            return {
                "mean": {"ht": m_ht, "2ht": m_sh, "ft": m_ft},
                "median": {"ht": med_ht, "2ht": med_sh, "ft": med_ft}
            }

        # 1. Goal
        row_goal = calc_row([x["gf_ht"] for x in filtered_matches], [x["gf_2h"] for x in filtered_matches], [x["gf_ft"] for x in filtered_matches])
        # 2. xG
        row_xg = calc_row([x["xg_f_ht"] for x in filtered_matches], [x["xg_f_2h"] for x in filtered_matches], [x["xg_f_ft"] for x in filtered_matches])
        # 3. Bobol
        row_bobol = calc_row([x["ga_ht"] for x in filtered_matches], [x["ga_2h"] for x in filtered_matches], [x["ga_ft"] for x in filtered_matches])
        # 4. xGA
        row_xga = calc_row([x["xg_a_ht"] for x in filtered_matches], [x["xg_a_2h"] for x in filtered_matches], [x["xg_a_ft"] for x in filtered_matches])

        # Asian Over/Under scoring function for a single match:
        # Returns 1.0 (Win Full), 0.5 (Win Half or Half Loss push equivalent), 0.0 (Loss Full)
        def score_asian_match(goals: int, line: float) -> float:
            base_n = int(math.floor(line))
            dec = round(line - base_n, 2)
            if dec == 0.25:
                if goals > base_n: return 1.0        # Menang Penuh
                elif goals == base_n: return 0.5     # Kalah Setengah / Split
                else: return 0.0                     # Kalah Penuh
            elif dec == 0.75:
                if goals >= base_n + 2: return 1.0   # Menang Penuh
                elif goals == base_n + 1: return 0.75 # Menang Setengah
                else: return 0.0                     # Kalah Penuh
            else:
                return 1.0 if goals > line else 0.0

        def calc_asian_row(line_val: float):
            return calc_row(
                [score_asian_match(x["tot_ht"], line_val) for x in filtered_matches],
                [score_asian_match(x["tot_2h"], line_val) for x in filtered_matches],
                [score_asian_match(x["tot_ft"], line_val) for x in filtered_matches]
            )

        metrics_out = {
            "goal": row_goal,
            "xg": row_xg,
            "bobol": row_bobol,
            "xga": row_xga,
            "o025": calc_asian_row(0.25),
            "o075": calc_asian_row(0.75),
            "o125": calc_asian_row(1.25),
            "o175": calc_asian_row(1.75),
            "o225": calc_asian_row(2.25),
            "o275": calc_asian_row(2.75),
            "o325": calc_asian_row(3.25),
            "o375": calc_asian_row(3.75),
            "o425": calc_asian_row(4.25),
            "o475": calc_asian_row(4.75),
            "o525": calc_asian_row(5.25),
            "o575": calc_asian_row(5.75)
        }

        return {
            "team": team_name,
            "season": season,
            "venue": venue,
            "count": count,
            "metrics": metrics_out
        }

    def get_full_predictions(
        self,
        league_id: str,
        team1: str,
        team2: str,
        season: str = "2026/2027",
        last_n: int = 10
    ) -> Dict[str, Any]:
        t1_venue = self.get_team_matrix_stats(league_id, team1, venue="home", last_n=last_n, season=season)
        t2_venue = self.get_team_matrix_stats(league_id, team2, venue="away", last_n=last_n, season=season)

        t1_overall = self.get_team_matrix_stats(league_id, team1, venue="overall", last_n=last_n, season=season)
        t2_overall = self.get_team_matrix_stats(league_id, team2, venue="overall", last_n=last_n, season=season)

        ranks = self.get_standings_ranks(league_id, season=season)
        r1 = ranks.get(self._normalize_name(team1), 10)
        r2 = ranks.get(self._normalize_name(team2), 10)

        pred_venue = calculate_statistical_prediction(
            team1_name=team1,
            team2_name=team2,
            team1_venue_stats=t1_venue,
            team2_venue_stats=t2_venue,
            team1_overall_stats=t1_overall,
            team2_overall_stats=t2_overall,
            team1_rank=r1,
            team2_rank=r2
        )

        pred_overall = calculate_statistical_prediction(
            team1_name=team1,
            team2_name=team2,
            team1_venue_stats=t1_overall,
            team2_venue_stats=t2_overall,
            team1_overall_stats=t1_overall,
            team2_overall_stats=t2_overall,
            team1_rank=r1,
            team2_rank=r2
        )

        return {
            "team1": {"name": team1, "rank": r1},
            "team2": {"name": team2, "rank": r2},
            "season": season,
            "last_n": last_n,
            "venue_prediction": pred_venue,
            "overall_prediction": pred_overall
        }

engine = PredictLabsEngine()
