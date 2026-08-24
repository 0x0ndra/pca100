from pca.agc import is_saturated, next_integration_us

LIMITS = (1_000, 6_000_000)


def test_scales_toward_target() -> None:
    assert next_integration_us(27_850, 100_000, 55_700, LIMITS) == 200_000


def test_ratio_capped() -> None:
    assert next_integration_us(100, 100_000, 55_700, LIMITS) == 800_000


def test_clamped_to_limits() -> None:
    assert next_integration_us(55_700, 500, 55_700, LIMITS) == 1_000
    assert next_integration_us(1.0, 6_000_000, 55_700, LIMITS) == 6_000_000


def test_dark_input_grows() -> None:
    assert next_integration_us(0.0, 100_000, 55_700, LIMITS) == 800_000


def test_saturated_steps_down_by_max_ratio() -> None:
    # Clipped peak 65_535 would suggest a mild 55_700/65_535 step; the real
    # signal may be orders of magnitude over, so saturation forces a full-step
    # descent: 6 s -> 750 ms instead of ~5.1 s.
    assert next_integration_us(65_535, 6_000_000, 55_700, LIMITS, saturated=True) == 750_000
    assert next_integration_us(65_535, 6_000_000, 55_700, LIMITS) == 5_099_565


def test_holds_integration_while_peak_is_near_target() -> None:
    # Small drift around target must not retune: every retune calls
    # set_integration_time and pollutes the next scan, so the luminance
    # display jumps while the light is effectively steady.
    assert next_integration_us(52_000, 700_000, 55_700, LIMITS) == 700_000
    assert next_integration_us(59_000, 700_000, 55_700, LIMITS) == 700_000


def test_hold_band_still_clamps_to_limits() -> None:
    assert next_integration_us(55_700, 500, 55_700, LIMITS) == 1_000


def test_adjusts_once_peak_leaves_the_hold_band() -> None:
    assert next_integration_us(40_000, 700_000, 55_700, LIMITS) != 700_000
    assert next_integration_us(64_000, 700_000, 55_700, LIMITS) != 700_000


def test_saturation() -> None:
    assert is_saturated(65_535, 65_535)
    assert is_saturated(62_300, 65_535)
    assert not is_saturated(60_000, 65_535)
