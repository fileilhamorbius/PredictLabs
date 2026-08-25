import math
from typing import Dict, List, Any, Tuple

def poisson_pmf(k: int, lamb: float) -> float:
    """Computes Poisson Probability Mass Function P(X = k; lambda)."""
    if lamb <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)

def dixon_coles_tau(x: int, y: int, lambda_h: float, lambda_a: float, rho: float = -0.12) -> float:
    """
    Dixon and Coles (1997) low-score correlation adjustment factor tau(x, y).
    Modifies independent Poisson probabilities for (0,0), (1,0), (0,1), and (1,1).
    """
    if x == 0 and y == 0:
        return max(0.0, 1.0 - (lambda_h * lambda_a * rho))
    elif x == 1 and y == 0:
        return max(0.0, 1.0 + (lambda_a * rho))
    elif x == 0 and y == 1:
        return max(0.0, 1.0 + (lambda_h * rho))
    elif x == 1 and y == 1:
        return max(0.0, 1.0 - rho)
    else:
        return 1.0

def calculate_dixon_coles_total_pmf(lambda_h: float, lambda_a: float, max_goals: int = 15, rho: float = -0.12) -> List[float]:
    """
    Calculates the exact total match goal PMF P(Total = k) using the bivariate Dixon-Coles model.
    P(Total = k) = sum_{x+y=k} P(X=x, Y=y; lambda_h, lambda_a, rho)
    """
    p_h = [poisson_pmf(x, lambda_h) for x in range(max_goals + 1)]
    p_a = [poisson_pmf(y, lambda_a) for y in range(max_goals + 1)]

    total_pmf = [0.0] * (max_goals + 1)
    for x in range(max_goals + 1):
        for y in range(max_goals + 1):
            if x + y <= max_goals:
                tau = dixon_coles_tau(x, y, lambda_h, lambda_a, rho)
                joint_p = tau * p_h[x] * p_a[y]
                total_pmf[x + y] += joint_p

    s = sum(total_pmf)
    if s > 0:
        total_pmf = [p / s for p in total_pmf]

    return total_pmf

