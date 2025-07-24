import cv2
import numpy as np
from datetime import datetime
import os
from ultralytics import YOLO
import db_manager
from plyer import notification
import winsound

# Ensure recordings directory exists
if not os.path.exists("recordings"):
    os.makedirs("recordings")

# Initialize YOLO model
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

        # Preprocessing for motion/tamper
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)

        if first_frame is None:
            first_frame = gray_blur
            continue

        # Motion Detection
        delta = cv2.absdiff(first_frame, gray_blur)
        thresh = cv2.threshold(delta, 40, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = any(cv2.contourArea(c) >= 3000 for c in contours)

        # Tamper Detection
        if np.mean(gray) < 20:
            cv2.putText(frame, "⚠ TAMPER DETECTED", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            if not tamper_logged:
                print("⚠ Tamper Detected: Possible camera obstruction.")

                # Insert tamper event into DB
                db_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db_manager.insert_event(db_timestamp, "tamper", None, None)
                print("✅ Tamper event inserted into DB.")

                # 🚨 Beep sound
                winsound.Beep(1000, 500)

                # 🚨 Desktop notification
                notification.notify(
                    title="Suraksha Alert – Tamper Detected",
                    message="Camera obstruction detected.",
                    timeout=5
                )

                tamper_logged = True
        else:
            tamper_logged = False

        # YOLO Object Detection
        results = model.predict(source=frame, conf=YOLO_CONFIDENCE_THRESHOLD, verbose=False)
        annotated_frame = results[0].plot()

        # Check if objects detected
        object_detected = False
        for box in results[0].boxes:
            conf = float(box.conf)
            if conf >= YOLO_CONFIDENCE_THRESHOLD:
                object_detected = True
                if not object_logged:
                    print(f"🎯 Object Detected with confidence: {conf:.2f}")

                    # Insert object event into DB
                    db_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db_manager.insert_event(db_timestamp, "object", None, conf)
                    print("✅ Object event inserted into DB.")

                    # 🚨 Desktop notification
                    notification.notify(
                        title="Suraksha Alert – Object Detected",
                        message=f"Object detected (confidence {conf:.2f})",
                        timeout=5
                    )

                    object_logged = True
                break
        if not object_detected:
            object_logged = False

        # Refresh background every 100 frames ONLY if no motion
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
            if recording and video_writer:
                video_writer.write(annotated_frame)
        else:
            if recording:
                recording = False
                if video_writer:
                    video_writer.release()
                    video_writer = None
                print("⏹ Recording stopped.")

                # Insert motion event if motion was last
                db_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db_manager.insert_event(db_timestamp, "motion", last_clip_filename, None)

        # Show video feed
        cv2.imshow("Suraksha Live Feed", annotated_frame)

        key = cv2.waitKey(1)
        if key == ord('q'):
            print("Exit requested by user.")
            break

except KeyboardInterrupt:
    print("⛔ Interrupted by user.")

finally:
    cap.release()
    if video_writer:
        video_writer.release()
    cv2.destroyAllWindows()
    print("✅ Camera released. All windows closed.")
