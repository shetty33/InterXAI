from flask import Flask, render_template, request, jsonify
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
import re

app = Flask(__name__)

# Initialize Groq client
groq_client = Groq(api_key="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")

def extract_video_id(url):
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry['text'] for entry in transcript])
    except Exception as e:
        return f"Error fetching transcript: {str(e)}"

def generate_flashcards(transcript):
    prompt = f"""
    Convert the following transcript of youtube video into paragraphs(each paragraph should be atmost 100 words), don't add headings and do not include any content except the video content:
    Transcript: {transcript}

    do not give anything except the paragraphs like this is the generated text or here are the paragraphs
    """
    try:
        # Using Groq's API to generate content
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",  # Choose appropriate Groq model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that converts YouTube transcripts into concise paragraphs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating flashcards: {str(e)}"

@app.route('/')
def index():
    return render_template('flashcardsupdateddd.html')

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    youtube_url = data.get("youtube_url")

    if not youtube_url:
        return jsonify({"error": "No YouTube URL provided."})

    video_id = extract_video_id(youtube_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL."})

    transcript = get_youtube_transcript(video_id)
    if "Error" in transcript:
        return jsonify({"error": transcript})

    flashcards = generate_flashcards(transcript)
    if "Error" in flashcards:
        return jsonify({"error": flashcards})

    return jsonify({"flashcards": flashcards})

if __name__ == '__main__':
    app.run(debug=False, port=5005)