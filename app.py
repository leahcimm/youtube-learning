import os
import re
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from summarizer import extract_key_points

app = Flask(__name__)

PRIORITY_LANGS = ["en", "zh-Hans", "zh-TW", "zh", "es", "fr", "de", "ja", "ko"]


def extract_video_id(url: str):
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


def get_snippets(video_id: str) -> list[dict]:
    api = YouTubeTranscriptApi()
    try:
        transcript_list = api.list(video_id)
    except Exception as e:
        raise Exception(f"Could not list transcripts: {e}")

    # Try preferred languages in order
    for lang in PRIORITY_LANGS:
        try:
            t = transcript_list.find_transcript([lang])
            snippets = list(t.fetch())
            return [{"text": s.text, "start": s.start, "duration": s.duration} for s in snippets]
        except Exception:
            continue

    # Fall back to any available transcript
    try:
        available = list(transcript_list)
        if available:
            snippets = list(available[0].fetch())
            return [{"text": s.text, "start": s.start, "duration": s.duration} for s in snippets]
    except Exception:
        pass

    raise NoTranscriptFound(video_id, PRIORITY_LANGS, None)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "Please paste a YouTube URL"}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Could not find a valid YouTube video ID in that URL"}), 400

    try:
        snippets = get_snippets(video_id)
    except TranscriptsDisabled:
        return jsonify({"error": "This video has captions/transcripts disabled"}), 400
    except NoTranscriptFound:
        return jsonify({"error": "No transcript found for this video"}), 400
    except Exception as e:
        return jsonify({"error": f"Could not fetch transcript: {str(e)}"}), 400

    try:
        result = extract_key_points(snippets)
        result["video_id"] = video_id
        result["url"] = url
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=8080)
