"""
Analog clock built on top of a Circular Doubly Linked List.

Data Structures workshop - Universidad Cooperativa de Colombia, Campus Pasto.

Only two modules that ship with Python are used:
    - tkinter: to draw the window (frontend).
    - time:    to read the system clock.
Everything else (the data structure, the trigonometry used to place the
hands, the calendar, the themes, the time zones and the alarms) is written
by hand in pure Python and stored in circular doubly linked lists.

Main idea:
    The clock face is a circular doubly linked list with 60 links
    (one link per minute mark). Each hand (hour, minute, second) is just a
    pointer to one link of that list. To move a hand we follow `next`
    (clockwise) or `prev` (counter-clockwise), choosing the shortest way.
"""

import tkinter as tk
import time


# =============================================================================
# 1. Math helpers (written by hand, no `math` module)
# =============================================================================

PI = 3.141592653589793
TWO_PI = 2 * PI


def sine(angle):
    """Sine using the Taylor series: x - x^3/3! + x^5/5! - ..."""
    while angle > PI:
        angle -= TWO_PI
    while angle < -PI:
        angle += TWO_PI
    term = angle
    total = angle
    n = 1
    while n < 18:
        term = -term * angle * angle / ((2 * n) * (2 * n + 1))
        total += term
        n += 1
    return total


def cosine(angle):
    """cos(x) = sin(x + pi/2)."""
    return sine(angle + PI / 2)


# =============================================================================
# 2. Data structure: Circular Doubly Linked List
# =============================================================================

class ClockLink:
    """A link of the ring: it points to the previous link and to the next link."""

    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None


class ClockRing:
    """
    Circular doubly linked list.
    The last link points to the head (last.next == head) and the head points
    back to the last link (head.prev == last).
    """

    def __init__(self):
        self.head = None
        self.size = 0

    def is_empty(self):
        return self.head is None

    def __len__(self):
        return self.size

    # ---- Insertion ---------------------------------------------------------

    def insert_at_beginning(self, data):
        """Insert a new link before the head and make it the new head."""
        new_link = ClockLink(data)
        if self.head is None:
            self.head = new_link
            new_link.next = new_link
            new_link.prev = new_link
        else:
            last = self.head.prev
            new_link.next = self.head
            new_link.prev = last
            last.next = new_link
            self.head.prev = new_link
            self.head = new_link
        self.size += 1
        return new_link

    def insert_at_end(self, data):
        """Insert a new link between the last link and the head."""
        new_link = ClockLink(data)
        if self.head is None:
            self.head = new_link
            new_link.next = new_link
            new_link.prev = new_link
        else:
            last = self.head.prev
            last.next = new_link
            new_link.prev = last
            new_link.next = self.head
            self.head.prev = new_link
        self.size += 1
        return new_link

    def insert_sorted(self, data, key):
        """Insert keeping the list ordered by key(data) (ascending)."""
        if self.head is None or key(data) < key(self.head.data):
            return self.insert_at_beginning(data)
        current = self.head
        while current.next != self.head and key(current.next.data) <= key(data):
            current = current.next
        new_link = ClockLink(data)
        new_link.prev = current
        new_link.next = current.next
        current.next.prev = new_link
        current.next = new_link
        self.size += 1
        return new_link

    # ---- Deletion ----------------------------------------------------------

    def delete(self, data):
        """Remove the first link whose data equals `data`. Returns True if found."""
        if self.head is None:
            return False
        current = self.head
        for _ in range(self.size):
            if current.data == data:
                if self.size == 1:
                    self.head = None
                else:
                    current.prev.next = current.next
                    current.next.prev = current.prev
                    if current is self.head:
                        self.head = current.next
                current.next = None
                current.prev = None
                self.size -= 1
                return True
            current = current.next
        return False

    # ---- Search and access -------------------------------------------------

    def find(self, condition):
        """Return the first link whose data satisfies condition(data), or None."""
        current = self.head
        for _ in range(self.size):
            if condition(current.data):
                return current
            current = current.next
        return None

    def get_link(self, index):
        """
        Return the link at `index` (wraps around because the list is circular).
        It walks forward or backward, whichever is shorter: this is only
        possible because every link has both `next` and `prev`.
        """
        if self.head is None:
            return None
        index %= self.size
        current = self.head
        if index <= self.size // 2:
            for _ in range(index):
                current = current.next
        else:
            for _ in range(self.size - index):
                current = current.prev
        return current

    # ---- Traversal ---------------------------------------------------------

    def __iter__(self):
        """Forward traversal: head -> ... -> last."""
        current = self.head
        for _ in range(self.size):
            yield current.data
            current = current.next

    def iter_backward(self):
        """Backward traversal: last -> ... -> head."""
        if self.head is None:
            return
        current = self.head.prev
        for _ in range(self.size):
            yield current.data
            current = current.prev

    def print_list(self):
        """Print every element in the console (same idea as the class code)."""
        for data in self:
            print(data)


