# EDL to Clip Name for DaVinci Resolve

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![DaVinci Resolve](https://img.shields.io/badge/DaVinci%20Resolve-Scripting%20API-233A51?logo=blackmagicdesign&logoColor=white)](https://www.blackmagicdesign.com/products/davinciresolve)
[![EDL](https://img.shields.io/badge/EDL-CMX%203600-4B8BBE)](https://en.wikipedia.org/wiki/Edit_Decision_List)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Скрипт сверяет события из EDL с клипами на видеодорожке `V1` текущего таймлайна DaVinci Resolve по таймкодам. Если количество клипов и все таймкоды совпадают, он переименовывает клипы именами из поля `FROM CLIP NAME` EDL.

## Возможности

- читает EDL в формате CMX 3600;
- получает FPS и стартовый таймкод открытого таймлайна;
- сравнивает количество и границы клипов на `V1`;
- не вносит изменений при любом несовпадении;
- переименовывает клипы через `TimelineItem.SetName()` или резервный метод Media Pool.

## Требования

- Python 3.11 или новее;
- DaVinci Resolve с доступным Scripting API;
- открытый проект и таймлайн в DaVinci Resolve;
- EDL с non-drop-frame таймкодами и целочисленной частотой кадров, например 24 или 25 fps.

## Установите Python 3.11:

```bash
brew install python@3.11
```
Эта команда установит интерпретатор и пакетный менеджер pip для этой версии.

Проверьте установку. Homebrew устанавливает исполняемый файл с уточняющим именем, чтобы не конфликтовать с другими версиями:

```bash
python3.11 --version
```
Вы должны увидеть что-то вроде Python 3.11.x.

## Установка зависимостей

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Настройка

1. Откройте нужный проект и таймлайн в DaVinci Resolve.
2. Разместите EDL в каталоге `test_data/` или в другом удобном месте.
3. Укажите путь к EDL при запуске скрипта. Частота кадров для парсера сейчас задана в [edl_to_clip_name_terminal.py](edl_to_clip_name_terminal.py) как `FPS_FOR_EDL = "24"`.

4. Убедитесь, что клипы для обработки находятся на видеодорожке `V1`.

## Запуск

Запускайте скрипт в окружении, где доступен модуль `DaVinciResolveScript` (например, из консоли DaVinci Resolve или настроенного окружения Resolve):

```bash
python edl_to_clip_name_terminal.py ./test_data/SOURCE_REQUEST_20260928.edl
```

Перед переименованием скрипт выведет найденные события EDL, клипы таймлайна и результат сверки. При разном количестве событий EDL и клипов на `V1` по умолчанию обрабатываются только пары до конца более короткого списка. Несовпадение входных или выходных таймкодов всегда останавливает выполнение.

Чтобы требовать точного совпадения количества событий EDL и клипов на `V1`, добавьте флаг `-s` или `--strict-count-match`:

```bash
python edl_to_clip_name_terminal.py ./test_data/SOURCE_REQUEST_20260928.edl -s
```

В строгом режиме несовпадение количества останавливает выполнение до проверки таймкодов и переименования.

## Проверка утилит таймкода

Для запуска встроенной самопроверки конвертации таймкодов:

```bash
python -m services.timecode
```

## Ограничения

- Обрабатывается только первая видеодорожка `V1`.
- Поддерживаются non-drop-frame таймкоды при целочисленном FPS; drop-frame и дробные частоты, включая 23.976 fps, пока не реализованы корректно.
- Скрипт меняет имена клипов в текущем открытом таймлайне. Перед запуском рекомендуется сохранить проект или создать резервную копию.

## Структура проекта

```text
.
├── edl_to_clip_name_terminal.py  # Сверка EDL и переименование клипов
├── LICENSE                        # Лицензия MIT
├── services/
│   └── timecode.py               # Преобразование таймкодов и кадров
├── test_data/                    # Примеры EDL
└── requirements.txt              # Зависимости Python
```

## Лицензия

Проект распространяется по лицензии [MIT](LICENSE).
