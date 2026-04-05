// ScamShield Chrome Extension - Background Service Worker

// Badge colors
const COLORS = {
  safe: '#22c55e',
  caution: '#eab308',
  danger: '#ef4444',
  unknown: '#6b7280'
};

// Default badge
chrome.action.setBadgeBackgroundColor({ color: COLORS.unknown });
chrome.action.setBadgeText({ text: '?' });

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'updateBadge') {
    const color = COLORS[message.label?.toLowerCase()] || COLORS.unknown;
    const text = message.label ? message.label.charAt(0) : '?';

    chrome.action.setBadgeBackgroundColor({ color });
    chrome.action.setBadgeText({ text });

    sendResponse({ success: true });
  }
});

// Install event
chrome.runtime.onInstalled.addListener(() => {
  console.log('ScamShield extension installed');

  // Set default title
  chrome.action.setTitle({ title: 'ScamShield - Job Scam Detector' });
});