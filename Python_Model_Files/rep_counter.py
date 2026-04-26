# rep_counter.py
# Counts exercise reps using joint angle thresholds.
# Uses MoveNet keypoint indices.
#
# Exercises: pushup, benchpress, squat
# Label encoding (must match label_encoder.pkl):
#   0 = pushup
#   1 = benchpress
#   2 = squat
#
# Camera is to the RIGHT of the person — right side joints used.
#
# MoveNet keypoint indices:
#   0=nose   1=left_eye   2=right_eye   3=left_ear   4=right_ear
#   5=left_shoulder   6=right_shoulder
#   7=left_elbow      8=right_elbow
#   9=left_wrist     10=right_wrist
#  11=left_hip       12=right_hip
#  13=left_knee      14=right_knee
#  15=left_ankle     16=right_ankle

import numpy as np
from collections import deque

# MoveNet keypoint indices
KP = {
    "nose":            0,
    "left_eye":        1,  "right_eye":       2,
    "left_ear":        3,  "right_ear":       4,
    "left_shoulder":   5,  "right_shoulder":  6,
    "left_elbow":      7,  "right_elbow":     8,
    "left_wrist":      9,  "right_wrist":    10,
    "left_hip":       11,  "right_hip":      12,
    "left_knee":      13,  "right_knee":     14,
    "left_ankle":     15,  "right_ankle":    16,
}

# Camera to the RIGHT — use right side joints
EXERCISE_JOINTS = {
    "benchpress": ("right_shoulder", "right_elbow", "right_wrist"),
    "pushup":     ("right_shoulder", "right_elbow", "right_wrist"),
    "squat":      ("right_hip",      "right_knee",  "right_ankle"),
}

# Must match label_encoder.pkl — verify with:
# joblib.load('outputs/label_encoder.pkl').classes_
CLASS_NAMES = {
    0: "benchpress",
    1: "pushup",
    2: "squat",
}

# ── Tuning parameters ──────────────────────────────────────────────────────────
MIN_CONF          = 0.15  # minimum keypoint confidence for MoveNet
CONFIRM_FRAMES    = 3     # frames to confirm exercise before starting — low since model is accurate
CLASS_LOCK_FRAMES = 20    # frames of different class needed to unlock — high to prevent mid-rep switching
CONF_GATE         = 0.80  # classifier confidence required to trigger unlock
NONE_TOLERANCE    = 8     # frames of missing keypoints before resetting
STILL_TIMEOUT     = 120   # frames of no movement before returning to IDLE (~4s at 30fps)
STILL_THRESH      = 2.0   # degrees — movement below this = still
COOLDOWN_FRAMES   = 10    # frames to wait after counting a rep before counting another

# Exercise-specific angle thresholds — tuned for accurate model
# These are absolute degree thresholds, not relative
THRESHOLDS = {
    # Pushup: arms nearly straight at top (~160°), bent at bottom (~70°)
    "pushup":     {"top": 150, "bottom": 90},
    # Bench press: arms nearly straight at top (~160°), bent at bottom (~70°)
    "benchpress": {"top": 150, "bottom": 90},
    # Squat: legs nearly straight at top (~160°), bent at bottom (~90°)
    "squat":      {"top": 150, "bottom": 130},
}
# ──────────────────────────────────────────────────────────────────────────────


def compute_angle(a, b, c):
    """
    Angle at joint b given three MoveNet keypoints [y, x, confidence].
    Returns degrees or None if any keypoint is below MIN_CONF.
    """
    if a[2] < MIN_CONF or b[2] < MIN_CONF or c[2] < MIN_CONF:
        return None
    va    = np.array([a[1] - b[1], a[0] - b[0]])
    vc    = np.array([c[1] - b[1], c[0] - b[0]])
    denom = np.linalg.norm(va) * np.linalg.norm(vc) + 1e-6
    cos_a = np.dot(va, vc) / denom
    return float(np.degrees(np.arccos(np.clip(cos_a, -1.0, 1.0))))


