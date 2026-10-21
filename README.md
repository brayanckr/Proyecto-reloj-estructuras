# Analog Clock in Python

Data Structures course project: a hand-driven (analog) clock built only with Python.
No HTML, no CSS and no third-party libraries.

## Requirements
- Python 3.8+ (with `tkinter`, which is bundled with the standard Python installer)

## Run
```bash
python clock.py
```

## Features
- Analog clock with hour, minute and second hands
- Small digital display with the current date
- 12h / 24h format toggle
- Light / dark theme toggle
- Alarms (earliest alarm rings first)
- Stopwatch with laps

## Data structures (implemented from scratch)
| Structure | Used for |
|---|---|
| Circular doubly linked list | The 12 hour marks and 60 minute ticks used to draw the dial |
| Priority queue (sorted linked list) | Alarms: the front node is always the next alarm to ring |
| Stack (LIFO) | Stopwatch laps: the newest lap is shown first |

## Standard library modules
- `tkinter` – graphical frontend
- `time` – current time
- `math` – hand angles (sin / cos)

## Project structure
```
clock.py    # data structures + GUI + main loop
README.md
```
