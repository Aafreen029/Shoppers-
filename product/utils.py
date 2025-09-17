import numpy as np
import mediapipe as mp
import os
import cv2
from mediapipe.python.solutions.holistic import PoseLandmark as lm
mp_holistic = mp.solutions.holistic
PoseLandmark = mp.solutions.holistic.PoseLandmark
# --- Utility Functions ---
def validate_image(image_path):
    valid_extensions = ['.png', '.jpg']
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in valid_extensions:
        raise ValueError(f"Unsupported file format: {ext}. Only PNG and JPG are allowed.")

    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at {image_path}")

    height, width = image.shape[:2]
    if width >= height:
        raise ValueError(f"Image must be in portrait orientation. Got {width}x{height}")
    if height < 600 or width < 400:
        raise ValueError(f"Image resolution too low: {width}x{height}")
    if height > 3000 or width > 2000:
        raise ValueError(f"Image resolution too high: {width}x{height}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    if mean_brightness < 40:
        raise ValueError("Image rejected: lighting too dark.")

    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def distance(a, b): return np.linalg.norm(np.array(a) - np.array(b))
def midpoint(a, b): return (a + b) / 2
def estimate_waist_circumference(width_cm,depth_cm=18):
    #depth_cm = np.clip(width_cm * 0.85, 14.0, 20.0)  
    a, b = width_cm / 2, depth_cm / 2
    return np.pi * (3*(a + b) - np.sqrt((3*a + b)*(a + 3*b)))

def recommend_size_upper(shoulder_cm, chest_circumference_cm):
    if shoulder_cm < 35 and chest_circumference_cm < 85: return "XS"
    elif shoulder_cm < 40 and chest_circumference_cm < 90: return "S"
    elif shoulder_cm < 45 and chest_circumference_cm < 100: return "M"
    elif shoulder_cm < 50 and chest_circumference_cm < 104: return "L"
    elif shoulder_cm < 55 and chest_circumference_cm < 110: return "XL"
    else: return "XXL"

def recommend_size_pants(waist_cm, inseam_cm):
    waist_circ = estimate_waist_circumference(waist_cm)
    if waist_circ < 70 and inseam_cm < 75: return "28"
    elif waist_circ < 75 and inseam_cm < 80: return "30"
    elif waist_circ < 80 and inseam_cm < 85: return "32"
    elif waist_circ < 85 and inseam_cm < 90: return "34"
    else: return "36"

def percentile_alignment(value, lower, upper):
    if value < lower or value > upper:
        return 60
    center = (lower + upper) / 2
    deviation = abs(value - center) / ((upper - lower) / 2)
    return np.clip(90 - deviation * 10, 60, 100)

def compute_accuracy_score(
    visible_ratio,
    pose_quality,
    body_coverage_pct,
    angle_score,
    landmark_symmetry_score=None,
    percentile_alignment_score=None,
    weights=None):
  
    default_weights = {
        "visible_ratio": 0.2,
        "pose_quality": 0.2,
        "body_coverage_pct": 0.2,
        "body_angle": 0.15,
        "symmetry": 0.15,
        "percentile_alignment": 0.1,
    }
    weights = weights or default_weights

    score = 0
    score += visible_ratio * weights.get("visible_ratio", 0)
    score += (pose_quality / 100) * weights.get("pose_quality", 0)
    score += (body_coverage_pct / 100) * weights.get("body_coverage_pct", 0)
    score += (angle_score / 100) * weights.get("body_angle", 0)

    if landmark_symmetry_score is not None:
        score += (landmark_symmetry_score / 100) * weights.get("symmetry", 0)
    if percentile_alignment_score is not None:
        score += (percentile_alignment_score / 100) * weights.get("percentile_alignment", 0)

    score = min(score, 1.0)
    return round(score, 2)

def extract_measurements(results, user_height_cm):
    def landmark_to_array(lm_obj): return np.array([lm_obj.x, lm_obj.y, lm_obj.z])
    lms = results.pose_world_landmarks.landmark
    
    # Key landmarks
    left_shoulder = landmark_to_array(lms[lm.LEFT_SHOULDER])
    right_shoulder = landmark_to_array(lms[lm.RIGHT_SHOULDER])
    left_elbow = landmark_to_array(lms[lm.LEFT_ELBOW])
    right_elbow = landmark_to_array(lms[lm.RIGHT_ELBOW])
    left_wrist = landmark_to_array(lms[lm.LEFT_WRIST])
    right_wrist = landmark_to_array(lms[lm.RIGHT_WRIST])
    left_hip = landmark_to_array(lms[lm.LEFT_HIP])
    right_hip = landmark_to_array(lms[lm.RIGHT_HIP])
    left_knee = landmark_to_array(lms[lm.LEFT_KNEE])
    right_knee = landmark_to_array(lms[lm.RIGHT_KNEE])
    left_ankle = landmark_to_array(lms[lm.LEFT_ANKLE])
    right_ankle = landmark_to_array(lms[lm.RIGHT_ANKLE])
    nose = landmark_to_array(lms[lm.NOSE])
    left_ear= landmark_to_array(lms[lm.LEFT_EAR])
    right_ear= landmark_to_array(lms[lm.RIGHT_EAR])
    upper_landmarks = [lm.LEFT_SHOULDER, lm.RIGHT_SHOULDER, lm.RIGHT_ELBOW, lm.LEFT_ELBOW, lm.LEFT_WRIST, lm.RIGHT_WRIST]
    lower_landmarks = [lm.LEFT_HIP, lm.RIGHT_HIP, lm.LEFT_KNEE, lm.RIGHT_KNEE, lm.LEFT_ANKLE, lm.RIGHT_ANKLE]

    height_m = distance(nose, right_ankle)
    scale = user_height_cm / (height_m * 100)

    # Neck
    shoulder_span_cm = distance(left_shoulder, right_shoulder) * scale
    neck_width= shoulder_span_cm * 0.36
    if neck_width < user_height_cm * 0.08:
      neck_width = user_height_cm * 0.085
    neck_depth = distance(nose, midpoint(left_shoulder, right_shoulder)) * scale
    neck_depth = np.clip(neck_depth, 7.0, 8.5)
    a = neck_width/ 2
    b = neck_depth / 2
    neck_circ = np.pi * (3*(a + b) - np.sqrt((3*a + b)*(a + 3*b)))

    # Shoulder
    shoulder_width = distance(left_shoulder, right_shoulder) * 100 * scale

    # Chest
    chest_center = midpoint(left_shoulder, right_shoulder)
    back_center = midpoint(left_hip, right_hip)
    chest_depth = np.linalg.norm((chest_center - back_center)[[1, 2]]) * scale * 100
    chest_depth = np.clip(chest_depth, 16.0, 24.0)
    chest_width = np.linalg.norm(right_shoulder[:2] - left_shoulder[:2]) * scale * 100
    a, b = chest_width / 2, chest_depth / 2
    chest_circ = np.pi * (3*(a + b) - np.sqrt((3*a + b)*(a + 3*b)))

    # Arms
    upper_arm_left = distance(left_shoulder, left_elbow) * 100 * scale
    upper_arm_right = distance(right_shoulder, right_elbow) * 100 * scale
    lower_arm_left = distance(left_elbow, left_wrist) * 100 * scale
    lower_arm_right = distance(right_elbow, right_wrist) * 100 * scale
    arm_length = (upper_arm_left + lower_arm_left + upper_arm_right + lower_arm_right) / 2

    # Waist
    waist_ratio = 0.42
    left_waist = left_shoulder * (1 - waist_ratio) + left_hip * waist_ratio
    right_waist = right_shoulder * (1 - waist_ratio) + right_hip * waist_ratio
    waist_width = distance(left_waist, right_waist) * 100 * scale
    waist_circ = estimate_waist_circumference(waist_width)

    #hip
    def estimate_hip_width(left_hip, right_hip, shoulder_width, scale, scale_factor=0.22):
        spine_mid = (left_hip + right_hip) / 2

        def project_outward(hip, center, factor):
            direction = hip - center
            return hip + factor * direction

        left_proj = project_outward(left_hip, spine_mid, scale_factor)
        right_proj = project_outward(right_hip, spine_mid, scale_factor)

        projected_width = np.linalg.norm(left_proj[:2] - right_proj[:2]) * 100 * scale
        z_offset = np.clip(abs(left_hip[2] - right_hip[2]) * 100 * scale, 0, 4.0)
        corrected_width = np.sqrt(projected_width**2 + z_offset**2)

        lower_bound = shoulder_width * 0.75
        upper_bound = shoulder_width * 1.35
        fallback_width = shoulder_width * 1.05

        if corrected_width < lower_bound or corrected_width > upper_bound:
            return fallback_width, "fallback", spine_mid
        else:
            return corrected_width, "projected", spine_mid

    def estimate_hip_circumference(left_hip, right_hip, spine_mid, scale, hip_width_cm):
        hip_center = (left_hip + right_hip) / 2
        depth_vector = hip_center - spine_mid
        hip_depth = np.linalg.norm(depth_vector[[1, 2]]) * scale * 100
        hip_depth = np.clip(hip_depth, 16.0, 26.0)

        a, b = hip_width_cm / 2, hip_depth / 2
        hip_circ = np.pi * (3*(a + b) - np.sqrt((3*a + b)*(a + 3*b)))

        plausible_range = (80, 110)
        if hip_circ < plausible_range[0] or hip_circ > plausible_range[1]:
            return hip_circ, "outlier",None
        else:
            return hip_circ, "valid", hip_depth
    hip_width, hip_width_source, spine_mid = estimate_hip_width(left_hip, right_hip, shoulder_width, scale)
    hip_circ, hip_circ_source, hip_depth = estimate_hip_circumference(left_hip, right_hip, spine_mid, scale, hip_width)

    # Thigh
    left_thigh_mid = midpoint(left_hip, left_knee)
    right_thigh_mid = midpoint(right_hip, right_knee)
    thigh_width = distance(left_thigh_mid[:2], right_thigh_mid[:2]) * 100 * scale
    spine_mid = midpoint(left_hip, right_hip)
    thigh_center = midpoint(left_thigh_mid, right_thigh_mid)
    thigh_depth = np.linalg.norm((thigh_center - spine_mid)[[1, 2]]) * 100 * scale
    thigh_depth = np.clip(thigh_depth, 8.0, 12.0)
    a, b = thigh_width / 2, thigh_depth / 2
    thigh_circ = np.pi * (3*(a + b) - np.sqrt((3*a + b)*(a + 3*b)))

    # Inseam
    def estimate_inseam(hip, knee, ankle, scale, user_height_cm, tolerance=0.05):
        hip_to_knee = distance(hip, knee)
        knee_to_ankle = distance(knee, ankle)
        raw_inseam = (hip_to_knee + knee_to_ankle) * 100 * scale
        plausible_min = user_height_cm * 0.45
        plausible_max = user_height_cm * 0.50
        
        if raw_inseam < plausible_min:
            return raw_inseam, "short_or_compressed"
        elif raw_inseam > plausible_max * (1 + tolerance):
            return plausible_max, "capped"
        elif raw_inseam > plausible_max:
            return raw_inseam, "flagged_high"
        else:
            return raw_inseam, "measured"
    left_inseam, left_flag = estimate_inseam(left_hip, left_knee, left_ankle, scale, user_height_cm)
    right_inseam, right_flag = estimate_inseam(right_hip, right_knee, right_ankle, scale, user_height_cm)
    inseam = (left_inseam + right_inseam) / 2
    
     # --- Accuracy Components ---
    key_landmarks = [lm.LEFT_SHOULDER, lm.RIGHT_SHOULDER, lm.LEFT_HIP, lm.RIGHT_HIP,
                     lm.LEFT_KNEE, lm.RIGHT_KNEE, lm.LEFT_ANKLE, lm.RIGHT_ANKLE]
    visibility_scores = [results.pose_landmarks.landmark[l].visibility for l in key_landmarks]
    upper_coverage = sum([results.pose_landmarks.landmark[l].visibility > 0.5 for l in upper_landmarks]) / len(upper_landmarks)
    lower_coverage = sum([results.pose_landmarks.landmark[l].visibility > 0.5 for l in lower_landmarks]) / len(lower_landmarks)
    visible_ratio = np.mean(visibility_scores)

    shoulder_span = distance(left_shoulder, right_shoulder)
    hip_span = distance(left_hip, right_hip)
    pose_quality = np.clip(100 - abs(shoulder_span - hip_span) * 100, 60, 100)

    coverage = sum([v > 0.5 for v in visibility_scores])
    body_coverage_pct = (coverage / len(key_landmarks)) * 100

    vertical_vector = nose - right_ankle
    angle_score = np.clip(100 - abs(vertical_vector[0]) * 100, 70, 100)

    left_sym = distance(left_ear, left_shoulder)
    right_sym = distance(right_ear, right_shoulder)
    symmetry_diff = abs(left_sym - right_sym)
    landmark_symmetry_score = np.clip(100 - symmetry_diff * 100, 70, 100)
    percentile_alignment_score = percentile_alignment(hip_circ, 80, 110)
   
    accuracy_score = compute_accuracy_score(
        visible_ratio=visible_ratio,
        pose_quality=pose_quality,
        body_coverage_pct=body_coverage_pct,
        angle_score=angle_score,
        landmark_symmetry_score=landmark_symmetry_score,
        percentile_alignment_score=percentile_alignment_score
    )
    if lower_coverage < 0.5:
        penalty = (0.5 - lower_coverage) * 0.5 
        accuracy_score = max(accuracy_score - penalty, 0.5)

    return {
        "accuracy_score": accuracy_score,
        "neck": neck_circ,
        "shoulder": shoulder_width,
        "chest": chest_circ,
        "arm_length": arm_length,
        "waist": waist_circ,
        "hips": hip_circ,
        "thigh": thigh_circ,
        "inseam": inseam
    }

def get_cart_session_key(request):
    if not request.session.session_key:
        request.session.create()  
    return request.session.session_key