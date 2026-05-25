import numpy as np
import pandas as pd

def detect_stable_segments(
        df, col, 
        smooth_window=30, #smmoth over 30s
        gradient_window=30, #gradient avergaed over 30s
        stable_threshold=0.02, #less than 0.02 deg is considered stable
        min_stable_length=120, #shoudl be stable for at least 2 minutes
        rise_threshold=0.07, #above 0.06 deg is considered rising
        lookback_window=600): #look back after 10 min for a rise
    df = df.copy()

    signal = df[col].rolling(window=smooth_window, min_periods=1).mean()
    gradient = signal.diff().fillna(0)
    gradient_smooth = gradient.rolling(window=gradient_window, min_periods=1, center=True).mean()

    stable = gradient_smooth.abs() < stable_threshold
    rising = gradient_smooth > rise_threshold

    start_marker_col = f"{col}_stable_start_marker"
    end_marker_col = f"{col}_stable_end_marker"
    segment_col = f"{col}_stable_segment"
    segment_id_col = f"{col}_segment_id"    

    df[start_marker_col] = np.nan
    df[end_marker_col] = np.nan
    df[segment_col] = False
    df[segment_id_col] = np.nan

    segment_id = (stable != stable.shift()).cumsum()
    stable_segments = []
    segment_number = 0

    for _, segment in df[stable].groupby(segment_id[stable]):
        if len(segment) < min_stable_length:
            continue

        start_idx = segment.index[0]
        end_idx = segment.index[-1]

        #check whetehr there is a rise before the stable segment
        lookback_start = max(0, start_idx - lookback_window)

        had_recent_rise = rising.loc[lookback_start:start_idx].any()

        if not had_recent_rise:
            continue

        max_stable_drift = 1.0
        segment_drift = abs(df.loc[end_idx, col] - df.loc[start_idx, col])

        if segment_drift > max_stable_drift:
            continue

        segment_number += 1

        stable_segments.append((start_idx, end_idx))

        #start marker
        df.loc[start_idx, start_marker_col] = df[col].max()
        #end marker
        df.loc[end_idx, end_marker_col] = df[col].max()
        #segment marker
        df.loc[start_idx:end_idx, segment_col] = True
        #segment ID
        df.loc[start_idx:end_idx, segment_id_col] = segment_number

    print(f"Detected {len(stable_segments)} stable segments in column {col}")

    return df

def smoothen(df, cols, window_size):
    df = df.copy()

    df[cols] = (df[cols].rolling(window=window_size, min_periods=1).mean())
    return df

