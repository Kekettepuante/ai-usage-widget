from ai_usage_widget.notifications import NotificationTracker, classify_threshold


def test_classify_threshold():
    assert classify_threshold(0.10) == 0
    assert classify_threshold(0.75) == 75
    assert classify_threshold(0.91) == 90
    assert classify_threshold(1.00) == 100


def test_notification_tracker_rearms_when_usage_drops():
    tracker = NotificationTracker(startup_sent=True)

    assert tracker.next_threshold_notification(0.80) == 75
    assert tracker.next_threshold_notification(0.82) is None
    assert tracker.next_threshold_notification(0.95) == 90
    assert tracker.next_threshold_notification(0.40) is None
    assert tracker.last_threshold == 0
    assert tracker.next_threshold_notification(0.78) == 75
