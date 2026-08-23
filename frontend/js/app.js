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
        try {
            await fetch(`${API_BASE}/api/refresh?league=${currentLeague}`, { method: 'POST' });
            await loadLeague(currentLeague);
        } catch (e) {
            console.error('Sync error:', e);
        } finally {
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

// Render Prediction Cards with Clean Labels (no redundant "Asia" words)
function renderPredictions() {
    if (!predictionData) return;

    const predObj = currentScenario === 'venue' ? predictionData.venue_prediction : predictionData.overall_prediction;
    const team1 = predictionData.team1.name;
    const team2 = predictionData.team2.name;

    function createPickItemHTML(label, pickData) {
        return `
            <div class="pick-item">
                <div class="pick-main-row">
                    <span class="pick-label">${label}</span>
                    <div class="pick-result-badge">
                        <span class="${pickData.is_over ? 'badge-pill-over' : 'badge-pill-under'}">${pickData.pick}</span>
                        <span class="pick-conf">${pickData.conf_pct}%</span>
                    </div>
                </div>
                <div class="pick-sub-row">
                    <span class="scenario-tag"><i class="fa-solid fa-shield-halved"></i> ${pickData.outcome_text}</span>
                </div>
            </div>
        `;
    }

    // 1. Babak 1 (HT)
    const htExp = predObj.expectancies.ht;
    document.getElementById('htExpBadge').textContent = `λ Match: ${htExp.total} gol (xG)`;

    const htP = predObj.predictions.ht;
    const htList = document.getElementById('htPicksList');
    htList.innerHTML = `
        ${createPickItemHTML('Total Laga > 0.75 HT', htP.match_075)}
        ${createPickItemHTML('Total Laga > 1.25 HT', htP.match_125)}
        ${createPickItemHTML(`${team1} > 0.75 HT`, htP.team1_075)}
        ${createPickItemHTML(`${team2} > 0.75 HT`, htP.team2_075)}
    `;
    document.getElementById('htReasoningText').textContent = predObj.reasoning.ht;

    // 2. Babak 2 (2HT)
    const shExp = predObj.expectancies['2ht'];
    document.getElementById('shExpBadge').textContent = `λ Match: ${shExp.total} gol (xG)`;

    const shP = predObj.predictions['2ht'];
    const shList = document.getElementById('shPicksList');
    shList.innerHTML = `
        ${createPickItemHTML('Total Laga > 0.75 2HT', shP.match_075)}
        ${createPickItemHTML('Total Laga > 1.25 2HT', shP.match_125)}
        ${createPickItemHTML(`${team1} > 0.75 2HT`, shP.team1_075)}
        ${createPickItemHTML(`${team2} > 0.75 2HT`, shP.team2_075)}
    `;
    document.getElementById('shReasoningText').textContent = predObj.reasoning['2ht'];

    // 3. Full Time (FT)
    const ftExp = predObj.expectancies.ft;
    document.getElementById('ftExpBadge').textContent = `λ Match: ${ftExp.total} gol (xG)`;

    const ftP = predObj.predictions.ft;
    const ftList = document.getElementById('ftPicksList');
    ftList.innerHTML = `
        ${createPickItemHTML('Total Laga > 1.75 FT', ftP.match_175)}
        ${createPickItemHTML('Total Laga > 2.25 FT', ftP.match_225)}
        ${createPickItemHTML('Total Laga > 2.75 FT', ftP.match_275)}
        ${createPickItemHTML('Total Laga > 3.25 FT', ftP.match_325)}
        ${createPickItemHTML(`${team1} > 1.25 FT`, ftP.team1_125)}
        ${createPickItemHTML(`${team2} > 0.75 FT`, ftP.team2_075)}
    `;
    document.getElementById('ftReasoningText').textContent = predObj.reasoning.ft;
}
