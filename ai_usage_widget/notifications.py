"""Notification threshold tracking."""

from dataclasses import dataclass


def classify_threshold(dominant: float) -> int:
    pct_value = int(dominant * 100)
    if pct_value >= 100:
        return 100
    if pct_value >= 90:
        return 90
    if pct_value >= 75:
        return 75
    return 0


@dataclass(slots=True)
class NotificationTracker:
    startup_sent: bool = False
    last_threshold: int = 0

    def next_threshold_notification(self, dominant: float) -> int | None:
        current_threshold = classify_threshold(dominant)
        if current_threshold < self.last_threshold:
            self.last_threshold = current_threshold
        if current_threshold > self.last_threshold:
            self.last_threshold = current_threshold
            return current_threshold
        return None