# =============================================================================
# 3. Domain classes
# =============================================================================

class DialPosition:
    """One of the 60 marks of the clock face, with its direction vector."""

    def __init__(self, value, total):
        self.value = value
        angle = TWO_PI * value / total
        self.x = sine(angle)      # horizontal component
        self.y = -cosine(angle)   # vertical component (screen Y grows downward)

    def __str__(self):
        return f"{self.value:02d}"


class Dial:
    """The clock face: a circular doubly linked list of 60 positions."""

    POSITIONS = 60

    def __init__(self):
        self.positions = ClockRing()
        for value in range(self.POSITIONS):
            self.positions.insert_at_end(DialPosition(value, self.POSITIONS))


class ClockHand:
    """A hand is a pointer to a link of the dial list."""

    def __init__(self, name, dial, length, width, tail, color_key):
        self.name = name
        self.length = length        # fraction of the radius
        self.width = width          # line width in pixels
        self.tail = tail            # small part behind the center
        self.color_key = color_key  # attribute name inside Theme
        self.size = dial.positions.size
        self.current = dial.positions.head

    @property
    def value(self):
        return self.current.data.value

    def step_towards(self, target):
        """
        Move one link towards `target` using the shortest path:
        `next` = clockwise, `prev` = counter-clockwise.
        Returns True if the hand moved.
        """
        forward = (target - self.value) % self.size
        if forward == 0:
            return False
        if forward <= self.size - forward:
            self.current = self.current.next
        else:
            self.current = self.current.prev
        return True


class TimeZone:
    """A city and its offset from UTC (None means: use the computer's zone)."""

    def __init__(self, city, offset):
        self.city = city
        self.offset = offset

    def now(self):
        if self.offset is None:
            return time.localtime()
        return time.gmtime(time.time() + self.offset * 3600)

    def offset_text(self):
        if self.offset is None:
            return "Zona horaria del equipo"
        sign = "+" if self.offset >= 0 else "−"
        total = abs(self.offset)
        hours = int(total)
        minutes = int(round((total - hours) * 60))
        if minutes:
            return f"UTC {sign}{hours}:{minutes:02d}"
        return f"UTC {sign}{hours}"


class Theme:
    """Color palette for the whole interface."""

    def __init__(self, name, background, panel, face, rim, ticks, numbers,
                 hour, minute, second, text, muted, accent, button):
        self.name = name
        self.background = background
        self.panel = panel
        self.face = face
        self.rim = rim
        self.ticks = ticks
        self.numbers = numbers
        self.hour = hour
        self.minute = minute
        self.second = second
        self.text = text
        self.muted = muted
        self.accent = accent
        self.button = button


class Alarm:
    def __init__(self, hour, minute):
        self.hour = hour
        self.minute = minute

    def key(self):
        return self.hour * 60 + self.minute

    def __str__(self):
        period = "a. m." if self.hour < 12 else "p. m."
        hour_12 = self.hour % 12 or 12
        return f"  {self.hour:02d}:{self.minute:02d}   ({hour_12}:{self.minute:02d} {period})"


