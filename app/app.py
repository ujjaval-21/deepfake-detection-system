from flask import Flask, render_template, request, redirect, url_for
import os
import shutil
from werkzeug.utils import secure_filename
import validators
import requests
import yt_dlp
import uuid

# Import detection modules
from detectors.detect_image import analyze_image
from detectors.detect_video import analyze_video
from detectors.detect_link import analyze_link
from detectors.detect_audio import analyze_audio

from flask import send_from_directory


app = Flask(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# FILE TYPE CONFIG
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov'}
AUDIO_EXTENSIONS = {'mp3', 'wav'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# NAVIGATION ROUTES

@app.route('/image')
def image_page():
    return render_template('image.html')

@app.route('/video')
def video_page():
    return render_template('video.html')

@app.route('/audio')
def audio_page():
    return render_template('audio.html')

@app.route('/link')
def link_page():
    return render_template('link.html')

@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/select')
def select_page():
    return render_template('select.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/history')
def history():
    return render_template('history.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin":
            return redirect(url_for('select_page'))
        else:
            return render_template('login.html', error="Invalid Credentials")

    return render_template('login.html')


# IMAGE DETECTION ROUTE

@app.route('/detect-image', methods=['POST'])
def detect_image():

    file = request.files.get('image')

    if not file or file.filename == "":
        return "No file uploaded"

    if not allowed_file(file.filename, IMAGE_EXTENSIONS):
        return "❌ Only Image files (JPG, PNG) allowed!"

    filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file.save(image_path)

    label, confidence, metadata = analyze_image(image_path)

    return render_template(
    'result.html',
    result=label,
    prob=confidence,
    metadata=metadata,
    filename=filename,
    filetype="image"
)

# VIDEO DETECTION ROUTE

@app.route('/detect-video', methods=['POST'])
def detect_video():

    file = request.files.get('video')

    if not file or file.filename == "":
        return "No file uploaded"

    if not allowed_file(file.filename, VIDEO_EXTENSIONS):
        return "❌ Only Video files (MP4, AVI, MOV) allowed!"

    filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file.save(video_path)

    confidence, metadata = analyze_video(video_path)

    result = "Likely Deepfake" if confidence > 50 else "Likely Real"

    return render_template(
        'result.html',
        result=result,
        prob=f"{int(confidence)}%",
        filename=filename,
        filetype="video"
    )


#AUDIO DETECTION ROUTE

@app.route('/detect-audio', methods=['POST'])
def detect_audio():

    file = request.files.get('audio')

    if not file or file.filename == "":
        return "No file uploaded"

    if not allowed_file(file.filename, AUDIO_EXTENSIONS):
        return "❌ Only Audio files (MP3, WAV) allowed!"

    filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file.save(audio_path)

    result, confidence = analyze_audio(audio_path)

    return render_template(
        'result.html',
        result=result,
        prob=confidence,
        filename=filename,
        filetype="audio"
    )


# LINK DETECTION ROUTE
import validators
import requests
import os
import yt_dlp

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@app.route('/detect-link', methods=['POST'])
def detect_link():

    url = request.form['video_url'].strip()

    # 1️⃣ Validate URL
    if not validators.url(url):
        return render_template("result.html",
                               result="Invalid URL",
                               prob="0%",
                               metadata=None,
                               filename="",
                               filetype="none")

    try:
        # 2️⃣ Check reachable
        head = requests.head(url, allow_redirects=True, timeout=7)
        content_type = head.headers.get('content-type', '')

    except:
        return render_template("result.html",
                               result="Unable to access link",
                               prob="0%",
                               metadata=None,
                               filename="",
                               filetype="none")

    # CASE 1: SOCIAL MEDIA / WEBPAGE (YouTube / Instagram etc)
    if 'text/html' in content_type:

        try:
            ydl_opts = {
                'outtmpl': os.path.join(app.config['UPLOAD_FOLDER'], 'downloaded.%(ext)s'),
                'format': 'mp4/best',
                'quiet': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            confidence, metadata = analyze_video(filename)
            result = "Likely Deepfake" if confidence > 50 else "Likely Real"
            prob = f"{int(confidence)}%"

            return render_template("result.html",
                                   result=result,
                                   prob=prob,
                                   metadata=metadata,
                                   filename=os.path.basename(filename),
                                   filetype="video")

        except:
            return render_template("result.html",
                                   result="Could not extract video from link",
                                   prob="0%",
                                   metadata=None,
                                   filename="",
                                   filetype="none")

    
    # CASE 2: DIRECT MEDIA FILE (image/audio/video URL)
    try:
        extension = content_type.split('/')[-1]
        filename = f"link_file.{extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        r = requests.get(url, stream=True, timeout=15)
        size = 0

        with open(file_path, "wb") as f:
            for chunk in r.iter_content(1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    return render_template("result.html",
                                           result="File too large (max 20MB)",
                                           prob="0%",
                                           metadata=None,
                                           filename="",
                                           filetype="none")
                f.write(chunk)

        # ---------- Detect type ----------
        if 'image' in content_type:
            result = analyze_image(file_path)
            prob = "N/A"
            metadata = None
            filetype = "image"

        elif 'audio' in content_type:
            result, prob = analyze_audio(file_path)
            metadata = None
            filetype = "audio"

        elif 'video' in content_type:
            confidence, metadata = analyze_video(file_path)
            result = "Likely Deepfake" if confidence > 50 else "Likely Real"
            prob = f"{int(confidence)}%"
            filetype = "video"

        else:
            return render_template("result.html",
                                   result="Unsupported file type",
                                   prob="0%",
                                   metadata=None,
                                   filename="",
                                   filetype="none")

        return render_template("result.html",
                               result=result,
                               prob=prob,
                               metadata=metadata,
                               filename=filename,
                               filetype=filetype)

    except:
        return render_template("result.html",
                               result="Failed to download media",
                               prob="0%",
                               metadata=None,
                               filename="",
                               filetype="none")



# MAIN

if __name__ == '__main__':
    app.run(debug=True, port=3002)
