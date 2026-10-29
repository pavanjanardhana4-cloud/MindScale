def process_keystrokes(events):
    """
    Processes a list of keystroke events into behavioral metrics.
    events: List of dicts with {'type': 'keydown'|'keyup', 'key': str, 'ts': ms}
    """
    if not events:
        return {
            "backspace_count": 0,
            "total_keystrokes": 0,
            "typing_duration": 0,
            "pause_time": 0,
            "avg_speed": 0,
            "hesitation_ratio": 0,
            "correction_ratio": 0
        }
    
    # Filter only keydown for most metrics
    keydowns = [e for e in events if e['type'] == 'keydown']
    total_keys = len(keydowns)
    backspaces = len([e for e in keydowns if e['key'] == 'Backspace'])
    
    start_ts = events[0]['ts']
    end_ts = events[-1]['ts']
    duration_ms = end_ts - start_ts
    duration_sec = duration_ms / 1000.0
    
    # Pauses (> 1.5s)
    pause_threshold = 1500 # ms
    total_pause_ms = 0
    pause_intervals = []
    
    for i in range(1, len(keydowns)):
        gap = keydowns[i]['ts'] - keydowns[i-1]['ts']
        if gap > pause_threshold:
            total_pause_ms += gap
            pause_intervals.append(gap)
            
    # Metrics
    avg_speed = total_keys / duration_sec if duration_sec > 0 else 0
    hesitation_ratio = total_pause_ms / duration_ms if duration_ms > 0 else 0
    correction_ratio = backspaces / total_keys if total_keys > 0 else 0
    
    return {
        "backspace_count": backspaces,
        "total_keystrokes": total_keys,
        "typing_duration": round(duration_sec, 2),
        "pause_time": round(total_pause_ms / 1000.0, 2),
        "avg_speed": round(avg_speed, 2),
        "hesitation_ratio": round(hesitation_ratio, 3),
        "correction_ratio": round(correction_ratio, 3)
    }