class SpanishCalendar:
    """Day and month names stored in circular doubly linked lists."""

    def __init__(self):
        self.days = ClockRing()
        for name in ("lunes", "martes", "miércoles", "jueves",
                     "viernes", "sábado", "domingo"):
            self.days.insert_at_end(name)

        self.months = ClockRing()
        for name in ("enero", "febrero", "marzo", "abril", "mayo", "junio",
                     "julio", "agosto", "septiembre", "octubre",
                     "noviembre", "diciembre"):
            self.months.insert_at_end(name)

    def day_name(self, moment):
        # tm_wday: 0 = Monday ... 6 = Sunday
        return self.days.get_link(moment.tm_wday).data

    def month_name(self, moment):
        return self.months.get_link(moment.tm_mon - 1).data

    def describe(self, moment):
        text = (f"{self.day_name(moment)}, {moment.tm_mday} de "
                f"{self.month_name(moment)} de {moment.tm_year}")
        return text[0].upper() + text[1:]


def build_time_zones():
    """Cities without daylight saving time, so the offset is always correct."""
    zones = ClockRing()
    zones.insert_at_end(TimeZone("Pasto, Colombia", -5))
    zones.insert_at_end(TimeZone("Hora de este equipo", None))
    zones.insert_at_end(TimeZone("Ciudad de México", -6))
    zones.insert_at_end(TimeZone("Buenos Aires, Argentina", -3))
    zones.insert_at_end(TimeZone("Reikiavik, Islandia", 0))
    zones.insert_at_end(TimeZone("Dubái, Emiratos Árabes", 4))
    zones.insert_at_end(TimeZone("Nueva Delhi, India", 5.5))
    zones.insert_at_end(TimeZone("Pekín, China", 8))
    zones.insert_at_end(TimeZone("Tokio, Japón", 9))
    return zones


def build_themes():
    themes = ClockRing()
    themes.insert_at_end(Theme(
        "Medianoche", "#0b1020", "#151b2e", "#1b2238", "#2a3350", "#8b93b0",
        "#e6e9f5", "#e6e9f5", "#c3c9e0", "#ff6b6b", "#e6e9f5", "#7d86a6",
        "#7c9cff", "#222a42"))
    themes.insert_at_end(Theme(
        "Papel", "#efebe4", "#fbf9f5", "#ffffff", "#d9d2c5", "#8a8273",
        "#2b2620", "#2b2620", "#4a443b", "#d9480f", "#2b2620", "#8a8273",
        "#d9480f", "#ece6db"))
    themes.insert_at_end(Theme(
        "Bosque", "#0f1a14", "#17261d", "#1d3025", "#2c4636", "#86a892",
        "#e4efe7", "#e4efe7", "#bcd3c3", "#f2c14e", "#e4efe7", "#7f9c89",
        "#f2c14e", "#22362a"))
    themes.insert_at_end(Theme(
        "Océano", "#06202b", "#0b2f3d", "#0f3a4b", "#1b5266", "#7fb4c4",
        "#e2f4f8", "#e2f4f8", "#b5dbe5", "#ff9f43", "#e2f4f8", "#6fa3b3",
        "#3dd6d0", "#124456"))
    themes.insert_at_end(Theme(
        "Atardecer", "#2a1420", "#3a1c2c", "#45213a", "#5e2f4c", "#c99ab3",
        "#fbe8f1", "#fbe8f1", "#e8c2d4", "#ffb347", "#fbe8f1", "#b98aa3",
        "#ff7eb6", "#4a2538"))
    return themes


# =============================================================================
# 4. Frontend (tkinter)
# =============================================================================

FONT = "Segoe UI"


