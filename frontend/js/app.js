/**
 * PredictLabs - Simple Symmetrical Matrix Layout with Clean Labels & Predictions
 * Football Goals & xG Intelligence
 */

const API_BASE = window.location.origin;

let currentLeague = 'epl';
let currentSeason = '2026/2027';
let team1Venue = 'home';
let team2Venue = 'away';
let currentLastN = 10;
let currentScenario = 'venue'; // 'venue' or 'overall'
let currentConfFilter = 'high'; // 'high' (>=85%) or 'all'
let currentBetMode = 'single'; // 'single' or 'parlay'
let teamsList = [];
let predictionData = null;

const ASIAN_OVER_UNDER_KEYS = [
    'o025', 'o075', 'o125', 'o175', 'o225', 'o275',
    'o325', 'o375', 'o425', 'o475', 'o525', 'o575'
];

document.addEventListener('DOMContentLoaded', () => {
    initLeagueTabs();
    initSeasonPills();
    initVenuePills();
    initMatchFilterPills();
    initTeamDropdowns();
    initScenarioToggle();
    initConfToggle();
    initBetModeToggle();
    
    // Initial Load
    loadLeague(currentLeague);
});

// 1. League Navigation
function initLeagueTabs() {
    const pills = document.querySelectorAll('#leagueTabs .league-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            currentLeague = pill.getAttribute('data-league');
            loadLeague(currentLeague);
        });
    });

    const btnSync = document.getElementById('btnSync');
    btnSync.addEventListener('click', async () => {
        btnSync.classList.add('loading');
        btnSync.disabled = true;
        const originalText = btnSync.innerHTML;
        btnSync.innerHTML = '<i class="fa-solid fa-rotate"></i> Syncing All Leagues...';
        try {
            await fetch(`${API_BASE}/api/refresh?league=all`, { method: 'POST' });
            await loadLeague(currentLeague);
        } catch (e) {
            console.error('Sync error:', e);
        } finally {
            btnSync.innerHTML = originalText;
            btnSync.classList.remove('loading');
            btnSync.disabled = false;
        }
    });
}

// 2. Season / Tahun Kompetisi Filter
function initSeasonPills() {
    const seasonBtns = document.querySelectorAll('#seasonPills .season-btn');
    seasonBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            seasonBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSeason = btn.getAttribute('data-season');
            loadLeague(currentLeague);
        });
    });
}

// 3. Venue Pills (Home / Away / Overall for Team 1 & Team 2)
function initVenuePills() {
    const t1Pills = document.querySelectorAll('#team1VenuePills .venue-btn');
    t1Pills.forEach(btn => {
        btn.addEventListener('click', () => {
            t1Pills.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            team1Venue = btn.getAttribute('data-venue');
            updateMatrix();
        });
    });

    const t2Pills = document.querySelectorAll('#team2VenuePills .venue-btn');
    t2Pills.forEach(btn => {
        btn.addEventListener('click', () => {
            t2Pills.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            team2Venue = btn.getAttribute('data-venue');
            updateMatrix();
        });
    });
}

// 4. Match Range Filter (Last 3, Last 5, Last 10)
function initMatchFilterPills() {
    const mPills = document.querySelectorAll('#matchFilterPills .match-btn');
    mPills.forEach(btn => {
        btn.addEventListener('click', () => {
            mPills.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentLastN = parseInt(btn.getAttribute('data-n'));
            
            const badge = document.getElementById('predActiveMatchBadge');
            if (badge) {
                badge.textContent = `Basis: Last ${currentLastN} Matches`;
            }
            
            updateMatrix();
        });
    });
}

// 5. Team Selectors
function initTeamDropdowns() {
    const s1 = document.getElementById('team1Select');
    const s2 = document.getElementById('team2Select');

    s1.addEventListener('change', updateMatrix);
    s2.addEventListener('change', updateMatrix);
}

// 6. Scenario Toggle for Predictions
function initScenarioToggle() {
    const sBtns = document.querySelectorAll('#scenarioToggle .scenario-btn');
    sBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            sBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentScenario = btn.getAttribute('data-scenario');
            renderPredictions();
        });
    });
}

// 7. Confidence Filter Toggle (>= 85% vs All)
function initConfToggle() {
    const cBtns = document.querySelectorAll('#confToggle .conf-btn');
    cBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            cBtns.forEach(b => {
                b.classList.remove('active');
                b.style.background = 'transparent';
                b.style.borderColor = 'transparent';
                b.style.color = 'var(--text-secondary)';
            });
            btn.classList.add('active');
            btn.style.background = 'var(--btn-active)';
            btn.style.borderColor = 'var(--accent-cyan)';
            btn.style.color = '#ffffff';

            currentConfFilter = btn.getAttribute('data-filter');
            renderPredictions();
        });
    });
}

