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

// Selected User Picks for Comparison (HT, 2HT, FT)
let userSelectedPicks = {
    ht: [],
    '2ht': [],
    ft: []
};

document.addEventListener('DOMContentLoaded', () => {
    initLeagueTabs();
    initSeasonPills();
    initVenuePills();
    initMatchFilterPills();
    initTeamDropdowns();
    initScenarioToggle();
    initConfToggle();
    initBetModeToggle();
    initComparePanelEvents();
    
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
            btnSync.classList.remove('loading');
            btnSync.disabled = false;
            btnSync.innerHTML = originalText;
        }
    });
}

// 2. Season Pills
function initSeasonPills() {
    const pills = document.querySelectorAll('#seasonPills .season-btn');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            currentSeason = pill.getAttribute('data-season');
            loadLeague(currentLeague);
        });
    });
}

// 3. Venue Pills (Home / Away / Overall for Team 1 & Team 2)
function initVenuePills() {
    const t1Pills = document.querySelectorAll('#team1VenuePills .venue-btn');
    t1Pills.forEach(pill => {
        pill.addEventListener('click', () => {
            t1Pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            team1Venue = pill.getAttribute('data-venue');
            updateMatrix();
        });
    });

    const t2Pills = document.querySelectorAll('#team2VenuePills .venue-btn');
    t2Pills.forEach(pill => {
        pill.addEventListener('click', () => {
            t2Pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            team2Venue = pill.getAttribute('data-venue');
            updateMatrix();
        });
    });
}

// 4. Last Matches Filter Pills (3, 5, 10)
function initMatchFilterPills() {
    const mPills = document.querySelectorAll('#matchFilterPills .match-btn');
    mPills.forEach(pill => {
        pill.addEventListener('click', () => {
            mPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            currentLastN = parseInt(pill.getAttribute('data-n'), 10);
            updateMatrix();
        });
    });
}

// 5. Team Dropdowns
function initTeamDropdowns() {
    const s1 = document.getElementById('team1Select');
    const s2 = document.getElementById('team2Select');
    s1.addEventListener('change', updateMatrix);
    s2.addEventListener('change', updateMatrix);
}

// 6. Scenario Toggle for Predictions (Sofascore Segmented Switch)
function initScenarioToggle() {
    const sBtns = document.querySelectorAll('#scenarioToggle .sofa-segment-btn');
    sBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            sBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentScenario = btn.getAttribute('data-scenario');
            renderPredictions();
        });
    });
}

// 7. Quick Filter Chips (Top >=85%, Over, Under, All)
function initConfToggle() {
    const cBtns = document.querySelectorAll('#confToggle .sofa-filter-chip');
    cBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            cBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentConfFilter = btn.getAttribute('data-filter');
            renderPredictions();
        });
    });
}

// 8. Bet Mode Toggle (Single Bet vs Mix Parlay)
function initBetModeToggle() {
    const bBtns = document.querySelectorAll('#betModeToggle .sofa-segment-btn');
    bBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            bBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentBetMode = btn.getAttribute('data-mode');

            const tip = document.getElementById('sofaRibbonTip');
            if (tip) {
                if (currentBetMode === 'parlay') {
                    tip.innerHTML = `<i class="fa-solid fa-shield-halved" style="color: #38bdf8;"></i> <span><strong>Mode Mix Parlay</strong>: Menampilkan % kelangsungan tiket. Menang/Kalah Setengah tidak mematikan parlay!</span>`;
                } else {
                    tip.innerHTML = `<i class="fa-solid fa-circle-info" style="color: #22c55e;"></i> <span><strong>Mode Single Bet</strong>: Menampilkan probabilitas kemenangan murni Pasaran Asia.</span>`;
                }
            }

            renderPredictions();
        });
    });
}

// 9. Comparison Panel & Reset Listener
function initComparePanelEvents() {
    const resetBtn = document.getElementById('compareResetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            userSelectedPicks = { ht: [], '2ht': [], ft: [] };
            document.querySelectorAll('.sofa-pick-card.is-selected').forEach(c => c.classList.remove('is-selected'));
            renderComparePanel();
        });
    }
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

    // Reset user selections on team change
    userSelectedPicks = { ht: [], '2ht': [], ft: [] };
    renderComparePanel();

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

