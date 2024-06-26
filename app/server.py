from time import sleep
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from ultralytics import YOLO
import os
from PIL import Image, ImageDraw
from kafka import KafkaProducer
import atexit

# Tries to connect to the kafka broker periodically for given number of attempts.
def ConnectToBroker(retryCount):
    for _ in range(retryCount):
        try:
            producer = KafkaProducer(bootstrap_servers = "kafka-broker-svc:9092")
            return producer
        except:
            print("Connecting to broker failed")
            sleep(5)
    return None

producer = ConnectToBroker(5)
if producer == None:
    raise Exception("Producer aka kafka broker was none, meaning connection error")
else:
    print("Connected to broker")

# Predefined kafka topic
kafka_topic = "serverUploads"

# Create flask application instance
app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pictures.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
model = YOLO('yolov8n.pt')
print("db and model loaded")

# Define the Picture model
class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    carcount = db.Column(db.Integer, nullable=False)

# Create uploads folder if not exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
print("created upload folder")

# Health check
@app.route("/health")
def health():
    return "OK"

# Starting page
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

# Image detection
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

# Close connection to broker
def shutdown():
    producer.close()

with app.app_context():
    # Create SQLite database tables
    db.create_all()
    atexit.register(shutdown)