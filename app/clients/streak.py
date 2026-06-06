from __future__ import annotations

from app.schemas import StreakData


def compute_streak_from_calendar(weeks: list[dict]) -> StreakData:
    daily: list[int] = []
    for week in weeks:
        for day in week.get("contributionDays", []):
            daily.append(int(day.get("contributionCount", 0)))

    current = 0
    for v in reversed(daily):
        if v > 0:
            current += 1
        else:
            break

    longest = 0
    run = 0
    for v in daily:
        if v > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    return StreakData(current_streak=current, longest_streak=longest)
