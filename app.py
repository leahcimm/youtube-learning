import os
import json
import anthropic
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:shorts\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(video_id: str) -> str:
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join(entry["text"] for entry in transcript_list)


def extract_key_points(transcript: str, video_url: str) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this YouTube video transcript and extract the most important learning points.

Return a JSON object with this exact structure:
{{
  "title": "A short descriptive title for this video (max 8 words)",
  "summary": "2-3 sentence summary of what the video is about",
  "key_points": [
    {{
      "emoji": "relevant emoji",
      "heading": "Short heading (max 6 words)",
      "detail": "1-2 sentence explanation"
    }}
  ],
  "takeaway": "The single most important thing to remember from this video (1 sentence)"
}}

Extract 5-8 key points. Be concise and educational. Make headings punchy and memorable.

Transcript:
{transcript[:8000]}""",
            }
        ],
    )

    text = response.content[0].text
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return json.loads(text)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "Please paste a YouTube URL"}), 400

    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY not set. Add it to your .env file."}), 500

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Could not find a valid YouTube video ID in that URL"}), 400

    try:
        transcript = get_transcript(video_id)
    except TranscriptsDisabled:
        return jsonify({"error": "This video has captions/transcripts disabled"}), 400
    except NoTranscriptFound:
        return jsonify({"error": "No transcript found for this video"}), 400
    except Exception as e:
        return jsonify({"error": f"Could not fetch transcript: {str(e)}"}), 400

    try:
        result = extract_key_points(transcript, url)
        result["video_id"] = video_id
        result["url"] = url
        return jsonify(result)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse AI response. Try again."}), 500
    except Exception as e:
        return jsonify({"error": f"AI analysis failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
