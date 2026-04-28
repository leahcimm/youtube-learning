# YouTube Learning

Paste any YouTube link → get the core ideas extracted by AI, displayed in an Instagram-styled dashboard.

## Setup

**1. Get an Anthropic API key**
Go to https://console.anthropic.com and copy your API key.

**2. Create your `.env` file**
```
cp .env.example .env
```
Open `.env` and replace `your_api_key_here` with your actual key.

**3. Run the app**
```
chmod +x start.sh
./start.sh
```

Open **http://localhost:5000** in your browser.

## How it works

1. Paste a YouTube URL and click **Analyze**
2. The app fetches the video's transcript
3. Claude AI extracts the key points
4. Results are shown in an Instagram-styled card
5. Your history is saved in the browser (no account needed)
