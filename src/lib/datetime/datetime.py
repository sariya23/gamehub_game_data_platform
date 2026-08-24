import re
from datetime import date, datetime


RU_MONTHS = {
    "янв": 1,
    "января": 1,
    "фев": 2,
    "февраля": 2,
    "мар": 3,
    "марта": 3,
    "апр": 4,
    "апреля": 4,
    "май": 5,
    "мая": 5,
    "июн": 6,
    "июня": 6,
    "июл": 7,
    "июля": 7,
    "авг": 8,
    "августа": 8,
    "сен": 9,
    "сент": 9,
    "сентября": 9,
    "окт": 10,
    "октября": 10,
    "ноя": 11,
    "ноября": 11,
    "дек": 12,
    "декабря": 12,
}


def parse_release_date_from_human(value: str) -> date:
    normalized = value.strip().lower().replace("ё", "е")
    match = re.fullmatch(
        r"(\d{1,2})\s+([а-я]+)\.?\s+(\d{4})(?:\s*г\.?)?",
        normalized,
    )
    if match:
        day, month_name, year = match.groups()
        month = RU_MONTHS.get(month_name)
        if month is not None:
            return date(int(year), month, int(day))

    formats = (
        "%d %b, %Y",   # 1 May, 2003
        "%b %d, %Y",   # May 1, 2003
        "%d %B, %Y",
        "%B %d, %Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"unsupported release date format: {value!r}")