// Render Prediction Cards with Sofascore Pro Sports Layout
function renderPredictions() {
    if (!predictionData) return;

    const predObj = currentScenario === 'venue' ? predictionData.venue_prediction : predictionData.overall_prediction;

    function createPickItemHTML(pickData, period) {
        const isParlayMode = currentBetMode === 'parlay';
        const confValue = isParlayMode ? pickData.parlay_safety_pct : pickData.single_conf_pct;
        const isHigh = confValue >= 85;

        const actionClass = pickData.is_over ? 'badge-pill-over' : 'badge-pill-under';
        const cardStateClass = isParlayMode ? (isHigh ? 'parlay-safe' : '') : (isHigh ? 'high-conf' : '');

        const pickKey = `${period}_${pickData.label}_${pickData.pick}`;
        const isSelected = userSelectedPicks[period] && userSelectedPicks[period].some(p => p.key === pickKey);

        let statusHTML = '';
        if (isParlayMode) {
            statusHTML = `<span class="sofa-status-text parlay-shield"><i class="fa-solid fa-shield-halved"></i> Resiko Gugur: ${pickData.parlay_loss_pct}%</span>`;
        } else {
            let statusIcon = 'fa-circle-check';
            if (pickData.outcome_text === 'Menang Setengah') statusIcon = 'fa-star-half-stroke';
            else if (pickData.outcome_text.includes('Kalah')) statusIcon = 'fa-triangle-exclamation';

            statusHTML = `<span class="sofa-status-text"><i class="fa-solid ${statusIcon}"></i> ${pickData.outcome_text}</span>`;
        }

        return `
            <div class="sofa-pick-card ${cardStateClass} ${isSelected ? 'is-selected' : ''}"
                 data-period="${period}"
                 data-key="${pickKey}"
                 data-label="${pickData.label}"
                 data-pick="${pickData.pick}"
                 data-conf="${confValue}"
                 data-is-over="${pickData.is_over}"
                 data-mode="${isParlayMode ? 'parlay' : 'single'}"
                 data-loss="${pickData.parlay_loss_pct || 0}"
                 data-outcome="${pickData.outcome_text || ''}">
                <div class="sofa-pick-top">
                    <span class="sofa-market-name">${pickData.label}</span>
                    <div class="sofa-metric-badge">
                        <span class="sofa-pct-value">${confValue}%</span>
                        <span class="sofa-pct-sub">${isParlayMode ? 'Aman' : 'Peluang'}</span>
                    </div>
                </div>
                <div class="sofa-pick-bottom">
                    <span class="sofa-action-pill ${actionClass}">${pickData.pick}</span>
                    ${statusHTML}
                </div>
                <div class="sofa-micro-bar">
                    <div class="sofa-micro-fill" style="width: ${Math.min(100, Math.max(10, confValue))}%;"></div>
                </div>
            </div>
        `;
    }

    function renderList(containerId, periodKey, picksArray, highProbArray, highOverArray, highUnderArray, parlaySafeArray) {
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
            container.innerHTML = `<div style="color: #64748b; font-size: 0.8rem; text-align: center; padding: 20px;">Tidak ada opsi ${filterName} di atas 85% untuk babak ini.</div>`;
            return;
        }

        container.innerHTML = displayPicks.map(p => createPickItemHTML(p, periodKey)).join('');

        // Attach Card Click Events
        container.querySelectorAll('.sofa-pick-card').forEach(card => {
            card.addEventListener('click', () => toggleCardSelection(card));
        });
    }

    // 1. Babak 1 (HT)
    const htExp = predObj.expectancies.ht;
    document.getElementById('htExpBadge').textContent = `λ Match: ${htExp.total} gol (xG)`;

    const htP = predObj.predictions.ht;
    renderList('htPicksList', 'ht', htP.all_picks, htP.high_prob, htP.high_over, htP.high_under, htP.parlay_safe);
    document.getElementById('htReasoningText').textContent = predObj.reasoning.ht;

    // 2. Babak 2 (2HT)
    const shExp = predObj.expectancies['2ht'];
    document.getElementById('shExpBadge').textContent = `λ Match: ${shExp.total} gol (xG)`;

    const shP = predObj.predictions['2ht'];
    renderList('shPicksList', '2ht', shP.all_picks, shP.high_prob, shP.high_over, shP.high_under, shP.parlay_safe);
    document.getElementById('shReasoningText').textContent = predObj.reasoning['2ht'];

    // 3. Full Time (FT)
    const ftExp = predObj.expectancies.ft;
    document.getElementById('ftExpBadge').textContent = `λ Match: ${ftExp.total} gol (xG)`;

    const ftP = predObj.predictions.ft;
    renderList('ftPicksList', 'ft', ftP.all_picks, ftP.high_prob, ftP.high_over, ftP.high_under, ftP.parlay_safe);
    document.getElementById('ftReasoningText').textContent = predObj.reasoning.ft;

    renderComparePanel();
}

