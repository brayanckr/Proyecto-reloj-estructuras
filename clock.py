"""
Analog + Digital Clock with Python (Data Structures project)

Only Python is used: no HTML, no CSS, no third-party libraries.
Frontend: tkinter (bundled with Python). Time and math come from the
standard library.

Data structures implemented by hand:
  - CircularDoublyLinkedList : holds the 12 hour marks / 60 minute ticks
                               and drives how the dial is drawn.
  - AlarmQueue               : sorted linked list used as a priority queue
                               (earliest alarm is always at the front).
  - LapStack                 : stack (LIFO) that stores stopwatch laps.

Extra features (beyond the basic clock):
  - Digital display with date and 12h / 24h toggle
  - Light / dark theme toggle
  - Alarms (priority queue)
  - Stopwatch with laps (stack)
"""

import math
import time
import tkinter as tk


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class DNode:
    """Node of a doubly linked list."""

    def __init__(self, value):
        self.value = value
        self.next = None
        self.prev = None


class CircularDoublyLinkedList:
    """Circular doubly linked list: the last node points back to the first."""

    def __init__(self):
        self.head = None
        self.size = 0

    def append(self, value):
        node = DNode(value)
        if self.head is None:
            node.next = node
            node.prev = node
            self.head = node
        else:
            tail = self.head.prev
            tail.next = node
            node.prev = tail
            node.next = self.head
            self.head.prev = node
        self.size += 1

    def __iter__(self):
        current = self.head
        for _ in range(self.size):
            yield current.value
            current = current.next


class SNode:
    """Node of a singly linked list."""

    def __init__(self, key, label):
        self.key = key          # minutes since midnight
        self.label = label      # text "HH:MM"
        self.next = None


class AlarmQueue:
    """Priority queue (sorted linked list): smallest time is served first."""

    def __init__(self):
        self.front = None
        self.size = 0

    def is_empty(self):
        return self.front is None

    def insert(self, key, label):
        """Insert keeping the list sorted. Duplicates are ignored."""
        new = SNode(key, label)
        if self.front is None or key < self.front.key:
            new.next = self.front
            self.front = new
            self.size += 1
            return True
        current = self.front
        while current.next is not None and current.next.key < key:
            current = current.next
        if current.key == key or (current.next and current.next.key == key):
            return False
        new.next = current.next
        current.next = new
        self.size += 1
        return True

    def peek(self):
        return self.front

    def pop(self):
        if self.front is None:
            return None
        node = self.front
        self.front = node.next
        self.size -= 1
        return node

    def to_list(self):
        result, current = [], self.front
        while current is not None:
            result.append(current.label)
            current = current.next
        return result


class LapStack:
    """Stack (LIFO) implemented with linked nodes."""

    class _Node:
        def __init__(self, value, below):
            self.value = value
            self.below = below

    def __init__(self):
        self.top = None
        self.size = 0

    def push(self, value):
        self.top = LapStack._Node(value, self.top)
        self.size += 1

    def pop(self):
        if self.top is None:
            return None
        value = self.top.value
        self.top = self.top.below
        self.size -= 1
        return value

    def clear(self):
        self.top = None
        self.size = 0

    def to_list(self):
        """Items from top (newest) to bottom (oldest)."""
        result, current = [], self.top
        while current is not None:
            result.append(current.value)
            current = current.below
        return result


# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------

