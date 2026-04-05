// ScamShield Chrome Extension - Popup Logic

// Configuration - Change this to your deployed backend URL
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');
const urlInput = document.getElementById('url-input');
const textInput = document.getElementById('text-input');
const scanUrlBtn = document.getElementById('scan-url-btn');
const scanTextBtn = document.getElementById('scan-text-btn');
const resultsSection = document.getElementById('results');
const loadingSection = document.getElementById('loading');
const errorSection = document.getElementById('error');
const errorMessage = document.getElementById('error-message');
const retryBtn = document.getElementById('retry-btn');

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
  // Get current tab URL
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs[0]?.url) {
      urlInput.value = tabs[0].url;
    }
  } catch (e) {
    console.log('Could not get tab URL:', e);
  }

  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  // Scan buttons
  scanUrlBtn.addEventListener('click', () => scanUrl());
  scanTextBtn.addEventListener('click', () => scanText());
  retryBtn.addEventListener('click', () => {
    hideAll();
    document.getElementById('url-tab').style.display = 'block';
  });
}

function switchTab(tabName) {
  tabs.forEach(t => t.classList.remove('active'));
  tabContents.forEach(tc => tc.classList.remove('active'));

  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
  document.getElementById(`${tabName}-tab`).classList.add('active');
}

async function scanUrl() {
  const url = urlInput.value.trim();
  if (!url) {
    showError('Please enter a URL');
    return;
  }

  await performScan({ type: 'url', url });
}

async function scanText() {
  const text = textInput.value.trim();
  if (!text) {
    showError('Please enter job description text');
    return;
  }

  await performScan({ type: 'text', text });
}

async function performScan(data) {
  showLoading();

  try {
    const response = await fetch(`${API_BASE_URL}/api/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams(data)
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    const result = await response.json();
    showResults(result);

    // Update badge
    updateBadge(result.label);

  } catch (error) {
    console.error('Scan error:', error);
    showError(error.message || 'Failed to scan. Make sure backend is running.');
  }
}

function showResults(data) {
  hideAll();
  resultsSection.style.display = 'block';

  // Update score
  const scoreCircle = document.getElementById('score-circle');
  const scoreValue = document.getElementById('score-value');
  const scoreLabel = document.getElementById('score-label');

  scoreValue.textContent = data.score;
  scoreLabel.textContent = data.label;

  scoreCircle.className = 'score-circle';
  if (data.label === 'Safe') scoreCircle.classList.add('safe');
  else if (data.label === 'Caution') scoreCircle.classList.add('caution');
  else scoreCircle.classList.add('danger');

  // Update details
  document.getElementById('company-name').textContent = data.company_name || 'Unknown';
  document.getElementById('job-title').textContent = data.job_title || 'Unknown';

  // Update findings
  const findingsList = document.getElementById('findings-list');
  findingsList.innerHTML = '';

  if (data.findings && data.findings.length > 0) {
    data.findings.forEach(finding => {
      const li = document.createElement('li');
      li.textContent = `${finding.type.replace(/_/g, ' ')}: ${finding.message}`;
      findingsList.appendChild(li);
    });
  } else {
    const li = document.createElement('li');
    li.textContent = 'No red flags detected';
    findingsList.appendChild(li);
  }

  // Update actions
  const actionsList = document.getElementById('actions-list');
  actionsList.innerHTML = '';

  if (data.actions && data.actions.length > 0) {
    data.actions.forEach(action => {
      const li = document.createElement('li');
      li.textContent = action;
      actionsList.appendChild(li);
    });
  }
}

function showLoading() {
  hideAll();
  loadingSection.style.display = 'block';
}

function showError(message) {
  hideAll();
  errorMessage.textContent = message;
  errorSection.style.display = 'block';
}

function hideAll() {
  resultsSection.style.display = 'none';
  loadingSection.style.display = 'none';
  errorSection.style.display = 'none';
}

function updateBadge(label) {
  let color = '#22c55e'; // green
  let text = '✓';

  if (label === 'Caution') {
    color = '#eab308'; // yellow
    text = '!';
  } else if (label === 'Danger') {
    color = '#ef4444'; // red
    text = '!';
  }

  chrome.action.setBadgeBackgroundColor({ color });
  chrome.action.setBadgeText({ text });
}

// Context menu for right-click scan
chrome.contextMenus?.create({
  id: 'scan-with-scamshield',
  title: 'Scan with ScamShield',
  contexts: ['selection', 'page']
});

chrome.contextMenus?.onClicked.addListener(async (info, tab) => {
  if (info.selectionText) {
    // Scan selected text
    await performScan({ type: 'text', text: info.selectionText });
  } else if (info.pageUrl) {
    // Scan page URL
    await performScan({ type: 'url', url: info.pageUrl });
  }
});