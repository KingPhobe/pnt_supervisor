"""Centralized keys for feature flags and numeric feature values."""


class FeatureFlag:
    TIMESTAMP_BACKWARDS = "timestamp_backwards"
    KINEMATIC_TIME_INVALID = "kinematic_time_invalid"
    TRACK_GEOMETRY_AMBIGUOUS = "track_geometry_ambiguous"
    HOVER_VALID = "hover_valid"
    LOW_MOTION_SUSPICIOUS = "low_motion_suspicious"
    HDOP_BAD = "hdop_bad"
    GEOMETRY_BAD = "geometry_bad"
    REACQ_UNSTABLE = "reacq_unstable"


class FeatureValue:
    GAP_S = "gap_s"
    GAP_RATIO = "gap_ratio"
    STALE_COUNT = "stale_count"
    FROZEN_SOLUTION_COUNT = "frozen_solution_count"
    FIX_VALID_NUMERIC = "fix_valid_numeric"
    NUM_SATS = "num_sats"
    HDOP = "hdop"
    FIX_TRANSITION_COUNT_SHORT_WINDOW = "fix_transition_count_short_window"
    TIME_SINCE_LAST_INVALID = "time_since_last_invalid"
    STATE_FLAP_COUNT = "state_flap_count"
    JUMP_DISTANCE_M = "jump_distance_m"
    FD_SPEED_MPS = "fd_speed_mps"
    SPEED_MISMATCH_MPS = "speed_mismatch_mps"
    COURSE_TRACK_MISMATCH_DEG = "course_track_mismatch_deg"
    CLIMB_MISMATCH_MPS = "climb_mismatch_mps"
    TURN_RATE_DEGPS = "turn_rate_degps"
