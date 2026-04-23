"""Exponential backoff schedule for quota-aware worker recovery.

Implements exponential backoff with cap for worker retry after quota exhaustion.
Usage:
    from backoff import compute_backoff, format_duration

    retry_count = worker_data['quota_retry_count']
    backoff_sec = compute_backoff(retry_count)
    print(f"Waiting {format_duration(backoff_sec)} before retry")
"""

BACKOFF_SCHEDULE = [
    600,     # retry 0 (1st failure): 10 minutes
    1200,    # retry 1 (2nd failure): 20 minutes
    2400,    # retry 2 (3rd failure): 40 minutes
    7200,    # retry 3+: 2 hours (cap)
]


def compute_backoff(retry_count: int) -> int:
    """Calculate backoff duration in seconds based on retry count.

    Args:
        retry_count: Number of previous quota failures (0 = first failure)

    Returns:
        Backoff duration in seconds, capped at 2 hours
    """
    if retry_count < 0:
        retry_count = 0
    idx = min(retry_count, len(BACKOFF_SCHEDULE) - 1)
    return BACKOFF_SCHEDULE[idx]


def format_duration(seconds: int) -> str:
    """Format seconds as human-readable duration.

    Examples:
        600 -> '10m'
        1200 -> '20m'
        2400 -> '40m'
        7200 -> '2h'
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds / 3600
        if hours == int(hours):
            return f"{int(hours)}h"
        else:
            return f"{hours:.1f}h"
