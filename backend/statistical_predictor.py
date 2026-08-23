import math
from typing import Dict, List, Any, Tuple

def poisson_pmf(k: int, lamb: float) -> float:
    """Computes Poisson Probability Mass Function P(X = k; lambda)."""
    if lamb <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)

def calculate_asian_over_under_prob(line: float, lamb: float) -> Dict[str, Any]:
    """
    Computes Asian Handicap Over/Under probabilities and settlement scenarios:
    Lines: 0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75, 4.25, 4.75, 5.25, 5.75
    """
    pmf = [poisson_pmf(k, lamb) for k in range(16)]
    base_n = int(math.floor(line))
    decimal_part = round(line - base_n, 2)

    if decimal_part == 0.25:
        p_over_win_full = sum(pmf[k] for k in range(base_n + 1, 16))
        p_over_win_half = 0.0
        p_over_loss_half = pmf[base_n] if base_n < 16 else 0.0
        p_over_loss_full = sum(pmf[k] for k in range(0, base_n))

        p_under_win_full = p_over_loss_full
        p_under_win_half = p_over_loss_half
        p_under_loss_half = 0.0
        p_under_loss_full = p_over_win_full

    elif decimal_part == 0.75:
        p_over_win_full = sum(pmf[k] for k in range(base_n + 2, 16))
        p_over_win_half = pmf[base_n + 1] if base_n + 1 < 16 else 0.0
        p_over_loss_half = 0.0
        p_over_loss_full = sum(pmf[k] for k in range(0, base_n + 1))

        p_under_win_full = p_over_loss_full
        p_under_win_half = 0.0
        p_under_loss_half = p_over_win_half
        p_under_loss_full = p_over_win_full

    else:
        p_over_win_full = sum(pmf[k] for k in range(math.floor(line) + 1, 16))
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
        if p_over_win_full >= 0.50:
            outcome_text = "Menang Penuh"
        elif p_over_win_half >= 0.25:
            outcome_text = "Menang Setengah"
        elif p_over_loss_half >= 0.35:
            outcome_text = "Potensi Kalah Setengah"
        else:
            outcome_text = "Menang Penuh"
        conf_pct = int(round((p_over_win_full + 0.5 * p_over_win_half) * 100))
    else:
        pick = f"UNDER {line_str}"
        if p_under_win_full >= 0.50:
            outcome_text = "Menang Penuh"
        elif p_under_win_half >= 0.25:
            outcome_text = "Menang Setengah"
        elif p_under_loss_half >= 0.35:
            outcome_text = "Potensi Kalah Setengah"
        else:
            outcome_text = "Menang Penuh"
        conf_pct = int(round((p_under_win_full + 0.5 * p_under_win_half) * 100))

    conf_pct = max(51, min(99, conf_pct))

    return {
        "line": line_str,
        "pick": pick,
        "is_over": is_over,
        "conf_pct": conf_pct,
        "outcome_text": outcome_text,
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

    # Expectancies (Lambda)
    lam_t1_ht = max(0.15, round(0.45 * t1_v_gf_ht + 0.35 * t2_v_ga_ht + 0.20 * t1_v_xg_ht, 2))
    lam_t2_ht = max(0.10, round(0.45 * t2_v_gf_ht + 0.35 * t1_v_ga_ht + 0.20 * t2_v_xg_ht, 2))
    lam_tot_ht = round(lam_t1_ht + lam_t2_ht, 2)

    lam_t1_2h = max(0.20, round(0.45 * t1_v_gf_2h + 0.35 * t2_v_ga_2h + 0.20 * t1_v_xg_2h, 2))
    lam_t2_2h = max(0.15, round(0.45 * t2_v_gf_2h + 0.35 * t1_v_ga_2h + 0.20 * t2_v_xg_2h, 2))
    lam_tot_2h = round(lam_t1_2h + lam_t2_2h, 2)

    lam_t1_ft = max(0.35, round(0.45 * t1_v_gf_ft + 0.35 * t2_v_ga_ft + 0.20 * t1_v_xg_ft, 2))
    lam_t2_ft = max(0.25, round(0.45 * t2_v_gf_ft + 0.35 * t1_v_ga_ft + 0.20 * t2_v_xg_ft, 2))

    rank_diff = team2_rank - team1_rank
    if rank_diff != 0:
        multiplier = 1.0 + (min(10, max(-10, rank_diff)) * 0.015)
        lam_t1_ft = round(lam_t1_ft * multiplier, 2)
        lam_t2_ft = round(lam_t2_ft * (2.0 - multiplier), 2)

    lam_tot_ft = round(lam_t1_ft + lam_t2_ft, 2)

    # Clean Predictions
    pred_ht_m_075 = calculate_asian_over_under_prob(0.75, lam_tot_ht)
    pred_ht_m_125 = calculate_asian_over_under_prob(1.25, lam_tot_ht)
    pred_ht_t1_075 = calculate_asian_over_under_prob(0.75, lam_t1_ht)
    pred_ht_t2_075 = calculate_asian_over_under_prob(0.75, lam_t2_ht)

    pred_2h_m_075 = calculate_asian_over_under_prob(0.75, lam_tot_2h)
    pred_2h_m_125 = calculate_asian_over_under_prob(1.25, lam_tot_2h)
    pred_2h_t1_075 = calculate_asian_over_under_prob(0.75, lam_t1_2h)
    pred_2h_t2_075 = calculate_asian_over_under_prob(0.75, lam_t2_2h)

    pred_ft_m_175 = calculate_asian_over_under_prob(1.75, lam_tot_ft)
    pred_ft_m_225 = calculate_asian_over_under_prob(2.25, lam_tot_ft)
    pred_ft_m_275 = calculate_asian_over_under_prob(2.75, lam_tot_ft)
    pred_ft_m_325 = calculate_asian_over_under_prob(3.25, lam_tot_ft)
    pred_ft_t1_125 = calculate_asian_over_under_prob(1.25, lam_t1_ft)
    pred_ft_t1_175 = calculate_asian_over_under_prob(1.75, lam_t1_ft)
    pred_ft_t2_075 = calculate_asian_over_under_prob(0.75, lam_t2_ft)
    pred_ft_t2_125 = calculate_asian_over_under_prob(1.25, lam_t2_ft)

    reasons = {
        "ht": (
            f"Di Babak 1 (HT), total ekspektasi gol adalah {lam_tot_ht}. "
            f"Pada garis 0.75 HT ({pred_ht_m_075['pick']}), sistem memproyeksikan {pred_ht_m_075['outcome_text']} "
            f"dengan keyakinan {pred_ht_m_075['conf_pct']}%."
        ),
        "2ht": (
            f"Di Babak 2 (2HT), ekspektasi gol berada di {lam_tot_2h}. "
            f"Garis 0.75 2HT mengindikasikan opsi {pred_2h_m_075['pick']} ({pred_2h_m_075['outcome_text']}), "
            f"didukung daya serang {team1_name} ({pred_2h_t1_075['pick']})."
        ),
        "ft": (
            f"Agregat 90 menit (Full Time) menghasilkan total ekspektasi {lam_tot_ft} gol (xG {round(t1_v_xg_ft + t2_v_xg_ft, 2)}). "
            f"Pada garis utama 2.25 FT ({pred_ft_m_225['pick']}), model mengindikasikan {pred_ft_m_225['outcome_text']} "
            f"({pred_ft_m_225['conf_pct']}%). Sementara pada garis 2.75 FT diproyeksikan {pred_ft_m_275['pick']} ({pred_ft_m_275['outcome_text']})."
        )
    }

    return {
        "expectancies": {
            "ht": {"team1": lam_t1_ht, "team2": lam_t2_ht, "total": lam_tot_ht},
            "2ht": {"team1": lam_t1_2h, "team2": lam_t2_2h, "total": lam_tot_2h},
            "ft": {"team1": lam_t1_ft, "team2": lam_t2_ft, "total": lam_tot_ft}
        },
        "predictions": {
            "ht": {
                "match_075": pred_ht_m_075,
                "match_125": pred_ht_m_125,
                "team1_075": pred_ht_t1_075,
                "team2_075": pred_ht_t2_075
            },
            "2ht": {
                "match_075": pred_2h_m_075,
                "match_125": pred_2h_m_125,
                "team1_075": pred_2h_t1_075,
                "team2_075": pred_2h_t2_075
            },
            "ft": {
                "match_175": pred_ft_m_175,
                "match_225": pred_ft_m_225,
                "match_275": pred_ft_m_275,
                "match_325": pred_ft_m_325,
                "team1_125": pred_ft_t1_125,
                "team1_175": pred_ft_t1_175,
                "team2_075": pred_ft_t2_075,
                "team2_125": pred_ft_t2_125
            }
        },
        "reasoning": reasons
    }
