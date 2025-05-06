import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time

# Constants
SMOOTHING_FACTOR = 0.2
EAR_THRESHOLD = 0.21
CONSEC_FRAMES = 2
CAM_INDEX = 0  # Change if external webcam

# Eye indices for right eye (MediaPipe FaceMesh)
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# Cursor screen size
screen_w, screen_h = pyautogui.size()
pyautogui.moveTo(screen_w // 2, screen_h // 2)  # Center cursor initially
prev_cursor_x, prev_cursor_y = screen_w // 2, screen_h // 2  # Initialize to center

# Initialize variables
prev_cursor_x, prev_cursor_y = 0, 0
blink_counter = 0
blink_detected = False
last_click_time = 0
click_cooldown = 1  # seconds

# Mediapipe setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)
mp_drawing = mp.solutions.drawing_utils

# Eye aspect ratio function
def calculate_ear(landmarks, eye_indices, image_shape):
    ih, iw = image_shape[:2]
    p1 = np.array([landmarks[eye_indices[0]].x * iw, landmarks[eye_indices[0]].y * ih])
    p2 = np.array([landmarks[eye_indices[1]].x * iw, landmarks[eye_indices[1]].y * ih])
    p3 = np.array([landmarks[eye_indices[2]].x * iw, landmarks[eye_indices[2]].y * ih])
    p4 = np.array([landmarks[eye_indices[3]].x * iw, landmarks[eye_indices[3]].y * ih])
    p5 = np.array([landmarks[eye_indices[4]].x * iw, landmarks[eye_indices[4]].y * ih])
    p6 = np.array([landmarks[eye_indices[5]].x * iw, landmarks[eye_indices[5]].y * ih])

    vertical1 = np.linalg.norm(p2 - p6)
    vertical2 = np.linalg.norm(p3 - p5)
    horizontal = np.linalg.norm(p1 - p4)

    ear = (vertical1 + vertical2) / (2.0 * horizontal)
    return ear

# Webcam capture
cap = cv2.VideoCapture(CAM_INDEX)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    h, w, _ = frame.shape

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark

        # Use landmark #474 for right eye (pupil region)
        eye = landmarks[474]
        frame_w, frame_h = w, h
        x = int(np.interp(eye.x * frame_w, [0, frame_w], [0, screen_w]))
        y = int(np.interp(eye.y * frame_h, [0, frame_h], [0, screen_h]))

        # Smooth cursor
        cursor_x = int(prev_cursor_x + (x - prev_cursor_x) * SMOOTHING_FACTOR)
        cursor_y = int(prev_cursor_y + (y - prev_cursor_y) * SMOOTHING_FACTOR)
        pyautogui.moveTo(cursor_x, cursor_y)
        prev_cursor_x, prev_cursor_y = cursor_x, cursor_y

        # Blink detection
        ear = calculate_ear(landmarks, RIGHT_EYE, frame.shape)
        if ear < EAR_THRESHOLD:
            blink_counter += 1
        else:
            if blink_counter >= CONSEC_FRAMES:
                now = time.time()
                if now - last_click_time > click_cooldown:
                    pyautogui.click()
                    last_click_time = now
            blink_counter = 0

        # Optional: show eye landmarks
        for idx in RIGHT_EYE:
            lx = int(landmarks[idx].x * w)
            ly = int(landmarks[idx].y * h)
            cv2.circle(frame, (lx, ly), 2, (0, 255, 0), -1)

        # Draw cursor position on camera preview
        cv2.circle(frame, (int(eye.x * w), int(eye.y * h)), 5, (0, 0, 255), -1)
        cv2.putText(frame, f'EAR: {ear:.2f}', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    cv2.imshow("Eye Control Mouse", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