def calculate_asian_over_under_prob(line: float, pmf_or_lambda: Any) -> Dict[str, Any]:
    """
    Computes Asian Handicap Over/Under probabilities for both:
    1. Single Bet Confidence (Pure Win Score)
    2. Mix Parlay Safety Index (Anti-Gugur Survival Rate = 100% - P(Loss Full))
    """
    if isinstance(pmf_or_lambda, list):
        pmf = pmf_or_lambda
        if len(pmf) < 20:
            pmf = pmf + [0.0] * (20 - len(pmf))
    else:
        lamb = float(pmf_or_lambda)
        pmf = [poisson_pmf(k, lamb) for k in range(20)]

    base_n = int(math.floor(line))
    decimal_part = round(line - base_n, 2)
    max_k = len(pmf)

    if decimal_part == 0.25:
        # Asian Quarter Line N.25 (e.g. 0.25, 1.25, 2.25, 3.25, 4.25, 5.25)
        p_over_win_full = sum(pmf[k] for k in range(base_n + 1, max_k))
        p_over_win_half = 0.0
        p_over_loss_half = pmf[base_n] if base_n < max_k else 0.0
        p_over_loss_full = sum(pmf[k] for k in range(0, base_n))

        p_under_win_full = p_over_loss_full
        p_under_win_half = p_over_loss_half
        p_under_loss_half = 0.0
        p_under_loss_full = p_over_win_full

    elif decimal_part == 0.75:
        # Asian Three-Quarter Line N.75 (e.g. 0.75, 1.75, 2.75, 3.75, 4.75, 5.75)
        p_over_win_full = sum(pmf[k] for k in range(base_n + 2, max_k))
        p_over_win_half = pmf[base_n + 1] if base_n + 1 < max_k else 0.0
        p_over_loss_half = 0.0
        p_over_loss_full = sum(pmf[k] for k in range(0, base_n + 1))

        p_under_win_full = p_over_loss_full
        p_under_win_half = 0.0
        p_under_loss_half = p_over_win_half
        p_under_loss_full = p_over_win_full

    else:
        # Fallback quarter interpolation
        p_over_win_full = sum(pmf[k] for k in range(math.floor(line) + 1, max_k))
        p_over_win_half = 0.0
        p_over_loss_half = 0.0
        p_over_loss_full = 1.0 - p_over_win_full

        p_under_win_full = p_over_loss_full
        p_under_win_half = 0.0
        p_under_loss_half = 0.0
        p_under_loss_full = p_over_win_full

    score_over = p_over_win_full + (0.5 * p_over_win_half) - (0.5 * p_over_loss_half) - p_over_loss_full
    score_under = p_under_win_full + (0.5 * p_under_win_half) - (0.5 * p_under_loss_half) - p_under_loss_full

    is_over = score_over >= score_under
    line_str = str(line)

    if is_over:
        pick = f"OVER {line_str}"
        # Single Bet confidence
        single_conf_pct = int(round((p_over_win_full + 0.5 * p_over_win_half) * 100))
        # Parlay Safety Rate: 100% - Loss Full
        parlay_safety_pct = int(round((p_over_win_full + p_over_win_half + p_over_loss_half) * 100))
        parlay_loss_pct = round(p_over_loss_full * 100, 1)

        if p_over_win_full >= 0.50:
            outcome_text = "Menang Penuh"
        elif p_over_win_half >= 0.25:
            outcome_text = "Menang Setengah"
        elif p_over_loss_half >= 0.35:
            outcome_text = "Potensi Kalah Setengah"
        else:
            outcome_text = "Menang Penuh"
    else:
        pick = f"UNDER {line_str}"
        # Single Bet confidence
        single_conf_pct = int(round((p_under_win_full + 0.5 * p_under_win_half) * 100))
        # Parlay Safety Rate: 100% - Loss Full
        parlay_safety_pct = int(round((p_under_win_full + p_under_win_half + p_under_loss_half) * 100))
        parlay_loss_pct = round(p_under_loss_full * 100, 1)

        if p_under_win_full >= 0.50:
            outcome_text = "Menang Penuh"
        elif p_under_win_half >= 0.25:
            outcome_text = "Menang Setengah"
        elif p_under_loss_half >= 0.35:
            outcome_text = "Potensi Kalah Setengah"
        else:
            outcome_text = "Menang Penuh"

    single_conf_pct = max(51, min(99, single_conf_pct))
    parlay_safety_pct = max(51, min(99, parlay_safety_pct))

    return {
        "line": line_str,
        "pick": pick,
        "is_over": is_over,
        "conf_pct": single_conf_pct,
        "single_conf_pct": single_conf_pct,
        "parlay_safety_pct": parlay_safety_pct,
        "parlay_loss_pct": parlay_loss_pct,
        "outcome_text": outcome_text,
        "is_high_conf": single_conf_pct >= 85,
        "is_parlay_safe": parlay_safety_pct >= 85,
        "probs": {
            "over_win_full": round(p_over_win_full * 100, 1),
            "over_win_half": round(p_over_win_half * 100, 1),
            "over_loss_half": round(p_over_loss_half * 100, 1),
            "over_loss_full": round(p_over_loss_full * 100, 1),
            "under_win_full": round(p_under_win_full * 100, 1),
            "under_win_half": round(p_under_win_half * 100, 1),
            "under_loss_half": round(p_under_loss_half * 100, 1),
            "under_loss_full": round(p_under_loss_full * 100, 1)
        }
    }

