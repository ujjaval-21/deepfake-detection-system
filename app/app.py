from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename

# Import detection modules
from detectors.detect_image import analyze_image
from detectors.detect_video import analyze_video


app = Flask(__name__)

# PATH SETUP
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# SERVE UPLOADED FILES
@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# FILE TYPE CONFIG
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# NAVIGATION ROUTES
@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/select')
def select_page():
    return render_template('select.html')

@app.route('/image')
def image_page():
    return render_template('image.html')

@app.route('/video')
def video_page():
    return render_template('video.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

# LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "admin":
            return redirect(url_for('select_page'))
        else:
            return render_template('login.html', error="Invalid Credentials")

    return render_template('login.html')


# IMAGE DETECTION
@app.route('/detect-image', methods=['POST'])
def detect_image():

    file = request.files.get('image')

    if not file or file.filename == "":
        return "❌ No image uploaded"

    if not allowed_file(file.filename, IMAGE_EXTENSIONS):
        return "❌ Only Image files (JPG, PNG) allowed!"

    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
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


# VIDEO DETECTION
@app.route('/detect-video', methods=['POST'])
def detect_video():

    file = request.files.get('video')

    if not file or file.filename == "":
        return "❌ No video uploaded"

    if not allowed_file(file.filename, VIDEO_EXTENSIONS):
        return "❌ Only Video files (MP4, AVI, MOV) allowed!"

    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file.save(video_path)

    label, confidence, metadata, converted_path = analyze_video(video_path)
    converted_filename = os.path.basename(converted_path)
    video_url = url_for('serve_uploaded_file', filename=converted_filename)

    return render_template(
        'result.html',
        result=label,
        prob=confidence,
        metadata=metadata,
        video_url=video_url,
        filetype="video"
)

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True, port=3002)