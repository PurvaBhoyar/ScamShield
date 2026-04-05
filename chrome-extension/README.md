# ScamShield Chrome Extension

A lightweight Chrome extension to scan job postings and URLs for potential scams.

## Features

- **URL Scanner** - Scan any job listing URL
- **Text Scanner** - Paste job description text to analyze
- **Risk Score** - Get instant risk assessment
- **Findings** - See specific red flags detected
- **Recommendations** - Get actionable advice
- **Right-click Scan** - Scan selected text or page URL

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder

## Configuration

Before using, update the API URL in `popup.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

If deploying, change to your deployed backend:
```javascript
const API_BASE_URL = 'https://your-backend.railway.app';
```

## Usage

1. Click the ScamShield icon in Chrome toolbar
2. Choose URL Scan or Text Scan
3. Click Scan button
4. View results with risk score

## Or use Right-click:

- Select text on any page → Right-click → "Scan with ScamShield"
- On any page → Right-click → "Scan with ScamShield"

## Files

- `manifest.json` - Extension configuration
- `popup.html` - Extension UI
- `popup.js` - Extension logic
- `background.js` - Background service worker
- `styles.css` - UI styling

## Requirements

- Backend API must be running
- CORS enabled on backend (or use deployed URL)

## Notes

- Icons need to be added manually to `icons/` folder
- For production, update host_permissions in manifest.json