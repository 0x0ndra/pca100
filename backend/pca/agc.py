"""Automatic gain control and measurement stability detection."""

MAX_RATIO = 8.0
# Hold the current integration while the peak sits near target: every retune
# calls set_integration_time and the acquisition already in flight is exposed
# with the old timing, so churn turns a steady light into luminance jumps.
# Asymmetric on purpose: the bright side (low ratio) keeps the peak safely
# below the 95 % saturation check even at the edge of the band.
HOLD_RATIO_LOW = 0.92
HOLD_RATIO_HIGH = 1.15


def next_integration_us(
    peak_counts: float,
    current_us: int,
    target_counts: float,
    limits_us: tuple[int, int],
    saturated: bool = False,
) -> int:
    # A clipped sensor reports the ADC rail as the peak, which understates the
    # real overexposure and would cap the step at target/rail (~15 %); a
    # dark->bright transition then takes minutes to recover. Step down hard.
    if saturated:
        ratio = 1.0 / MAX_RATIO
    else:
        ratio = MAX_RATIO if peak_counts <= 0 else target_counts / peak_counts
        if HOLD_RATIO_LOW <= ratio <= HOLD_RATIO_HIGH:
            return min(max(current_us, limits_us[0]), limits_us[1])
        ratio = min(max(ratio, 1.0 / MAX_RATIO), MAX_RATIO)
    proposed = int(current_us * ratio)
    return min(max(proposed, limits_us[0]), limits_us[1])


def is_saturated(peak_counts: float, saturation_level: float) -> bool:
    return peak_counts >= 0.95 * saturation_level
