import librosa
import pandas as pd
import cv2
from flask import Flask, request, render_template, Response, jsonify, send_file
from datetime import datetime
import os

app = Flask(__name__)

EXCEL_FILE_LIVE = "live_stress_results.xlsx"
EXCEL_FILE_UPLOAD = "uploaded_stress_results.xlsx"

# Initialize Excel files with headers if they don't exist
for excel_file in [EXCEL_FILE_LIVE, EXCEL_FILE_UPLOAD]:
    if not os.path.exists(excel_file):
        df = pd.DataFrame(columns=['Frame', 'Stress_Level', 'Emotion', 'Frequency'])
        df.to_excel(excel_file, index=False)

# Placeholder function to calculate stress level and emotion
def calculate_stress_and_emotion(frame):
    # Replace this with actual analysis logic
    stress_level = 50  # Example stress level
    emotion = "Neutral"  # Example emotion
    return stress_level, emotion

# Detect frequency (for uploaded audio only)
def detect_audio_frequency(audio_file):
    y, sr = librosa.load(audio_file)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    avg_frequency = spectral_centroid.mean()
    return avg_frequency

# Route for index page
@app.route('/')
def index():
    return render_template('index.html')

# Live stress detection page
@app.route('/live-stress-detection')
def live_stress_detection():
    return render_template('live_stress_detection.html')

# Camera feed for live session
def generate_frames():
    cap = cv2.VideoCapture(1)
    frame_count = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Process frame for stress and emotion
        stress_level, emotion = calculate_stress_and_emotion(frame)
        
        # Simulated frequency per frame (this should be adjusted for real analysis)
        frequency = 0  # Replace with actual frequency if available

        # Append results to Excel file
        df = pd.read_excel(EXCEL_FILE_LIVE)
        new_data = {
            'Frame': frame_count,
            'Stress_Level': stress_level,
            'Emotion': emotion,
            'Frequency': frequency
        }
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_excel(EXCEL_FILE_LIVE, index=False)

        # Convert frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        frame_count += 1
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Start and End session for live stress detection
@app.route('/start_live_session', methods=['POST'])
def start_live_session():
    # Clear existing data in the live session Excel file
    df = pd.DataFrame(columns=['Frame', 'Stress_Level', 'Emotion', 'Frequency'])
    df.to_excel(EXCEL_FILE_LIVE, index=False)
    return jsonify({"status": "Session started"})

@app.route('/end_live_session', methods=['POST'])
def end_live_session():
    # Compute averages of recorded data
    df = pd.read_excel(EXCEL_FILE_LIVE)
    if not df.empty:
        avg_stress = df['Stress_Level'].mean()
        avg_frequency = df['Frequency'].mean()
        avg_emotion = df['Emotion'].mode()[0]  # Using mode as the dominant emotion

        # Append summary row to Excel
        summary_data = {
            'Frame': 'Average',
            'Stress_Level': avg_stress,
            'Emotion': avg_emotion,
            'Frequency': avg_frequency
        }
        df = pd.concat([df, pd.DataFrame([summary_data])], ignore_index=True)
        df.to_excel(EXCEL_FILE_LIVE, index=False)
    return jsonify({"status": "Session ended"})

@app.route('/download_live_excel')
def download_live_excel():
    return send_file(EXCEL_FILE_LIVE, as_attachment=True)

# Upload video functionality
@app.route('/upload-video', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        video = request.files.get('video')
        
        if video:
            # Simulated stress data and emotion (replace with actual detection logic)
            stress_data = [50, 60, 55, 70]
            avg_stress_level = sum(stress_data) / len(stress_data)
            dominant_emotion = "Neutral"  # Example emotion

            # Append session data to uploaded Excel file
            df = pd.read_excel(EXCEL_FILE_UPLOAD)
            for i, stress in enumerate(stress_data):
                new_data = {
                    'Frame': i + 1,
                    'Stress_Level': stress,
                    'Emotion': dominant_emotion,
                    'Frequency': 0  # Replace with frequency if available
                }
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)

            # Add averages to end of Excel file
            summary_data = {
                'Frame': 'Average',
                'Stress_Level': avg_stress_level,
                'Emotion': dominant_emotion,
                'Frequency': 0
            }
            df = pd.concat([df, pd.DataFrame([summary_data])], ignore_index=True)
            df.to_excel(EXCEL_FILE_UPLOAD, index=False)

            return render_template(
                'upload_video.html',
                avg_stress_level=avg_stress_level,
                avg_emotion=dominant_emotion,
                download_ready=True
            )
    return render_template('upload_video.html', download_ready=False)

@app.route('/download_uploaded_excel')
def download_uploaded_excel():
    return send_file(EXCEL_FILE_UPLOAD, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
