'use strict';

// ───────── State ─────────
let currentQ = 1;
let timeLeft = 0;
let timerInterval = null;
let answered = {};  // { qNum: true }
let qcmFinished = false;

// ───────── Init ─────────
function initQcm() {
    showQuestion(1);
    setupAntiCheat();
    requestFullscreen();
}

// ───────── Navigation ─────────
function showQuestion(num) {
    // Hide all
    document.querySelectorAll('.question-slide').forEach(el => el.classList.remove('active'));
    // Show target
    const slide = document.getElementById('question-' + num);
    if (!slide) return;
    slide.classList.add('active');

    // Update dots
    document.querySelectorAll('.progress-dot').forEach(d => d.classList.remove('current'));
    const dot = document.getElementById('dot-' + num);
    if (dot) dot.classList.add('current');

    // Counter
    const counter = document.getElementById('question-counter');
    if (counter) counter.textContent = 'Question ' + num + ' / ' + QUESTION_COUNT;

    currentQ = num;
    startTimer();
}

function nextQuestion() {
    if (currentQ < QUESTION_COUNT) {
        showQuestion(currentQ + 1);
    } else {
        confirmSubmit();
    }
}

// ───────── Timer ─────────
function startTimer() {
    clearInterval(timerInterval);
    timeLeft = QUESTION_TIME;
    updateTimerDisplay();

    timerInterval = setInterval(() => {
        timeLeft--;
        updateTimerDisplay();
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            autoAdvance();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const count = document.getElementById('timer-count');
    const bar   = document.getElementById('timer-bar');
    if (!count || !bar) return;

    count.textContent = timeLeft;
    const pct = (timeLeft / QUESTION_TIME) * 100;
    bar.style.width = pct + '%';

    // Color states
    count.className = '';
    bar.className = '';

    if (timeLeft <= 5) {
        count.classList.add('timer-critical', 'pulse-red');
        bar.classList.add('bar-critical');
    } else if (timeLeft <= 10) {
        count.classList.add('timer-warning');
        bar.classList.add('bar-warning');
    } else {
        count.classList.add('text-success');
        bar.classList.add('bg-success');
    }
}

function autoAdvance() {
    markDotAnswered(currentQ);
    if (currentQ < QUESTION_COUNT) {
        showQuestion(currentQ + 1);
    } else {
        qcmFinished = true;
        autoSubmit();
    }
}

function markDotAnswered(num) {
    const dot = document.getElementById('dot-' + num);
    if (dot && !answered[num]) {
        answered[num] = true;
        dot.classList.add('answered');
    }
}

// Track radio button selections to mark dots
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[type=radio]').forEach(radio => {
        radio.addEventListener('change', function () {
            const slide = this.closest('.question-slide');
            if (slide) {
                const num = parseInt(slide.dataset.num);
                markDotAnswered(num);
            }
        });
    });
});

// ───────── Submit ─────────
function confirmSubmit() {
    clearInterval(timerInterval);
    qcmFinished = true;

    const unanswered = QUESTION_COUNT - Object.keys(answered).length;
    const warn = document.getElementById('unanswered-warning');
    if (warn) {
        if (unanswered > 0) {
            warn.textContent = unanswered + ' question(s) sans réponse seront comptées comme fausses.';
        } else {
            warn.textContent = 'Toutes les questions ont été répondues.';
        }
    }

    const modal = new bootstrap.Modal(document.getElementById('submitModal'));
    modal.show();
}

function autoSubmit() {
    clearInterval(timerInterval);
    qcmFinished = true;
    setTimeout(() => {
        const form = document.getElementById('qcmForm');
        if (form) form.submit();
    }, 800);
}

// ───────── Anti-cheat ─────────
function setupAntiCheat() {
    // Tab / window visibility change
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && !qcmFinished) {
            showCheatWarning('Changement d\'onglet détecté ! Cet incident a été signalé.');
            logCheatEvent('tab_switch');
        }
    });

    // Window loses focus
    window.addEventListener('blur', () => {
        if (!qcmFinished) {
            logCheatEvent('window_blur');
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        const blocked = ['c', 'v', 'a', 'x', 'u', 's', 'p'];
        if (e.ctrlKey && blocked.includes(e.key.toLowerCase())) {
            e.preventDefault();
            if (!qcmFinished) logCheatEvent('keyboard_shortcut', e.key);
            return false;
        }
        // Block F12, F5 refresh etc.
        if (['F12', 'F11', 'F5'].includes(e.key)) {
            e.preventDefault();
            return false;
        }
        // Block Meta key combinations
        if (e.metaKey && blocked.includes(e.key.toLowerCase())) {
            e.preventDefault();
            return false;
        }
    });

    // Disable right-click context menu
    document.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        return false;
    });

    // Disable text drag
    document.addEventListener('dragstart', (e) => e.preventDefault());

    // Detect fullscreen exit
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
}

function handleFullscreenChange() {
    const isFullscreen = !!(document.fullscreenElement ||
                             document.webkitFullscreenElement ||
                             document.mozFullScreenElement);
    if (!isFullscreen && !qcmFinished) {
        showFullscreenOverlay();
        logCheatEvent('fullscreen_exit');
    }
}

function showCheatWarning(msg) {
    const banner = document.getElementById('cheat-warning');
    const msgEl  = document.getElementById('cheat-msg');
    if (!banner) return;
    if (msgEl) msgEl.textContent = msg;
    banner.style.display = 'block';
    setTimeout(() => { banner.style.display = 'none'; }, 5000);
}

function showFullscreenOverlay() {
    const overlay = document.getElementById('fullscreen-overlay');
    if (overlay) overlay.classList.add('show');
}

function hideFullscreenOverlay() {
    const overlay = document.getElementById('fullscreen-overlay');
    if (overlay) overlay.classList.remove('show');
}

function enterFullscreen() {
    const el = document.documentElement;
    const req = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen;
    if (req) {
        req.call(el).then(() => {
            hideFullscreenOverlay();
        }).catch(err => {
            console.warn('Fullscreen refused:', err);
            hideFullscreenOverlay();
            showCheatWarning('Plein écran refusé par le navigateur. Cet incident a été signalé.');
            logCheatEvent('fullscreen_denied');
        });
    } else {
        hideFullscreenOverlay();
    }
}

function requestFullscreen() {
    const el = document.documentElement;
    const req = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen;
    if (req) {
        req.call(el).catch(() => {
            showFullscreenOverlay();
        });
    }
}

// ───────── Log event ─────────
function logCheatEvent(type, details) {
    if (typeof SESSION_ID === 'undefined' || typeof CSRF_TOKEN === 'undefined') return;

    fetch('/log-event', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({
            type: type,
            session_id: SESSION_ID,
            details: details || ''
        })
    }).catch(() => {/* silent */});
}