// 8. Bet Mode Toggle (Single Bet vs Mix Parlay Safety)
function initBetModeToggle() {
    const bBtns = document.querySelectorAll('#betModeToggle .bet-mode-btn');
    bBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            bBtns.forEach(b => {
                b.classList.remove('active');
                b.style.background = 'transparent';
                b.style.borderColor = 'transparent';
                b.style.color = 'var(--text-secondary)';
            });
            btn.classList.add('active');
            btn.style.background = 'var(--btn-active)';
            btn.style.borderColor = 'var(--accent-cyan)';
            btn.style.color = '#ffffff';

            currentBetMode = btn.getAttribute('data-mode');
            const sub = document.getElementById('predictionSubtitle');
            if (sub) {
                if (currentBetMode === 'parlay') {
                    sub.innerHTML = `🛡️ <strong>Mode Mix Parlay (Anti-Gugur Aktif)</strong>: Menghitung persentase kelangsungan tiket parley (100% - Resiko Kalah Penuh). Menang Setengah atau Kalah Setengah tidak menggagalkan akumulasi tiket!`;
                } else {
                    sub.innerHTML = `🎯 <strong>Mode Single Bet (Win Rate Aktif)</strong>: Perhitungan probabilitas kemenangan murni Pasaran Asia untuk Babak 1 (HT), Babak 2 (2HT), dan Full Time (FT).`;
                }
            }
            renderPredictions();
        });
    });
}

// Master Loader
async function loadLeague(leagueId) {
    try {
        const res = await fetch(`${API_BASE}/api/teams?league=${leagueId}&season=${encodeURIComponent(currentSeason)}`);
        const data = await res.json();
        if (data.status === 'success') {
            teamsList = data.data;
            populateDropdowns(teamsList);
            updateMatrix();
        }
    } catch (e) {
        console.error('Error fetching teams:', e);
    }
}

function populateDropdowns(teams) {
    const s1 = document.getElementById('team1Select');
    const s2 = document.getElementById('team2Select');

    const prev1 = s1.value;
    const prev2 = s2.value;

    s1.innerHTML = '';
    s2.innerHTML = '';

    teams.forEach(t => {
        const opt1 = document.createElement('option');
        opt1.value = t; opt1.textContent = t;
        s1.appendChild(opt1);

        const opt2 = document.createElement('option');
        opt2.value = t; opt2.textContent = t;
        s2.appendChild(opt2);
    });

    if (teams.length >= 2) {
        s1.value = teams.includes(prev1) ? prev1 : teams[0];
        s2.value = teams.includes(prev2) ? prev2 : (teams[1] || teams[0]);
    }
}

// Fetch & Populate Symmetrical Matrix & Clean Predictions
async function updateMatrix() {
    const team1 = document.getElementById('team1Select').value;
    const team2 = document.getElementById('team2Select').value;

    if (!team1 || !team2) return;

    document.getElementById('labelTeam1Mean').textContent = `Mean (${team1})`;
    document.getElementById('labelTeam1Med').textContent = `Median (${team1})`;
    document.getElementById('labelTeam2Mean').textContent = `Mean (${team2})`;
    document.getElementById('labelTeam2Med').textContent = `Median (${team2})`;

    const badge = document.getElementById('predActiveMatchBadge');
    if (badge) {
        badge.textContent = `Basis: Last ${currentLastN} Matches`;
    }

    try {
        // 1. Fetch Matrix Comparison Table
        const urlMatrix = `${API_BASE}/api/matrix-compare?league=${currentLeague}&season=${encodeURIComponent(currentSeason)}&team1=${encodeURIComponent(team1)}&venue1=${team1Venue}&team2=${encodeURIComponent(team2)}&venue2=${team2Venue}&last_n=${currentLastN}`;
        const resMatrix = await fetch(urlMatrix);
        const jsonMatrix = await resMatrix.json();

        if (jsonMatrix.status === 'success') {
            renderMatrixData(jsonMatrix.team1.metrics, jsonMatrix.team2.metrics);
        }

        // 2. Fetch Statistical Prediction Engine
        const urlPred = `${API_BASE}/api/predict?league=${currentLeague}&season=${encodeURIComponent(currentSeason)}&team1=${encodeURIComponent(team1)}&team2=${encodeURIComponent(team2)}&last_n=${currentLastN}`;
        const resPred = await fetch(urlPred);
        const jsonPred = await resPred.json();

        if (jsonPred.status === 'success') {
            predictionData = jsonPred.data;
            renderPredictions();
        }
    } catch (e) {
        console.error('Error updating matrix & predictions:', e);
    }
}

