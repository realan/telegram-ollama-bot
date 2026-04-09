from __future__ import annotations

MAX_TELEGRAM_MESSAGE_LENGTH = 4096


def split_text(text: str, limit: int = MAX_TELEGRAM_MESSAGE_LENGTH) -> list[str]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    if text == "":
        return [""]
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""

    for part in text.split():
        if len(part) > limit:
            if current:
                chunks.append(current)
                current = ""
            for start in range(0, len(part), limit):
                chunks.append(part[start:start + limit])
            continue

        candidate = part if not current else f"{current} {part}"
        if len(candidate) <= limit:
            current = candidate
            continue

        chunks.append(current)
        current = part

    if current:
        chunks.append(current)

    return chunks