class RepCounter:
    """
    Counts reps for pushup, benchpress, squat using absolute angle thresholds.
    Designed for high-accuracy classifier — uses tight confirmation windows
    and absolute thresholds rather than relative self-calibration.
    """

    IDLE      = "IDLE"
    CONFIRMED = "CONFIRMED"
    AT_TOP    = "AT_TOP"
    AT_BOTTOM = "AT_BOTTOM"
    COOLDOWN  = "COOLDOWN"

    def __init__(self):
        self.rep_count = 0
        self._reset_state()

    def reset(self):
        """Full reset including rep count."""
        self.rep_count = 0
        self._reset_state()

    def _reset_state(self):
        self.state              = self.IDLE
        self.current_class      = None
        self.confirm_count      = 0
        self.class_change_count = 0
        self.none_count         = 0
        self.still_frames       = 0
        self.last_angle         = None
        self.cooldown_frames    = 0

    def _get_angle(self, exercise_name, keypoints):
        if exercise_name not in EXERCISE_JOINTS:
            return None
        a, b, c = [keypoints[KP[n]] for n in EXERCISE_JOINTS[exercise_name]]
        return compute_angle(a, b, c)

    def update(self, exercise_class_idx, keypoints, confidence=1.0):
        """
        Call every frame.

        Args:
            exercise_class_idx: int from MLP classifier
            keypoints:          np.array (17, 3) — [y, x, confidence]
            confidence:         float — classifier output probability

        Returns:
            (rep_count, state, angle)
        """
        name  = CLASS_NAMES.get(exercise_class_idx)
        angle = self._get_angle(name, keypoints) if name else None
        thresh = THRESHOLDS.get(name, None)

        # ── Cooldown ───────────────────────────────────────────────────────
        if self.state == self.COOLDOWN:
            self.cooldown_frames -= 1
            if self.cooldown_frames <= 0:
                self.state = self.AT_TOP
            return self.rep_count, self.state, angle

        # ── IDLE: wait for consistent exercise detection ───────────────────
        if self.state == self.IDLE:
            if exercise_class_idx == self.current_class:
                self.confirm_count += 1
            else:
                self.current_class = exercise_class_idx
                self.confirm_count = 1

            if self.confirm_count >= CONFIRM_FRAMES and angle is not None:
                self.state              = self.CONFIRMED
                self.class_change_count = 0
                self.none_count         = 0
                self.still_frames       = 0
                self.last_angle         = angle
            return self.rep_count, self.state, angle

        # ── Class lock — ignore brief misclassifications ───────────────────
        if exercise_class_idx != self.current_class:
            if confidence >= CONF_GATE:
                self.class_change_count += 1
            if self.class_change_count > CLASS_LOCK_FRAMES:
                self._reset_state()
                return self.rep_count, self.state, angle
            return self.rep_count, self.state, angle
        else:
            self.class_change_count = 0

        # ── Handle missing keypoints ───────────────────────────────────────
        if angle is None:
            self.none_count += 1
            if self.none_count > NONE_TOLERANCE:
                self._reset_state()
            return self.rep_count, self.state, angle
        self.none_count = 0

        # ── Stillness detection ────────────────────────────────────────────
        if self.last_angle is not None:
            if abs(angle - self.last_angle) < STILL_THRESH:
                self.still_frames += 1
            else:
                self.still_frames = 0
        self.last_angle = angle

        if self.still_frames > STILL_TIMEOUT:
            self._reset_state()
            return self.rep_count, self.state, angle

        # ── CONFIRMED: find starting position ─────────────────────────────
        if self.state == self.CONFIRMED:
            if thresh and angle >= thresh["top"]:
                self.state = self.AT_TOP
            return self.rep_count, self.state, angle

        # ── AT_TOP: wait for descent to bottom ────────────────────────────
        if self.state == self.AT_TOP:
            if thresh and angle <= thresh["bottom"]:
                self.state = self.AT_BOTTOM
            return self.rep_count, self.state, angle

        # ── AT_BOTTOM: wait for return to top = rep complete ──────────────
        if self.state == self.AT_BOTTOM:
            if thresh and angle >= thresh["top"]:
                self.rep_count      += 1
                self.state           = self.COOLDOWN
                self.cooldown_frames = COOLDOWN_FRAMES
            return self.rep_count, self.state, angle

        return self.rep_count, self.state, angle

    def get_display_info(self):
        name = CLASS_NAMES.get(self.current_class, "none")
        thresh = THRESHOLDS.get(name, {})
        return {
            "reps":        self.rep_count,
            "state":       self.state,
            "exercise":    name,
            "top_thresh":  thresh.get("top"),
            "bot_thresh":  thresh.get("bottom"),
        }