// Toggle Selection on Card Click
function toggleCardSelection(cardElem) {
    const period = cardElem.getAttribute('data-period');
    const key = cardElem.getAttribute('data-key');
    const label = cardElem.getAttribute('data-label');
    const pick = cardElem.getAttribute('data-pick');
    const conf = cardElem.getAttribute('data-conf');
    const isOver = cardElem.getAttribute('data-is-over') === 'true';
    const mode = cardElem.getAttribute('data-mode');
    const loss = cardElem.getAttribute('data-loss');
    const outcome = cardElem.getAttribute('data-outcome');

    if (!userSelectedPicks[period]) userSelectedPicks[period] = [];

    const existingIndex = userSelectedPicks[period].findIndex(p => p.key === key);
    if (existingIndex >= 0) {
        userSelectedPicks[period].splice(existingIndex, 1);
        cardElem.classList.remove('is-selected');
    } else {
        userSelectedPicks[period].push({
            period,
            key,
            label,
            pick,
            conf,
            isOver,
            mode,
            loss,
            outcome
        });
        cardElem.classList.add('is-selected');
    }

    renderComparePanel();
}

// Render Comparison Panel
function renderComparePanel() {
    const totalCount = (userSelectedPicks.ht?.length || 0) + (userSelectedPicks['2ht']?.length || 0) + (userSelectedPicks.ft?.length || 0);
    const countBadge = document.getElementById('compareCountBadge');
    if (countBadge) {
        countBadge.textContent = `${totalCount} Terpilih`;
    }

    function renderCol(periodKey, containerId, periodTitle) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const list = userSelectedPicks[periodKey] || [];
        if (list.length === 0) {
            container.innerHTML = `<div class="compare-empty-placeholder">Klik kartu di kolom ${periodTitle} untuk menandai</div>`;
            return;
        }

        container.innerHTML = list.map(item => `
            <div class="compare-item-card">
                <div class="c-top">
                    <span>${item.label}</span>
                    <span class="c-val">${item.conf}% <span style="font-size:0.68rem; font-weight:normal; color:#64748b;">${item.mode === 'parlay' ? 'Aman' : 'Peluang'}</span></span>
                </div>
                <div class="c-bottom">
                    <span class="sofa-action-pill ${item.isOver ? 'badge-pill-over' : 'badge-pill-under'}" style="font-size: 0.7rem; padding: 2px 7px;">${item.pick}</span>
                    <span style="font-size: 0.72rem; color: #475569;">
                        ${item.mode === 'parlay' ? `🛡️ Resiko: ${item.loss}%` : `${item.outcome}`}
                    </span>
                    <button class="c-remove" onclick="removeSelectedPick('${periodKey}', '${item.key}')" title="Hapus dari komparasi">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    renderCol('ht', 'compareBodyHT', 'HT');
    renderCol('2ht', 'compareBody2HT', '2HT');
    renderCol('ft', 'compareBodyFT', 'FT');
}

// Window Global Remove Callback for Comparison Badges
window.removeSelectedPick = function(period, key) {
    if (userSelectedPicks[period]) {
        const idx = userSelectedPicks[period].findIndex(p => p.key === key);
        if (idx >= 0) {
            userSelectedPicks[period].splice(idx, 1);
        }
    }
    const cardElem = document.querySelector(`.sofa-pick-card[data-key="${key}"]`);
    if (cardElem) cardElem.classList.remove('is-selected');
    renderComparePanel();
};