function renderMatrixData(m1, m2) {
    const allMetrics = ['goal', 'xg', 'bobol', 'xga', ...ASIAN_OVER_UNDER_KEYS];

    allMetrics.forEach(k => {
        const row = document.querySelector(`tr[data-metric="${k}"]`);
        if (!row) return;

        const isAsian = ASIAN_OVER_UNDER_KEYS.includes(k);
        const data1 = m1[k] || { mean: { ht: 0, '2ht': 0, ft: 0 }, median: { ht: 0, '2ht': 0, ft: 0 } };
        const data2 = m2[k] || { mean: { ht: 0, '2ht': 0, ft: 0 }, median: { ht: 0, '2ht': 0, ft: 0 } };

        // Team 1 Mean
        row.querySelector('.t1-mean-ht').innerHTML = formatCell(data1.mean.ht, isAsian);
        row.querySelector('.t1-mean-2ht').innerHTML = formatCell(data1.mean['2ht'], isAsian);
        row.querySelector('.t1-mean-ft').innerHTML = formatCell(data1.mean.ft, isAsian);

        // Team 1 Median
        row.querySelector('.t1-med-ht').innerHTML = formatCell(data1.median.ht, isAsian);
        row.querySelector('.t1-med-2ht').innerHTML = formatCell(data1.median['2ht'], isAsian);
        row.querySelector('.t1-med-ft').innerHTML = formatCell(data1.median.ft, isAsian);

        // Team 2 Mean
        row.querySelector('.t2-mean-ht').innerHTML = formatCell(data2.mean.ht, isAsian);
        row.querySelector('.t2-mean-2ht').innerHTML = formatCell(data2.mean['2ht'], isAsian);
        row.querySelector('.t2-mean-ft').innerHTML = formatCell(data2.mean.ft, isAsian);

        // Team 2 Median
        row.querySelector('.t2-med-ht').innerHTML = formatCell(data2.median.ht, isAsian);
        row.querySelector('.t2-med-2ht').innerHTML = formatCell(data2.median['2ht'], isAsian);
        row.querySelector('.t2-med-ft').innerHTML = formatCell(data2.median.ft, isAsian);
    });
}

function formatCell(val, isAsian) {
    if (val === undefined || val === null) return '-';
    
    if (isAsian) {
        if (val >= 0.70) {
            return `<span class="badge-check" title="Over Menang Penuh (${val})"><i class="fa-solid fa-check"></i></span>`;
        } else if (val >= 0.50) {
            return `<span class="badge-half-win" title="Over Menang/Kalah Setengah Split (${val})">½</span>`;
        } else {
            return `<span class="badge-minus" title="Under / Kalah Penuh (${val})"><i class="fa-solid fa-minus"></i></span>`;
        }
    }
    return val;
}

