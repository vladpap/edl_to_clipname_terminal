import argparse
import sys
import os
from edl import Parser


os.environ["RESOLVE_SCRIPT_API"] = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
os.environ["RESOLVE_SCRIPT_LIB"] = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/")


from services.timecode import get_timeline_fps, timecode_to_frames, frames_to_timecode


def parse_args():
    parser = argparse.ArgumentParser(
        description="Сверяет EDL с клипами V1 и переименовывает совпавшие клипы."
    )
    parser.add_argument("edl_path", help="Путь к EDL-файлу")
    parser.add_argument(
        "-s",
        "--strict-count-match",
        action="store_true",
        help="остановить выполнение, если количество событий EDL и клипов V1 различается",
    )
    return parser.parse_args()


args = parse_args()


# --- Получаем объект Resolve ---
try:
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")
except ImportError:
    resolve = globals().get("resolve")

if not resolve:
    print("⛔ Не удалось подключиться к DaVinci Resolve.")
    sys.exit(1)

project = resolve.GetProjectManager().GetCurrentProject()
timeline = project.GetCurrentTimeline()
if not timeline:
    print("Нет открытого таймлайна.")
    sys.exit(1)


# --- Параметры таймлайна ---
fps = get_timeline_fps(timeline)
start_tc = timeline.GetStartTimecode()          # например, "01:00:00:00"
start_frame_offset = timecode_to_frames(start_tc, fps)  # смещение в кадрах

print(f"FPS: {fps}, стартовый TC: {start_tc}, offset: {start_frame_offset} кадров")


def item_frames_to_tc(frame_number: int) -> str:
    """GetStart()/GetEnd() возвращают абсолютный кадр с учётом стартового TC."""
    return frames_to_timecode(frame_number, fps)


# --- 1. Парсим EDL ---
FPS_FOR_EDL = "24"               # ← формат для библиотеки edl (см. её док)

parser = Parser(FPS_FOR_EDL)
with open(args.edl_path, "r", encoding="utf-8") as f:
    edl = parser.parse(f)

edl_events = []
for event in edl.events:
    edl_events.append({
        "name": event.clip_name or "",
        "in":  str(event.rec_start_tc),
        "out": str(event.rec_end_tc),
    })

print(f"\nEDL: {len(edl_events)} событий")
for e in edl_events:
    print(f"  {e['in']} – {e['out']}  →  {e['name']}")


# --- 2. Читаем клипы с таймлайна ---
track_items = timeline.GetItemListInTrack("video", 1)   # V1
if not track_items:
    print("На V1 нет клипов.")
    sys.exit(1)

timeline_items = []
for item in track_items:
    timeline_items.append({
        "item": item,
        "name": item.GetName(),
        "in":  item_frames_to_tc(item.GetStart()),
        "out": item_frames_to_tc(item.GetEnd()),
    })

print(f"\nТаймлайн: {len(timeline_items)} клипов на V1")
for t in timeline_items:
    print(f"  {t['in']} – {t['out']}  →  {t['name']}")


# --- 3. Сверка количества ---
if len(edl_events) != len(timeline_items):
    print(f"\n⚠️ Несовпадение по количеству: EDL={len(edl_events)}, Timeline={len(timeline_items)}")
    if args.strict_count_match:
        print("Строгая проверка количества включена. Выполнение остановлено.")
        sys.exit(1)
    print(
        "⚠️ Продолжаем: будут проверены и переименованы только первые "
        f"{min(len(edl_events), len(timeline_items))} пар. Остальные клипы и события будут пропущены."
    )
else:
    print("\n✅ Количество совпадает. Проверяем таймкоды...")

# --- 4. Сверка таймкодов ---
mismatches = []
for i, (edl_ev, tl_item) in enumerate(zip(edl_events, timeline_items)):
    if edl_ev["in"] != tl_item["in"] or edl_ev["out"] != tl_item["out"]:
        mismatches.append((i, edl_ev, tl_item))

if mismatches:
    print("\n❌ Найдены несовпадения по таймкодам:")
    for i, e, t in mismatches:
        print(f"  #{i}: EDL [{e['in']}–{e['out']}] ≠ TL [{t['in']}–{t['out']}]  «{t['name']}»")
    sys.exit(1)

print("✅ Все таймкоды совпадают. Переименовываем...")


# --- 5. Переименование ---
for edl_ev, tl_item in zip(edl_events, timeline_items):
    new_name = edl_ev["name"]
    if not new_name:
        print(f"  ⚠ Пропуск (пустое имя): {tl_item['name']}")
        continue

    item = tl_item["item"]
    try:
        success = item.SetName(new_name)            # Resolve 20.2+
    except AttributeError:
        mp_item = item.GetMediaPoolItem()           # fallback
        success = mp_item.SetClipProperty("Clip Name", new_name) if mp_item else False

    mark = "✅" if success else "❌"
    print(f"  {mark} {tl_item['name']}  →  {new_name}")

print("\nГотово.")