class ClockApp:
    CANVAS_SIZE = 540
    FRAME_MS = 30          # refresh every 30 ms (smooth hand animation)
    RING_SECONDS = 15      # how long the alarm rings

    def __init__(self, root):
        self.root = root
        self.root.title("Reloj · Listas Circulares Dobles")
        self.root.resizable(False, False)

        # Model
        self.dial = Dial()
        self.hour_hand = ClockHand("hora", self.dial, 0.50, 9, 0.10, "hour")
        self.minute_hand = ClockHand("minuto", self.dial, 0.72, 6, 0.12, "minute")
        self.second_hand = ClockHand("segundo", self.dial, 0.84, 2, 0.20, "second")
        self.hands = ClockRing()
        self.hands.insert_at_end(self.hour_hand)
        self.hands.insert_at_end(self.minute_hand)
        self.hands.insert_at_end(self.second_hand)

        self.calendar = SpanishCalendar()
        self.current_zone = build_time_zones().head
        self.current_theme = build_themes().head
        self.alarms = ClockRing()

        # State
        self.use_24h = False
        self.hands_dirty = True
        self.info_key = None
        self.last_text_key = None
        self.last_alarm_minute = None
        self.ring_left = 0
        self.last_ring_second = None

        # Widgets that must be recolored when the theme changes
        self.styled = ClockRing()

        self._build_ui()
        self._bind_keys()
        self.apply_theme()
        self.tick()

    # ---- UI construction ---------------------------------------------------

    def _register(self, widget, role):
        self.styled.insert_at_end((widget, role))
        return widget

    def _card(self, parent, title):
        card = self._register(tk.Frame(parent, padx=16, pady=12), "panel")
        card.pack(fill="x", pady=(0, 10))
        if title:
            label = tk.Label(card, text=title.upper(), font=(FONT, 8, "bold"), anchor="w")
            self._register(label, "muted").pack(fill="x", pady=(0, 4))
        return card

    def _button(self, parent, text, command, role="button", width=None):
        button = tk.Button(parent, text=text, command=command, relief="flat", bd=0,
                           cursor="hand2", font=(FONT, 10, "bold"), padx=10, pady=4)
        if width:
            button.configure(width=width)
        return self._register(button, role)

    def _build_ui(self):
        self.main = self._register(tk.Frame(self.root, padx=24, pady=20), "background")
        self.main.pack()

        # Left: the analog clock
        self.canvas = tk.Canvas(self.main, width=self.CANVAS_SIZE,
                                height=self.CANVAS_SIZE, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="n")

        # Alarm banner (hidden until an alarm rings)
        self.banner = tk.Label(self.canvas, font=(FONT, 12, "bold"), padx=14, pady=8,
                               cursor="hand2")
        self.banner.bind("<Button-1>", lambda event: self.stop_ringing())

        # Right: side panel
        side = self._register(tk.Frame(self.main, width=330), "background")
        side.grid(row=0, column=1, sticky="n", padx=(24, 0))

        # Card 1: digital time and date
        card = self._card(side, "Hora actual")
        row = self._register(tk.Frame(card), "panel")
        row.pack(anchor="w")
        self.time_label = self._register(tk.Label(row, font=(FONT, 40, "bold")), "text")
        self.time_label.pack(side="left")
        self.seconds_label = self._register(tk.Label(row, font=(FONT, 18, "bold")), "accent")
        self.seconds_label.pack(side="left", anchor="s", pady=(0, 10))
        self.period_label = self._register(tk.Label(row, font=(FONT, 12)), "muted")
        self.period_label.pack(side="left", anchor="s", pady=(0, 12), padx=(6, 0))
        self.date_label = self._register(tk.Label(card, font=(FONT, 11), anchor="w"), "text")
        self.date_label.pack(fill="x")

        # Card 2: time zones (navigated with next / prev)
        card = self._card(side, "Zona horaria")
        row = self._register(tk.Frame(card), "panel")
        row.pack(fill="x")
        self._button(row, "◀", self.previous_zone).pack(side="left")
        self.city_label = self._register(
            tk.Label(row, font=(FONT, 11, "bold"), width=22), "text")
        self.city_label.pack(side="left", expand=True, fill="x")
        self._button(row, "▶", self.next_zone).pack(side="right")
        self.offset_label = self._register(tk.Label(card, font=(FONT, 9)), "muted")
        self.offset_label.pack(pady=(4, 0))

        # Card 3: appearance
        card = self._card(side, "Apariencia")
        row = self._register(tk.Frame(card), "panel")
        row.pack(fill="x")
        self._button(row, "◀", self.previous_theme).pack(side="left")
        self.theme_label = self._register(tk.Label(row, font=(FONT, 11, "bold")), "text")
        self.theme_label.pack(side="left", expand=True, fill="x")
        self._button(row, "▶", self.next_theme).pack(side="right")
        self.format_button = self._button(card, "", self.toggle_format)
        self.format_button.pack(fill="x", pady=(8, 0))

        # Card 4: alarms
        card = self._card(side, "Alarmas")
        row = self._register(tk.Frame(card), "panel")
        row.pack(fill="x")
        self.hour_spin = self._spinbox(row, 23, "07")
        self.hour_spin.pack(side="left")
        self._register(tk.Label(row, text=":", font=(FONT, 14, "bold")), "text").pack(side="left")
        self.minute_spin = self._spinbox(row, 59, "00")
        self.minute_spin.pack(side="left")
        self._button(row, "Agregar", self.add_alarm, role="accent_button").pack(side="right")

        self.alarm_listbox = self._register(
            tk.Listbox(card, height=3, font=("Consolas", 10), relief="flat", bd=0,
                       activestyle="none"), "listbox")
        self.alarm_listbox.pack(fill="x", pady=(8, 6))
        row = self._register(tk.Frame(card), "panel")
        row.pack(fill="x")
        self._button(row, "Eliminar seleccionada", self.delete_alarm).pack(side="left")
        self.status_label = self._register(tk.Label(row, font=(FONT, 8)), "muted")
        self.status_label.pack(side="right")

        footer = tk.Label(self.main, font=(FONT, 9),
                          text="← → cambiar ciudad   ·   T cambiar tema   ·   F formato 12/24 h")
        self._register(footer, "background_muted").grid(row=1, column=0, columnspan=2, pady=(12, 0))

        self.refresh_alarm_list()
        self.update_static_labels()

    def _spinbox(self, parent, maximum, initial):
        spin = tk.Spinbox(parent, from_=0, to=maximum, width=3, wrap=True,
                          format="%02.0f", justify="center", font=(FONT, 14, "bold"),
                          relief="flat", bd=0)
        spin.delete(0, "end")
        spin.insert(0, initial)
        return self._register(spin, "spinbox")

    def _bind_keys(self):
        self.root.bind("<Right>", lambda event: self.next_zone())
        self.root.bind("<Left>", lambda event: self.previous_zone())
        self.root.bind("<KeyPress-t>", lambda event: self.next_theme())
        self.root.bind("<KeyPress-T>", lambda event: self.next_theme())
        self.root.bind("<KeyPress-f>", lambda event: self.toggle_format())
        self.root.bind("<KeyPress-F>", lambda event: self.toggle_format())

    # ---- Theme -------------------------------------------------------------

    def apply_theme(self):
        theme = self.current_theme.data
        self.root.configure(bg=theme.background)
        self.canvas.configure(bg=theme.background)
        for widget, role in self.styled:
            if role == "background":
                widget.configure(bg=theme.background)
            elif role == "background_muted":
                widget.configure(bg=theme.background, fg=theme.muted)
            elif role == "panel":
                widget.configure(bg=theme.panel)
            elif role == "text":
                widget.configure(bg=theme.panel, fg=theme.text)
            elif role == "muted":
                widget.configure(bg=theme.panel, fg=theme.muted)
            elif role == "accent":
                widget.configure(bg=theme.panel, fg=theme.accent)
            elif role == "button":
                widget.configure(bg=theme.button, fg=theme.text,
                                 activebackground=theme.accent,
                                 activeforeground=theme.panel)
            elif role == "accent_button":
                widget.configure(bg=theme.accent, fg=theme.panel,
                                 activebackground=theme.text,
                                 activeforeground=theme.panel)
            elif role == "spinbox":
                widget.configure(bg=theme.button, fg=theme.text,
                                 buttonbackground=theme.button,
                                 insertbackground=theme.text,
                                 highlightthickness=0)
            elif role == "listbox":
                widget.configure(bg=theme.button, fg=theme.text,
                                 selectbackground=theme.accent,
                                 selectforeground=theme.panel,
                                 highlightthickness=0)
        self.banner.configure(bg=theme.accent, fg=theme.panel)
        self.draw_face()
        self.info_key = None
        self.hands_dirty = True
        self.update_static_labels()

    def next_theme(self):
        self.current_theme = self.current_theme.next
        self.apply_theme()

    def previous_theme(self):
        self.current_theme = self.current_theme.prev
        self.apply_theme()

    # ---- Drawing -----------------------------------------------------------

    def draw_face(self):
        theme = self.current_theme.data
        canvas = self.canvas
        canvas.delete("face")
        cx = cy = self.CANVAS_SIZE / 2
        r = self.radius = cx - 24

        canvas.create_oval(cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10,
                           fill=theme.rim, outline="", tags="face")
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                           fill=theme.face, outline="", tags="face")

        # Traverse the dial list to draw the 60 marks and the 12 numbers
        for position in self.dial.positions:
            major = position.value % 5 == 0
            inner = r * (0.86 if major else 0.91)
            outer = r * 0.95
            canvas.create_line(cx + position.x * inner, cy + position.y * inner,
                               cx + position.x * outer, cy + position.y * outer,
                               fill=theme.numbers if major else theme.ticks,
                               width=3 if major else 1, capstyle=tk.ROUND, tags="face")
            if major:
                number = position.value // 5 or 12
                weight = "bold" if number % 3 == 0 else "normal"
                canvas.create_text(cx + position.x * r * 0.74, cy + position.y * r * 0.74,
                                   text=str(number), fill=theme.numbers,
                                   font=(FONT, 22, weight), tags="face")

    def draw_info_window(self, moment):
        """Small window on the face with the day and date (e.g. MIÉ 21)."""
        key = (moment.tm_yday, self.current_theme.data.name)
        if key == self.info_key:
            return
        self.info_key = key
        theme = self.current_theme.data
        canvas = self.canvas
        canvas.delete("info")
        cx = cy = self.CANVAS_SIZE / 2
        y = cy + self.radius * 0.36
        canvas.create_rectangle(cx - 44, y - 15, cx + 44, y + 15, fill=theme.background,
                                outline=theme.rim, width=2, tags="info")
        day = self.calendar.day_name(moment)[:3].upper()
        canvas.create_text(cx, y, text=f"{day}  {moment.tm_mday}", fill=theme.accent,
                           font=(FONT, 11, "bold"), tags="info")
        canvas.tag_raise("hands")

    def draw_hands(self):
        theme = self.current_theme.data
        canvas = self.canvas
        canvas.delete("hands")
        cx = cy = self.CANVAS_SIZE / 2
        r = self.radius

        # Traverse the list of hands: hour, minute, second (second ends on top)
        for hand in self.hands:
            position = hand.current.data
            color = getattr(theme, hand.color_key)
            tip_x = cx + position.x * r * hand.length
            tip_y = cy + position.y * r * hand.length
            tail_x = cx - position.x * r * hand.tail
            tail_y = cy - position.y * r * hand.tail
            canvas.create_line(tail_x, tail_y, tip_x, tip_y, fill=color,
                               width=hand.width, capstyle=tk.ROUND, tags="hands")
            if hand is self.second_hand:
                canvas.create_oval(tail_x - 5, tail_y - 5, tail_x + 5, tail_y + 5,
                                   fill=color, outline="", tags="hands")

        canvas.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, fill=theme.second,
                           outline="", tags="hands")
        canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=theme.face,
                           outline="", tags="hands")
        self.hands_dirty = False

    # ---- Labels ------------------------------------------------------------

    def update_static_labels(self):
        zone = self.current_zone.data
        self.city_label.configure(text=zone.city)
        self.offset_label.configure(text=zone.offset_text())
        self.theme_label.configure(text=f"Tema: {self.current_theme.data.name}")
        self.format_button.configure(
            text="Cambiar a formato 12 horas" if self.use_24h else "Cambiar a formato 24 horas")
        self.last_text_key = None

    def update_texts(self, moment):
        key = (moment.tm_hour, moment.tm_min, moment.tm_sec, self.use_24h, self.current_zone)
        if key == self.last_text_key:
            return
        self.last_text_key = key

        if self.use_24h:
            self.time_label.configure(text=f"{moment.tm_hour:02d}:{moment.tm_min:02d}")
            self.period_label.configure(text="")
        else:
            hour_12 = moment.tm_hour % 12 or 12
            self.time_label.configure(text=f"{hour_12}:{moment.tm_min:02d}")
            self.period_label.configure(text="a. m." if moment.tm_hour < 12 else "p. m.")
        self.seconds_label.configure(text=f":{moment.tm_sec % 60:02d}")
        self.date_label.configure(text=self.calendar.describe(moment))

    def toggle_format(self):
        self.use_24h = not self.use_24h
        self.update_static_labels()

    # ---- Time zones --------------------------------------------------------

    def next_zone(self):
        self.current_zone = self.current_zone.next
        self.update_static_labels()

    def previous_zone(self):
        self.current_zone = self.current_zone.prev
        self.update_static_labels()

    # ---- Alarms ------------------------------------------------------------

    def add_alarm(self):
        try:
            hour = int(self.hour_spin.get())
            minute = int(self.minute_spin.get())
        except ValueError:
            self.status_label.configure(text="Escribe solo números")
            return
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            self.status_label.configure(text="Hora no válida")
            return
        if self.alarms.find(lambda a: a.hour == hour and a.minute == minute):
            self.status_label.configure(text="Esa alarma ya existe")
            return
        self.alarms.insert_sorted(Alarm(hour, minute), lambda a: a.key())
        self.status_label.configure(text=f"Alarma {hour:02d}:{minute:02d} creada")
        self.refresh_alarm_list()

    def delete_alarm(self):
        selection = self.alarm_listbox.curselection()
        if self.alarms.is_empty() or not selection:
            self.status_label.configure(text="Selecciona una alarma")
            return
        alarm = self.alarms.get_link(selection[0]).data
        self.alarms.delete(alarm)
        self.status_label.configure(text="Alarma eliminada")
        self.refresh_alarm_list()

    def refresh_alarm_list(self):
        self.alarm_listbox.delete(0, "end")
        if self.alarms.is_empty():
            self.alarm_listbox.insert("end", "  Sin alarmas programadas")
            return
        for alarm in self.alarms:
            self.alarm_listbox.insert("end", str(alarm))

    def check_alarms(self, moment):
        minute_key = (moment.tm_hour, moment.tm_min)
        if minute_key != self.last_alarm_minute:
            self.last_alarm_minute = minute_key
            found = self.alarms.find(
                lambda a: a.hour == moment.tm_hour and a.minute == moment.tm_min)
            if found is not None:
                self.start_ringing(found.data)

        if self.ring_left > 0 and moment.tm_sec != self.last_ring_second:
            self.last_ring_second = moment.tm_sec
            self.root.bell()
            self.ring_left -= 1
            if self.ring_left == 0:
                self.stop_ringing()

    def start_ringing(self, alarm):
        self.ring_left = self.RING_SECONDS
        self.banner.configure(
            text=f"⏰  ¡Alarma de las {alarm.hour:02d}:{alarm.minute:02d}!   ·   clic para detener")
        self.banner.place(relx=0.5, rely=0.66, anchor="n")

    def stop_ringing(self):
        self.ring_left = 0
        self.banner.place_forget()

    # ---- Main loop ---------------------------------------------------------

    def tick(self):
        moment = self.current_zone.data.now()
        hour_target = (moment.tm_hour % 12) * 5 + moment.tm_min // 12
        minute_target = moment.tm_min
        second_target = moment.tm_sec % 60

        # Each hand walks one link per frame towards its target
        moved_hour = self.hour_hand.step_towards(hour_target)
        moved_minute = self.minute_hand.step_towards(minute_target)
        moved_second = self.second_hand.step_towards(second_target)

        self.draw_info_window(moment)
        if moved_hour or moved_minute or moved_second or self.hands_dirty:
            self.draw_hands()
        self.update_texts(moment)
        self.check_alarms(moment)
        self.root.after(self.FRAME_MS, self.tick)


def main():
    root = tk.Tk()
    ClockApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
