from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from ultralytics import YOLO
import os
from PIL import Image, ImageDraw
from kafka import KafkaProducer
import atexit

kafka_host = os.environ.get('KAFKA_BROKER_HOST')
# kafka_port = os.environ.get('KAFKA_BROKER_PORT')
kafka_topic = "test"
producer = KafkaProducer(bootstrap_servers = f"{kafka_host}:9092")

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pictures.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
model = YOLO('yolov8n.pt')

# Define the Picture model
class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    carcount = db.Column(db.Integer, nullable=False)

# Create uploads folder if not exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Health check
@app.route("/health")
def health():
    return "OK"

@app.route('/')
def index():
    # Fetch all pictures from the database
    pictures = Picture.query.all()
    return render_template('index.html', pictures=pictures)

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        # Get the uploaded file
        file = request.files['file']
        description = request.form['description']

        if file:
            # Save the file to the uploads folder
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Perform vehicle detection
            carcount = detect_image(filepath)

            # Store the file details in the database
            new_picture = Picture(filename=filename, description=description, carcount=carcount)
            db.session.add(new_picture)
            db.session.commit()

            send_message_to_topic(description, carcount)

            return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def detect_image(filepath):
    # Load the image
    img = Image.open(filepath)

    # Perform inference
    results = model.predict(img)

    carcount = 0
    # Process the results and draw bounding boxes
    for result in results:
        # Iterate over each detected box
        for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
            # If the detected class is a vehicle
            if cls == 2:  # Assuming class ID 2 represents a vehicle
                carcount += 1
                # Extract box coordinates
                x1, y1, x2, y2 = box

                # Draw bounding box on the image
                draw = ImageDraw.Draw(img)
                draw.rectangle([x1, y1, x2, y2], outline="red", width=2)

    # Save the modified image
    img.save(filepath)

    return carcount

# Send message to kafka broker
def send_message_to_topic(imageDescription, carCount):
    producer.send(kafka_topic, value=f"An image has been uploaded containing {carCount} vehicles with the following description: {imageDescription}".encode())
    print("Image upload message sent to topic")

def shutdown():
    producer.close()

with app.app_context():
    # Create SQLite database tables
    db.create_all()
    atexit.register(shutdown)

# if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=5000, debug=True) # not needed if Dockerfile is with "CMD ["flask", "run", "--host", "0.0.0.0"]"
