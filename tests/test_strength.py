from datetime import timedelta

from membrain.models import Memory, MemoryStatus, utc_now
from membrain.strength import current_strength, reinforce, ARCHIVE_THRESHOLD


def test_strength_decays_and_reinforces() -> None:
    memory = Memory(
        id=1, content="project uses bun", summary="project uses bun",
        strength=0.8,
        last_accessed_at=utc_now() - timedelta(days=30),
    )
    decayed = current_strength(memory)
    # Adaptive decay: effective_d = 0.02 * (2-R), so decays faster than linear
    assert 0.1 < decayed < 0.8
    assert reinforce(memory) > decayed


def test_adaptive_decay_weaker_faster() -> None:
    """Weak memories decay faster than strong ones."""
    now = utc_now()
    strong = Memory(id=1, content="strong", strength=0.9,
                    last_accessed_at=now - timedelta(days=10))
    weak = Memory(id=2, content="weak", strength=0.3,
                  last_accessed_at=now - timedelta(days=10))

    strong_R = current_strength(strong, now)
    weak_R = current_strength(weak, now)

    # Both decayed, but weak should lose proportionally more
    strong_loss = 0.9 - strong_R
    weak_loss = 0.3 - weak_R
    weak_ratio = weak_loss / 0.3
    strong_ratio = strong_loss / 0.9
    assert weak_ratio >= strong_ratio, f"weak_ratio={weak_ratio:.4f} < strong_ratio={strong_ratio:.4f}"


def test_reinforce_gradual_approach() -> None:
    """Reinforce moves toward 1.0 but doesn't jump directly."""
    memory = Memory(id=1, content="test", strength=0.6)
    r1 = reinforce(memory)
    assert 0.6 < r1 < 1.0
    # Second reinforce should be higher
    memory.strength = r1
    r2 = reinforce(memory)
    assert r2 > r1


def test_archive_threshold() -> None:
    """ARCHIVE_THRESHOLD is a small positive value."""
    assert 0 < ARCHIVE_THRESHOLD < 0.1


def test_constants() -> None:
    from membrain.strength import DECAY_RATE, INITIAL_STRENGTH, REINFORCEMENT_GAIN
    assert 0 < DECAY_RATE < 0.1
    assert 0.5 < INITIAL_STRENGTH <= 1.0
    assert 0 < REINFORCEMENT_GAIN < 1.0