THEMES = {
    "light": {
        "bg": "#f4f7fc", "face": "#ffffff", "border": "#2b2f77",
        "text": "#1d2250", "hour": "#2b2f77", "minute": "#5a4fcf",
        "second": "#e5391e", "panel": "#e6ebf5", "button": "#2b2f77",
        "button_text": "#ffffff",
    },
    "dark": {
        "bg": "#14172b", "face": "#1d2140", "border": "#8f94ff",
        "text": "#e8eaff", "hour": "#e8eaff", "minute": "#a89dff",
        "second": "#ff6a4d", "panel": "#232850", "button": "#5a4fcf",
        "button_text": "#ffffff",
    },
}


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class ClockApp(tk.Tk):
    SIZE = 520
    CENTER = SIZE // 2
    RADIUS = 225

    def __init__(self):
        super().__init__()
        self.title("Python Clock")
        self.resizable(False, False)

        self.theme_name = "light"
        self.use_24h = True

        # Data structures
        self.hour_marks = CircularDoublyLinkedList()
        for h in range(1, 13):
            self.hour_marks.append(h)
        self.minute_ticks = CircularDoublyLinkedList()
        for m in range(60):
            self.minute_ticks.append(m)
        self.alarms = AlarmQueue()
        self.laps = LapStack()

        # Stopwatch state
        self.sw_running = False
        self.sw_start = 0.0
        self.sw_accum = 0.0
        self.last_lap_time = 0.0

        self.ringing_until = 0.0

        self._build_ui()
        self._apply_theme()
        self._tick()

    # ------------------------------ UI -------------------------------------

    def _build_ui(self):
        self.canvas = tk.Canvas(self, width=self.SIZE, height=self.SIZE,
                                highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=16, pady=16)

        self.side = tk.Frame(self)
        self.side.grid(row=0, column=1, padx=(0, 16), pady=16, sticky="n")

        self.digital = tk.Label(self.side, font=("Consolas", 14, "bold"))
        self.digital.pack(anchor="w")
        self.date_label = tk.Label(self.side, font=("Segoe UI", 12))
        self.date_label.pack(anchor="w", pady=(0, 10))

        row = tk.Frame(self.side)
        row.pack(anchor="w", pady=4)
        self.btn_format = self._button(row, "12h / 24h", self._toggle_format)
        self.btn_format.pack(side="left", padx=(0, 6))
        self.btn_theme = self._button(row, "Light / Dark", self._toggle_theme)
        self.btn_theme.pack(side="left")

        # Alarms
        self.alarm_title = tk.Label(self.side, text="Alarms (priority queue)",
                                    font=("Segoe UI", 11, "bold"))
        self.alarm_title.pack(anchor="w", pady=(14, 2))
        arow = tk.Frame(self.side)
        arow.pack(anchor="w")
        self.alarm_entry = tk.Entry(arow, width=8, font=("Consolas", 12))
        self.alarm_entry.insert(0, "HH:MM")
        self.alarm_entry.pack(side="left", padx=(0, 6))
        self.btn_alarm = self._button(arow, "Add", self._add_alarm)
        self.btn_alarm.pack(side="left")
        self.alarm_list = tk.Label(self.side, text="No alarms",
                                   font=("Consolas", 11), justify="left")
        self.alarm_list.pack(anchor="w", pady=2)
        self.alarm_msg = tk.Label(self.side, text="", font=("Segoe UI", 11, "bold"))
        self.alarm_msg.pack(anchor="w")

        # Stopwatch
        self.sw_title = tk.Label(self.side, text="Stopwatch (laps in a stack)",
                                 font=("Segoe UI", 11, "bold"))
        self.sw_title.pack(anchor="w", pady=(14, 2))
        self.sw_label = tk.Label(self.side, text="00:00.00",
                                 font=("Consolas", 20, "bold"))
        self.sw_label.pack(anchor="w")
        srow = tk.Frame(self.side)
        srow.pack(anchor="w", pady=4)
        self.btn_start = self._button(srow, "Start/Stop", self._sw_toggle)
        self.btn_start.pack(side="left", padx=(0, 6))
        self.btn_lap = self._button(srow, "Lap", self._sw_lap)
        self.btn_lap.pack(side="left", padx=(0, 6))
        self.btn_reset = self._button(srow, "Reset", self._sw_reset)
        self.btn_reset.pack(side="left")
        self.lap_list = tk.Label(self.side, text="", font=("Consolas", 10),
                                 justify="left")
        self.lap_list.pack(anchor="w")

    def _button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, relief="flat",
                         padx=10, pady=3, cursor="hand2",
                         font=("Segoe UI", 10, "bold"))

    def _apply_theme(self):
        t = THEMES[self.theme_name]
        self.configure(bg=t["bg"])
        self.canvas.configure(bg=t["bg"])
        self.side.configure(bg=t["bg"])
        for frame in self.side.winfo_children():
            if isinstance(frame, tk.Frame):
                frame.configure(bg=t["bg"])
        for w in (self.digital, self.date_label, self.alarm_title,
                  self.alarm_list, self.sw_title, self.sw_label,
                  self.lap_list):
            w.configure(bg=t["bg"], fg=t["text"])
        self.alarm_msg.configure(bg=t["bg"], fg=t["second"])
        self.digital.configure(fg=t["minute"])
        self.alarm_entry.configure(bg=t["panel"], fg=t["text"],
                                   insertbackground=t["text"], relief="flat")
        for b in (self.btn_format, self.btn_theme, self.btn_alarm,
                  self.btn_start, self.btn_lap, self.btn_reset):
            b.configure(bg=t["button"], fg=t["button_text"],
                        activebackground=t["minute"],
                        activeforeground=t["button_text"])

    # ---------------------------- Actions -----------------------------------

    def _toggle_format(self):
        self.use_24h = not self.use_24h

    def _toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self._apply_theme()

    def _add_alarm(self):
        text = self.alarm_entry.get().strip()
        try:
            hh, mm = text.split(":")
            hh, mm = int(hh), int(mm)
            if not (0 <= hh < 24 and 0 <= mm < 60):
                raise ValueError
        except ValueError:
            self.alarm_msg.config(text="Use format HH:MM (24h)")
            return
        added = self.alarms.insert(hh * 60 + mm, f"{hh:02d}:{mm:02d}")
        self.alarm_msg.config(text="" if added else "Alarm already exists")
        self._refresh_alarms()

    def _refresh_alarms(self):
        items = self.alarms.to_list()
        self.alarm_list.config(text=", ".join(items) if items else "No alarms")

    def _sw_elapsed(self):
        if self.sw_running:
            return self.sw_accum + (time.time() - self.sw_start)
        return self.sw_accum

    def _sw_toggle(self):
        if self.sw_running:
            self.sw_accum = self._sw_elapsed()
            self.sw_running = False
        else:
            self.sw_start = time.time()
            self.sw_running = True

    def _sw_lap(self):
        if not (self.sw_running or self.sw_accum > 0):
            return
        total = self._sw_elapsed()
        self.laps.push((self.laps.size + 1, total - self.last_lap_time, total))
        self.last_lap_time = total
        lines = [f"#{n:<2} lap {self._fmt_sw(d)}  total {self._fmt_sw(t)}"
                 for n, d, t in self.laps.to_list()[:5]]
        self.lap_list.config(text="\n".join(lines))

    def _sw_reset(self):
        self.sw_running = False
        self.sw_accum = 0.0
        self.last_lap_time = 0.0
        self.laps.clear()
        self.lap_list.config(text="")

    @staticmethod
    def _fmt_sw(seconds):
        minutes = int(seconds // 60)
        return f"{minutes:02d}:{seconds % 60:05.2f}"

    # ---------------------------- Drawing -----------------------------------

    def _polar(self, angle_deg, length):
        rad = math.radians(angle_deg)
        return (self.CENTER + length * math.sin(rad),
                self.CENTER - length * math.cos(rad))

    def _draw_dial(self, hh, mm, ss):
        t = THEMES[self.theme_name]
        c, r = self.canvas, self.RADIUS
        c.delete("all")
        cx = self.CENTER

        c.create_oval(cx - r - 8, cx - r - 8, cx + r + 8, cx + r + 8,
                      fill=t["face"], outline=t["border"], width=5)

        # Minute ticks (circular list of 60 nodes)
        for m in self.minute_ticks:
            is_hour = m % 5 == 0
            x1, y1 = self._polar(m * 6, r - (14 if is_hour else 7))
            x2, y2 = self._polar(m * 6, r)
            c.create_line(x1, y1, x2, y2, fill=t["border"],
                          width=3 if is_hour else 1)

        # Hour numbers (circular list of 12 nodes)
        for h in self.hour_marks:
            x, y = self._polar(h * 30, r - 32)
            c.create_text(x, y, text=str(h), fill=t["text"],
                          font=("Segoe UI", 22, "bold"))

        hour_angle = (hh % 12 + mm / 60 + ss / 3600) * 30
        minute_angle = (mm + ss / 60) * 6
        second_angle = ss * 6

        for angle, length, width, color in (
                (hour_angle, r * 0.50, 10, t["hour"]),
                (minute_angle, r * 0.76, 6, t["minute"])):
            x, y = self._polar(angle, length)
            c.create_line(cx, cx, x, y, width=width, fill=color,
                          capstyle="round")

        x, y = self._polar(second_angle, r * 0.85)
        bx, by = self._polar(second_angle + 180, 22)
        c.create_line(bx, by, x, y, width=3, fill=t["second"])
        c.create_oval(cx - 7, cx - 7, cx + 7, cx + 7,
                      fill=t["second"], outline="")

    # ---------------------------- Main loop ---------------------------------

    def _tick(self):
        now = time.localtime()
        hh, mm, ss = now.tm_hour, now.tm_min, now.tm_sec
        self._draw_dial(hh, mm, ss)

        if self.use_24h:
            self.digital.config(text=f"{hh:02d}:{mm:02d}:{ss:02d}")
        else:
            suffix = "AM" if hh < 12 else "PM"
            self.digital.config(
                text=f"{(hh % 12) or 12:02d}:{mm:02d}:{ss:02d} {suffix}")

        days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                "Saturday", "Sunday")
        months = ("January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November",
                  "December")
        self.date_label.config(
            text=f"{days[now.tm_wday]}, {months[now.tm_mon - 1]} "
                 f"{now.tm_mday}, {now.tm_year}")

        # Alarm check: only the front of the priority queue is inspected.
        front = self.alarms.peek()
        if front is not None and front.key == hh * 60 + mm:
            node = self.alarms.pop()
            self.alarm_msg.config(text=f"ALARM {node.label}!")
            self.ringing_until = time.time() + 10
            self._refresh_alarms()
        if time.time() < self.ringing_until:
            if ss % 2 == 0:
                self.bell()
        elif self.alarm_msg.cget("text").startswith("ALARM"):
            self.alarm_msg.config(text="")

        self.sw_label.config(text=self._fmt_sw(self._sw_elapsed()))
        self.after(100, self._tick)


if __name__ == "__main__":
    ClockApp().mainloop()