// Render Prediction Cards with Support for Single Bet & Mix Parlay Modes
function renderPredictions() {
    if (!predictionData) return;

    const predObj = currentScenario === 'venue' ? predictionData.venue_prediction : predictionData.overall_prediction;
    const team1 = predictionData.team1.name;
    const team2 = predictionData.team2.name;

    function createPickItemHTML(pickData) {
        const isParlayMode = currentBetMode === 'parlay';
        const confValue = isParlayMode ? pickData.parlay_safety_pct : pickData.single_conf_pct;
        const isHigh = confValue >= 85;

        let badgeTag = '';
        if (isParlayMode) {
            badgeTag = isHigh ? `<span class="badge-parlay-tag"><i class="fa-solid fa-shield-halved"></i> Anti-Gugur ${confValue}%</span>` : '';
        } else {
            badgeTag = isHigh ? `<span class="badge-high-conf-tag"><i class="fa-solid fa-fire"></i> ≥85%</span>` : '';
        }

        let subRowHTML = '';
        if (isParlayMode) {
            subRowHTML = `
                <div class="pick-sub-row" style="display: flex; justify-content: space-between; align-items: center; font-size: 0.74rem;">
                    <span class="scenario-tag" style="color: #38bdf8;"><i class="fa-solid fa-shield"></i> Aman Parley (Resiko Gugur: ${pickData.parlay_loss_pct}%)</span>
                    <span style="color: var(--text-dim);">${pickData.outcome_text}</span>
                </div>
            `;
        } else {
            subRowHTML = `
                <div class="pick-sub-row">
                    <span class="scenario-tag"><i class="fa-solid fa-shield-halved"></i> ${pickData.outcome_text}</span>
                </div>
            `;
        }

        return `
            <div class="pick-item ${isParlayMode ? (isHigh ? 'parlay-safe' : '') : (isHigh ? 'high-conf' : '')}">
                <div class="pick-main-row">
                    <span class="pick-label">
                        ${pickData.label}
                        ${badgeTag}
                    </span>
                    <div class="pick-result-badge">
                        <span class="${pickData.is_over ? 'badge-pill-over' : 'badge-pill-under'}">${pickData.pick}</span>
                        <span class="pick-conf" style="font-weight: 700; ${isParlayMode ? 'color: #38bdf8;' : (isHigh ? 'color: #22c55e;' : '')}">${confValue}% ${isParlayMode ? '<span style="font-size: 0.7rem; font-weight: normal; color: var(--text-secondary);">Aman</span>' : ''}</span>
                    </div>
                </div>
                ${subRowHTML}
            </div>
        `;
    }

    function renderList(containerId, picksArray, highProbArray, highOverArray, highUnderArray, parlaySafeArray) {
        const container = document.getElementById(containerId);
        if (!container) return;

        let displayPicks = [];
        const isParlayMode = currentBetMode === 'parlay';

        if (isParlayMode) {
            if (currentConfFilter === 'high') {
                displayPicks = (parlaySafeArray && parlaySafeArray.length > 0) ? parlaySafeArray : (picksArray ? picksArray.slice(0, 4) : []);
            } else if (currentConfFilter === 'over') {
                displayPicks = (parlaySafeArray ? parlaySafeArray.filter(p => p.is_over) : []).slice(0, 4);
                if (displayPicks.length === 0 && picksArray) displayPicks = picksArray.filter(p => p.is_over).slice(0, 3);
            } else if (currentConfFilter === 'under') {
                displayPicks = (parlaySafeArray ? parlaySafeArray.filter(p => !p.is_over) : []).slice(0, 4);
                if (displayPicks.length === 0 && picksArray) displayPicks = picksArray.filter(p => !p.is_over).slice(0, 3);
            } else {
                displayPicks = picksArray ? [...picksArray].sort((a, b) => b.parlay_safety_pct - a.parlay_safety_pct) : [];
            }
        } else {
            // Single Bet Mode
            if (currentConfFilter === 'high') {
                displayPicks = (highProbArray && highProbArray.length > 0) ? highProbArray : (picksArray ? picksArray.slice(0, 4) : []);
            } else if (currentConfFilter === 'over') {
                displayPicks = (highOverArray && highOverArray.length > 0) ? highOverArray : (picksArray ? picksArray.filter(p => p.is_over).slice(0, 3) : []);
            } else if (currentConfFilter === 'under') {
                displayPicks = (highUnderArray && highUnderArray.length > 0) ? highUnderArray : (picksArray ? picksArray.filter(p => !p.is_over).slice(0, 3) : []);
            } else {
                displayPicks = picksArray || [];
            }
        }

        if (displayPicks.length === 0) {
            const filterName = currentConfFilter === 'over' ? 'OVER' : (currentConfFilter === 'under' ? 'UNDER' : '');
            container.innerHTML = `<div style="color: var(--text-dim); font-size: 0.8rem; text-align: center; padding: 16px;">Tidak ada opsi ${filterName} di atas 85% untuk babak ini.</div>`;
            return;
        }

        container.innerHTML = displayPicks.map(p => createPickItemHTML(p)).join('');
    }

    // 1. Babak 1 (HT)
    const htExp = predObj.expectancies.ht;
    document.getElementById('htExpBadge').textContent = `λ Match: ${htExp.total} gol (xG)`;

    const htP = predObj.predictions.ht;
    renderList('htPicksList', htP.all_picks, htP.high_prob, htP.high_over, htP.high_under, htP.parlay_safe);
    document.getElementById('htReasoningText').textContent = predObj.reasoning.ht;

    // 2. Babak 2 (2HT)
    const shExp = predObj.expectancies['2ht'];
    document.getElementById('shExpBadge').textContent = `λ Match: ${shExp.total} gol (xG)`;

    const shP = predObj.predictions['2ht'];
    renderList('shPicksList', shP.all_picks, shP.high_prob, shP.high_over, shP.high_under, shP.parlay_safe);
    document.getElementById('shReasoningText').textContent = predObj.reasoning['2ht'];

    // 3. Full Time (FT)
    const ftExp = predObj.expectancies.ft;
    document.getElementById('ftExpBadge').textContent = `λ Match: ${ftExp.total} gol (xG)`;

    const ftP = predObj.predictions.ft;
    renderList('ftPicksList', ftP.all_picks, ftP.high_prob, ftP.high_over, ftP.high_under, ftP.parlay_safe);
    document.getElementById('ftReasoningText').textContent = predObj.reasoning.ft;
}



