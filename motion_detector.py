import cv2
import numpy as np
from datetime import datetime
import os
from ultralytics import YOLO
import db_manager
import email_alerts
from plyer import notification
import winsound

# Ensure recordings directory exists
if not os.path.exists("recordings"):
    os.makedirs("recordings")

# YOLO Model
model = YOLO("yolov5s.pt")
YOLO_CONFIDENCE_THRESHOLD = 0.4

cap = cv2.VideoCapture(0)
first_frame = None
recording = False
video_writer = None
fourcc = cv2.VideoWriter_fourcc(*'XVID')
frame_counter = 0
last_clip_filename = None
tamper_logged = False
object_logged = False

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Could not read from webcam.")
            break

        # Grayscale for motion/tamper detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)

        if first_frame is None:
            first_frame = gray_blur
            continue

        # Motion detection
        delta = cv2.absdiff(first_frame, gray_blur)
        thresh = cv2.threshold(delta, 40, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        motion_detected = any(cv2.contourArea(c) >= 3000 for c in contours)

        # Tamper detection
        if np.mean(gray) < 20:
            cv2.putText(frame, "⚠ TAMPER DETECTED", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            if not tamper_logged:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db_manager.insert_event(timestamp, "tamper", None, None)
                print("⚠ Tamper detected and logged.")
                email_alerts.send_email_alert("tamper")
                notification.notify(title="Suraksha Alert", message="Tamper Detected!", timeout=5)
                winsound.Beep(1500, 400)
                tamper_logged = True
        else:
            tamper_logged = False

        # YOLO object detection
        results = model.predict(source=frame, conf=YOLO_CONFIDENCE_THRESHOLD, verbose=False)
        annotated_frame = results[0].plot()

        object_detected = False
        for box in results[0].boxes:
            conf = float(box.conf)
            if conf >= YOLO_CONFIDENCE_THRESHOLD:
                object_detected = True
                if not object_logged:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db_manager.insert_event(timestamp, "object", None, conf)
                    print(f"🎯 Object Detected with confidence: {conf:.2f}")
                    email_alerts.send_email_alert("object", confidence=conf)
                    notification.notify(title="Suraksha Alert", message="Object Detected", timeout=5)
                    winsound.Beep(1000, 300)
                    object_logged = True
                break
        if not object_detected:
            object_logged = False

        # Refresh background every 100 frames
        frame_counter += 1
        if not motion_detected and frame_counter % 100 == 0:
            first_frame = gray_blur
            print("🔄 Background frame updated.")

        # Recording logic
        if motion_detected or object_detected:
            if not recording:
                filename = f"recordings/clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
                last_clip_filename = filename
                video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (frame.shape[1], frame.shape[0]))
                recording = True
                print(f"▶ Recording started: {filename}")
            if video_writer:
                video_writer.write(annotated_frame)
        else:
            if recording:
                recording = False
                if video_writer:
                    video_writer.release()
                    video_writer = None
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db_manager.insert_event(timestamp, "motion", last_clip_filename, None)
                print("⏹ Recording stopped and motion logged.")

        # Show live feed
        cv2.imshow("Suraksha Live Feed", annotated_frame)
        key = cv2.waitKey(1)
        if key == ord('q'):
            print("🛑 Exit requested.")
            break

except KeyboardInterrupt:
    print("🛑 Interrupted by user.")

finally:
    cap.release()
    if video_writer:
        video_writer.release()
    cv2.destroyAllWindows()
    print("✅ All resources released.")
