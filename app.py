from flask import Flask, request, render_template, redirect, url_for, flash
from gtts import gTTS
import time
import os
from vercel_blob import put, list as blob_list, delete as blob_delete

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Blob folder name
BLOB_FOLDER = "tts-audio"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form.get("text", "").strip()

        if not text:
            flash("Please enter text!", "error")
            return redirect(url_for("index"))

        # Create audio file in memory
        timestamp = int(time.time() * 1000)
        filename = f"audio_{timestamp}.mp3"
        temp_path = f"/tmp/{filename}"

        tts = gTTS(text=text, lang="en")
        tts.save(temp_path)

        # Upload to Vercel Blob
        with open(temp_path, "rb") as file:
            put(f"{BLOB_FOLDER}/{filename}", file, content_type="audio/mpeg")

        flash("Audio created successfully!", "success")
        return redirect(url_for("index"))

    # Load existing audio list from Blob
    files = blob_list(prefix=BLOB_FOLDER)

    # Extract only filename + URL
    audio_files = [
        {"name": item["pathname"].replace(f"{BLOB_FOLDER}/", ""), "url": item["url"]}
        for item in files
    ]

    audio_files.reverse()

    return render_template("index.html", files=audio_files)

@app.route("/delete/<filename>", methods=["POST"])
def delete(filename):
    try:
        blob_delete(f"{BLOB_FOLDER}/{filename}")
        flash("Audio deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting: {str(e)}", "error")

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
