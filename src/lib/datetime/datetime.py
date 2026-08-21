from datetime import date, datetime


def parse_release_date_from_human(value: str) -> date:
    formats = (
        "%d %b, %Y",   # 1 May, 2003
        "%b %d, %Y",   # May 1, 2003
        "%d %B, %Y",
        "%B %d, %Y",
    )

    for fmt in formats:
        return datetime.strptime(value, fmt).date()
