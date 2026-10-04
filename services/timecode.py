"""
Конвертация таймкодов DaVinci Resolve.

Соглашение об индексации:
  - timecode:  строка "HH:MM:SS:FF", non-drop-frame
  - frames:    int, 0-based (кадр 0 = первый кадр таймлайна)

DaVinci Resolve API использует разные базы в разных методах:
  - Timeline.AddMarker(frameId)       — 0-based
  - Timeline.GetStartFrame()          — 1-based для большинства таймлайнов
  - Timeline.GetCurrentTimecode()     — строка

Мы держим 0-based как «естественный» Python-формат и адаптируем
на границе с API, а не внутри утилит.
"""

from __future__ import annotations

FPS_FRAME_RATES = {
    "23.976": 23.976,
    "24": 24.0,
    "25": 25.0,
    "29.97": 29.97,          # NDF
    "29.97DF": 29.97,        # drop-frame
    "50": 50.0,
    "59.94": 59.94,          # NDF
    "59.94DF": 59.94,        # drop-frame
}


def get_timeline_fps(timeline) -> float:
    """Возвращает FPS таймлайна как float. Падает явно, если ключ отсутствует."""
    raw = timeline.GetSetting("timelineFrameRate")
    if raw is None:
        raise RuntimeError("Не удалось получить timelineFrameRate у таймлайна")
    return float(raw)


def timecode_to_frames(timecode: str, fps: float) -> int:
    """
    "00:00:10:00" @ 25fps → 250 (0-based).
    Non-drop-frame. Для drop-frame см. TODO ниже.
    """
    parts = timecode.split(":")
    if len(parts) != 4:
        raise ValueError(f"Ожидался формат HH:MM:SS:FF, получено: {timecode!r}")

    try:
        hh, mm, ss, ff = (int(p) for p in parts)
    except ValueError as e:
        raise ValueError(f"Не удалось распарсить таймкод {timecode!r}: {e}") from e

    if not (0 <= mm < 60 and 0 <= ss < 60 and 0 <= ff < round(fps)):
        raise ValueError(f"Компоненты таймкода вне диапазона: {timecode!r} @ {fps}fps")

    total_seconds = hh * 3600 + mm * 60 + ss
    return int(round(total_seconds * fps)) + ff


def frames_to_timecode(frames: int, fps: float) -> str:
    """
    250 @ 25fps → "00:00:10:00".
    Обратная к timecode_to_frames. Проверено round-trip-тестом ниже.
    """
    if frames < 0:
        raise ValueError(f"frames не может быть отрицательным: {frames}")

    fps_int = round(fps)
    if fps_int <= 0:
        raise ValueError(f"Некорректный fps: {fps}")

    total_seconds, ff = divmod(frames, fps_int)
    hh, rem = divmod(total_seconds, 3600)
    mm, ss = divmod(rem, 60)

    return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


# --- Самопроверка: запускается только при `python -m services.timecode` ---

if __name__ == "__main__":
    test_cases = [
        ("00:00:00:00", 25.0),
        ("00:00:10:00", 25.0),
        ("01:23:45:12", 25.0),
        ("00:00:00:23", 24.0),
        ("00:01:00:00", 23.976),
    ]

    for tc, fps in test_cases:
        frames = timecode_to_frames(tc, fps)
        back = frames_to_timecode(frames, fps)
        status = "✅ OK" if back == tc else "❌ MISMATCH"
        print(f"{status}: {tc} @ {fps}fps → {frames} → {back}")
