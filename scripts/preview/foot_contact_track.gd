extends RefCounted
## Deterministic world-space footsteps: planted feet do not travel with the hips.
## Used by the 5-second walking quality probe, not Musashi's final animation.

const PERIOD: float = 1.20
const STANCE_FRACTION: float = 0.64
const FOOT_LIFT: float = 0.077
const ANKLE_HEIGHT: float = 0.198
const LANDING_OFFSET: float = 0.33


static func sample(time_seconds: float, foot_index: int, x0: float, speed: float, lateral_z: float) -> Dictionary:
    var offset: float = 0.0 if foot_index == 0 else 0.5
    var total_phase: float = time_seconds / PERIOD + offset
    var cycle_index: int = floori(total_phase)
    var phase: float = total_phase - float(cycle_index)
    var contact_time: float = (float(cycle_index) - offset) * PERIOD
    var contact_x: float = x0 + speed * contact_time + LANDING_OFFSET
    var x: float = contact_x
    var height: float = ANKLE_HEIGHT
    var planted: bool = phase < STANCE_FRACTION
    if not planted:
        var swing: float = (phase - STANCE_FRACTION) / (1.0 - STANCE_FRACTION)
        var curved: float = swing * swing * (3.0 - 2.0 * swing)
        x = lerpf(contact_x, contact_x + speed * PERIOD, curved)
        height += FOOT_LIFT * pow(sin(PI * swing), 2.0)
    # Slight heel-to-toe roll rather than keeping each shoe perfectly rigid.
    var pitch_degrees: float = 0.0
    if planted:
        if phase < 0.13:
            var heel: float = 1.0 - phase / 0.13
            pitch_degrees = 8.0 * heel * heel * (3.0 - 2.0 * heel)
        elif phase > 0.50:
            var toe: float = (phase - 0.50) / (STANCE_FRACTION - 0.50)
            pitch_degrees = -7.0 * toe * toe * (3.0 - 2.0 * toe)
    else:
        var swing_phase: float = (phase - STANCE_FRACTION) / (1.0 - STANCE_FRACTION)
        pitch_degrees = 3.0 * pow(sin(PI * swing_phase), 2.0)

    return {
        "position": Vector3(x, height, lateral_z),
        "planted": planted,
        "phase": phase,
        "anchor_x": contact_x,
        "roll_degrees": pitch_degrees,
    }