def calculate_statistical_prediction(
    team1_name: str,
    team2_name: str,
    team1_venue_stats: Dict[str, Any],
    team2_venue_stats: Dict[str, Any],
    team1_overall_stats: Dict[str, Any],
    team2_overall_stats: Dict[str, Any],
    team1_rank: int = 1,
    team2_rank: int = 2
) -> Dict[str, Any]:
    t1_v_m = team1_venue_stats.get("metrics", {})
    t2_v_m = team2_venue_stats.get("metrics", {})

    t1_v_gf_ht = t1_v_m.get("goal", {}).get("mean", {}).get("ht", 0.7)
    t1_v_ga_ht = t1_v_m.get("bobol", {}).get("mean", {}).get("ht", 0.3)
    t1_v_xg_ht = t1_v_m.get("xg", {}).get("mean", {}).get("ht", 0.8)

    t2_v_gf_ht = t2_v_m.get("goal", {}).get("mean", {}).get("ht", 0.4)
    t2_v_ga_ht = t2_v_m.get("bobol", {}).get("mean", {}).get("ht", 0.8)
    t2_v_xg_ht = t2_v_m.get("xg", {}).get("mean", {}).get("ht", 0.5)

    # 2HT
    t1_v_gf_2h = t1_v_m.get("goal", {}).get("mean", {}).get("2ht", 1.0)
    t1_v_ga_2h = t1_v_m.get("bobol", {}).get("mean", {}).get("2ht", 0.5)
    t1_v_xg_2h = t1_v_m.get("xg", {}).get("mean", {}).get("2ht", 1.1)

    t2_v_gf_2h = t2_v_m.get("goal", {}).get("mean", {}).get("2ht", 0.5)
    t2_v_ga_2h = t2_v_m.get("bobol", {}).get("mean", {}).get("2ht", 0.9)
    t2_v_xg_2h = t2_v_m.get("xg", {}).get("mean", {}).get("2ht", 0.6)

    # FT
    t1_v_gf_ft = t1_v_m.get("goal", {}).get("mean", {}).get("ft", 1.7)
    t1_v_ga_ft = t1_v_m.get("bobol", {}).get("mean", {}).get("ft", 0.8)
    t1_v_xg_ft = t1_v_m.get("xg", {}).get("mean", {}).get("ft", 1.9)

    t2_v_gf_ft = t2_v_m.get("goal", {}).get("mean", {}).get("ft", 0.9)
    t2_v_ga_ft = t2_v_m.get("bobol", {}).get("mean", {}).get("ft", 1.7)
    t2_v_xg_ft = t2_v_m.get("xg", {}).get("mean", {}).get("ft", 1.1)

    # Shots on Target & Finishing Conversion Rate Estimation
    t1_sot_ft = round(max(2.5, (t1_v_xg_ft * 2.65) + (t1_v_gf_ft * 0.45)), 1)
    t2_sot_ft = round(max(2.0, (t2_v_xg_ft * 2.65) + (t2_v_gf_ft * 0.45)), 1)

    t1_conv_rate = round(t1_v_gf_ft / max(1.0, t1_sot_ft), 2)
    t2_conv_rate = round(t2_v_gf_ft / max(1.0, t2_sot_ft), 2)

    t1_eff_multiplier = 1.0 + min(0.12, max(-0.12, (t1_conv_rate - 0.32) * 0.35))
    t2_eff_multiplier = 1.0 + min(0.12, max(-0.12, (t2_conv_rate - 0.32) * 0.35))

    # Expectancies (Lambda)
    lam_t1_ht = max(0.15, round((0.40 * t1_v_gf_ht + 0.35 * t2_v_ga_ht + 0.25 * t1_v_xg_ht) * t1_eff_multiplier, 2))
    lam_t2_ht = max(0.10, round((0.40 * t2_v_gf_ht + 0.35 * t1_v_ga_ht + 0.25 * t2_v_xg_ht) * t2_eff_multiplier, 2))
    lam_tot_ht = round(lam_t1_ht + lam_t2_ht, 2)

    lam_t1_2h = max(0.20, round((0.40 * t1_v_gf_2h + 0.35 * t2_v_ga_2h + 0.25 * t1_v_xg_2h) * t1_eff_multiplier, 2))
    lam_t2_2h = max(0.15, round((0.40 * t2_v_gf_2h + 0.35 * t1_v_ga_2h + 0.25 * t2_v_xg_2h) * t2_eff_multiplier, 2))
    lam_tot_2h = round(lam_t1_2h + lam_t2_2h, 2)

    lam_t1_ft = max(0.35, round((0.40 * t1_v_gf_ft + 0.35 * t2_v_ga_ft + 0.25 * t1_v_xg_ft) * t1_eff_multiplier, 2))
    lam_t2_ft = max(0.25, round((0.40 * t2_v_gf_ft + 0.35 * t1_v_ga_ft + 0.25 * t2_v_xg_ft) * t2_eff_multiplier, 2))

    rank_diff = team2_rank - team1_rank
    if rank_diff != 0:
        multiplier = 1.0 + (min(10, max(-10, rank_diff)) * 0.015)
        lam_t1_ft = round(lam_t1_ft * multiplier, 2)
        lam_t2_ft = round(lam_t2_ft * (2.0 - multiplier), 2)

    lam_tot_ft = round(lam_t1_ft + lam_t2_ft, 2)

    # Dixon-Coles Bivariate Joint PMF for Total Goals
    ht_total_pmf = calculate_dixon_coles_total_pmf(lam_t1_ht, lam_t2_ht, max_goals=12, rho=-0.12)
    sh_total_pmf = calculate_dixon_coles_total_pmf(lam_t1_2h, lam_t2_2h, max_goals=12, rho=-0.12)
    ft_total_pmf = calculate_dixon_coles_total_pmf(lam_t1_ft, lam_t2_ft, max_goals=18, rho=-0.12)

    # =========================================================================
    # PURE ASIAN QUARTER-LINES ONLY (0.25, 0.75, 1.25, 1.75, 2.25, 2.75, etc.)
    # =========================================================================

    # 1. BABAK 1 (HT) - Pure Asian Lines (0.75 to 3.25)
    ht_asian_lines = [0.75, 1.25, 1.75, 2.25, 2.75, 3.25]
    ht_picks_list = []
    for line in ht_asian_lines:
        p = calculate_asian_over_under_prob(line, ht_total_pmf)
        p["label"] = "Total Laga"
        p["category"] = "match"
        buf = round(line - lam_tot_ht, 2) if not p["is_over"] else round(lam_tot_ht - line, 2)
        p["buffer_goals"] = buf
        ht_picks_list.append(p)

    for line in [0.75, 1.25, 1.75, 2.25]:
        p1 = calculate_asian_over_under_prob(line, lam_t1_ht)
        p1["label"] = team1_name
        p1["category"] = "team1"
        buf1 = round(line - lam_t1_ht, 2) if not p1["is_over"] else round(lam_t1_ht - line, 2)
        p1["buffer_goals"] = buf1
        ht_picks_list.append(p1)

        p2 = calculate_asian_over_under_prob(line, lam_t2_ht)
        p2["label"] = team2_name
        p2["category"] = "team2"
        buf2 = round(line - lam_t2_ht, 2) if not p2["is_over"] else round(lam_t2_ht - line, 2)
        p2["buffer_goals"] = buf2
        ht_picks_list.append(p2)

    ht_picks_list.sort(key=lambda x: x["conf_pct"], reverse=True)
    ht_high_prob = [p for p in ht_picks_list if p["conf_pct"] >= 85]
    ht_high_over = [p for p in ht_high_prob if p["is_over"]]
    ht_high_under = [p for p in ht_high_prob if not p["is_over"]]
    ht_parlay_safe = [p for p in sorted(ht_picks_list, key=lambda x: x["parlay_safety_pct"], reverse=True) if p["parlay_safety_pct"] >= 85]

    # 2. BABAK 2 (2HT) - Pure Asian Lines (0.75 to 4.25)
    sh_asian_lines = [0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75, 4.25]
    sh_picks_list = []
    for line in sh_asian_lines:
        p = calculate_asian_over_under_prob(line, sh_total_pmf)
        p["label"] = "Total Laga"
        p["category"] = "match"
        buf = round(line - lam_tot_2h, 2) if not p["is_over"] else round(lam_tot_2h - line, 2)
        p["buffer_goals"] = buf
        sh_picks_list.append(p)

    for line in [0.75, 1.25, 1.75, 2.25, 2.75]:
        p1 = calculate_asian_over_under_prob(line, lam_t1_2h)
        p1["label"] = team1_name
        p1["category"] = "team1"
        buf1 = round(line - lam_t1_2h, 2) if not p1["is_over"] else round(lam_t1_2h - line, 2)
        p1["buffer_goals"] = buf1
        sh_picks_list.append(p1)

        p2 = calculate_asian_over_under_prob(line, lam_t2_2h)
        p2["label"] = team2_name
        p2["category"] = "team2"
        buf2 = round(line - lam_t2_2h, 2) if not p2["is_over"] else round(lam_t2_2h - line, 2)
        p2["buffer_goals"] = buf2
        sh_picks_list.append(p2)

    sh_picks_list.sort(key=lambda x: x["conf_pct"], reverse=True)
    sh_high_prob = [p for p in sh_picks_list if p["conf_pct"] >= 85]
    sh_high_over = [p for p in sh_high_prob if p["is_over"]]
    sh_high_under = [p for p in sh_high_prob if not p["is_over"]]
    sh_parlay_safe = [p for p in sorted(sh_picks_list, key=lambda x: x["parlay_safety_pct"], reverse=True) if p["parlay_safety_pct"] >= 85]

    # 3. FULL TIME (FT) - Pure Asian Lines (0.75 to 5.75)
    ft_asian_lines = [0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75, 4.25, 4.75, 5.25, 5.75]
    ft_picks_list = []
    for line in ft_asian_lines:
        p = calculate_asian_over_under_prob(line, ft_total_pmf)
        p["label"] = "Total Laga"
        p["category"] = "match"
        buf = round(line - lam_tot_ft, 2) if not p["is_over"] else round(lam_tot_ft - line, 2)
        p["buffer_goals"] = buf
        ft_picks_list.append(p)

    for line in [0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75, 4.25]:
        p1 = calculate_asian_over_under_prob(line, lam_t1_ft)
        p1["label"] = team1_name
        p1["category"] = "team1"
        buf1 = round(line - lam_t1_ft, 2) if not p1["is_over"] else round(lam_t1_ft - line, 2)
        p1["buffer_goals"] = buf1
        ft_picks_list.append(p1)

        p2 = calculate_asian_over_under_prob(line, lam_t2_ft)
        p2["label"] = team2_name
        p2["category"] = "team2"
        buf2 = round(line - lam_t2_ft, 2) if not p2["is_over"] else round(lam_t2_ft - line, 2)
        p2["buffer_goals"] = buf2
        ft_picks_list.append(p2)

    ft_picks_list.sort(key=lambda x: x["conf_pct"], reverse=True)
    ft_high_prob = [p for p in ft_picks_list if p["conf_pct"] >= 85]
    ft_high_over = [p for p in ft_high_prob if p["is_over"]]
    ft_high_under = [p for p in ft_high_prob if not p["is_over"]]
    ft_parlay_safe = [p for p in sorted(ft_picks_list, key=lambda x: x["parlay_safety_pct"], reverse=True) if p["parlay_safety_pct"] >= 85]

    # Overall high-confidence list across all periods
    all_high_confidence = (
        [{"period": "HT", **p} for p in ht_high_prob] +
        [{"period": "2HT", **p} for p in sh_high_prob] +
        [{"period": "FT", **p} for p in ft_high_prob]
    )
    all_high_confidence.sort(key=lambda x: x["conf_pct"], reverse=True)

    t1_desc_eff = "tinggi" if t1_conv_rate >= 0.35 else ("moderat" if t1_conv_rate >= 0.25 else "rendah/boros peluang")
    t2_desc_eff = "tinggi" if t2_conv_rate >= 0.35 else ("moderat" if t2_conv_rate >= 0.25 else "rendah/boros peluang")

    reasons = {
        "ht": (
            f"Babak 1 (HT): Ekspektasi gol gabungan terkalibrasi Dixon-Coles adalah {lam_tot_ht}. "
            f"Terdeteksi {len(ht_high_over)} opsi OVER, {len(ht_high_under)} opsi UNDER, dan {len(ht_parlay_safe)} opsi Aman Parley (Anti-Gugur ≥ 85%). "
            f"Efisiensi serangan {team1_name} ({t1_desc_eff}) dan {team2_name} ({t2_desc_eff}) membentuk pola babak 1."
        ),
        "2ht": (
            f"Babak 2 (2HT): Ekspektasi gol babak kedua berada di {lam_tot_2h}. "
            f"Terdapat {len(sh_high_over)} opsi OVER, {len(sh_high_under)} opsi UNDER, dan {len(sh_parlay_safe)} opsi Aman Parley (Anti-Gugur ≥ 85%). "
            f"Intensitas paruh kedua lebih terbuka seiring dinamika kelelahan fisik pemain."
        ),
        "ft": (
            f"Full Time (FT): Agregat 90 menit menghasilkan total ekspektasi {lam_tot_ft} gol (xG {round(t1_v_xg_ft + t2_v_xg_ft, 2)} | Est. SoT {round(t1_sot_ft + t2_sot_ft, 1)}). "
            f"Tercatat {len(ft_high_over)} opsi OVER, {len(ft_high_under)} opsi UNDER, dan {len(ft_parlay_safe)} opsi Garansi Keselamatan Parley (Anti-Gugur ≥ 85%)."
        )
    }

    return {
        "expectancies": {
            "ht": {"team1": lam_t1_ht, "team2": lam_t2_ht, "total": lam_tot_ht},
            "2ht": {"team1": lam_t1_2h, "team2": lam_t2_2h, "total": lam_tot_2h},
            "ft": {"team1": lam_t1_ft, "team2": lam_t2_ft, "total": lam_tot_ft}
        },
        "shot_efficiency": {
            "team1": {"sot": t1_sot_ft, "conversion_rate": t1_conv_rate, "efficiency": t1_desc_eff},
            "team2": {"sot": t2_sot_ft, "conversion_rate": t2_conv_rate, "efficiency": t2_desc_eff}
        },
        "high_confidence_summary": all_high_confidence,
        "predictions": {
            "ht": {
                "all_picks": ht_picks_list,
                "high_prob": ht_high_prob,
                "high_over": ht_high_over,
                "high_under": ht_high_under,
                "parlay_safe": ht_parlay_safe,
                "match_075": next((p for p in ht_picks_list if "Total Laga > 0.75" in p["label"]), ht_picks_list[0]),
                "match_125": next((p for p in ht_picks_list if "Total Laga > 1.25" in p["label"]), ht_picks_list[0])
            },
            "2ht": {
                "all_picks": sh_picks_list,
                "high_prob": sh_high_prob,
                "high_over": sh_high_over,
                "high_under": sh_high_under,
                "parlay_safe": sh_parlay_safe,
                "match_075": next((p for p in sh_picks_list if "Total Laga > 0.75" in p["label"]), sh_picks_list[0]),
                "match_125": next((p for p in sh_picks_list if "Total Laga > 1.25" in p["label"]), sh_picks_list[0])
            },
            "ft": {
                "all_picks": ft_picks_list,
                "high_prob": ft_high_prob,
                "high_over": ft_high_over,
                "high_under": ft_high_under,
                "parlay_safe": ft_parlay_safe,
                "match_175": next((p for p in ft_picks_list if "Total Laga > 1.75" in p["label"]), ft_picks_list[0]),
                "match_225": next((p for p in ft_picks_list if "Total Laga > 2.25" in p["label"]), ft_picks_list[0]),
                "match_275": next((p for p in ft_picks_list if "Total Laga > 2.75" in p["label"]), ft_picks_list[0]),
                "match_325": next((p for p in ft_picks_list if "Total Laga > 3.25" in p["label"]), ft_picks_list[0])
            }
        },
        "reasoning": reasons
    }
