"""
TapIn — NFC Attendance System reated by tylerallen
PyQt6 edition with hardware-accelerated UI, smooth animations, and true transparency
"""

import sys
import os
import re
import csv
import json
import time
import serial
import serial.tools.list_ports
import threading
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSplitter, QTextEdit,
    QLineEdit, QComboBox, QCheckBox, QFileDialog, QMessageBox,
    QDialog, QGridLayout, QSizePolicy, QStackedWidget, QSpacerItem,
    QAbstractItemView
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal,
    QTimer, QSize, QRect, pyqtProperty, QObject
)
from PyQt6.QtGui import (
    QFont, QFontDatabase, QColor, QPalette, QLinearGradient,
    QRadialGradient, QPainter, QBrush, QPen, QPixmap, QIcon,
    QPainterPath, QCursor
)


# base dir - works for both .py and compiled .exe
def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

BASE_DIR         = get_base_dir()
SECTIONS_DIR     = BASE_DIR / "class_sections"
LOGS_DIR         = BASE_DIR / "attendance_logs"
SESSION_LOGS_DIR = BASE_DIR / "session_logs"


# font detection
def resolve_fonts():
    families = set(QFontDatabase.families())
    def pick(candidates):
        for c in candidates:
            if c in families:
                return c
        return candidates[-1]
    # headers
    display = pick(["Geist", "Geist Sans", "Inter", "Segoe UI", "Arial"])
    # body text
    text    = pick(["Geist Mono", "Geist", "Inter", "Consolas", "Segoe UI"])
    # mono/code areas
    mono    = pick(["Geist Mono", "Consolas", "Menlo", "Courier New"])
    return display, text, mono

_F_DISPLAY = _F_TEXT = _F_MONO = None 


C = {
    "bg":           "#0D0F14",
    "bg2":          "#111318",
    "bg3":          "#161A22",
    "surface":      "#1A1F2B",
    "surface2":     "#1E2433",
    "surface3":     "#232B3A",
    "border":       "#1E3A5F",
    "border2":      "#2A4A7A",
    "accent":       "#3B82F6",
    "accent_hover": "#60A5FA",
    "accent_dim":   "#1D4ED8",
    "green":        "#10B981",
    "green_dim":    "#065F46",
    "red":          "#EF4444",
    "red_dim":      "#7F1D1D",
    "warn":         "#F59E0B",
    "text":         "#F1F5F9",
    "text2":        "#94A3B8",
    "text3":        "#475569",
    "text4":        "#1E293B",
    "mono":         "#7DD3FC",
}


# qss stylesheet 
def build_qss():
    ft  = _F_TEXT
    fm  = _F_MONO
    return f"""
QMainWindow, QDialog {{
    background-color: {C["bg"]};
}}
QWidget {{
    color: {C["text"]};
    font-family: "{ft}";
    font-size: 13px;
    background-color: transparent;
}}

/* scrollbars */
QScrollBar:vertical {{
    background: {C["bg2"]};
    width: 6px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C["border2"]};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C["accent"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {C["bg2"]};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {C["border2"]};
    border-radius: 3px;
    min-width: 30px;
}}

/* splitter handle */
QSplitter::handle {{
    background: {C["border"]};
}}
QSplitter::handle:hover {{
    background: {C["accent"]};
}}
QSplitter::handle:horizontal {{
    width: 4px;
    background: transparent;
}}
QSplitter::handle:horizontal:hover {{
    background: {C["border2"]};
}}

/* text edit */
QTextEdit {{
    background-color: {C["surface"]};
    border: 1px solid {C["border"]};
    border-radius: 8px;
    padding: 8px;
    color: {C["text2"]};
    font-family: "{fm}";
    font-size: 11px;
    selection-background-color: {C["accent_dim"]};
}}

/* line edit */
QLineEdit {{
    background-color: {C["surface"]};
    border: 1px solid {C["border"]};
    border-radius: 8px;
    padding: 6px 10px;
    color: {C["text"]};
    font-size: 13px;
    selection-background-color: {C["accent_dim"]};
}}
QLineEdit:focus {{
    border: 1px solid {C["accent"]};
}}
QLineEdit:read-only {{
    color: {C["text2"]};
    background-color: {C["bg3"]};
}}

/* combo box */
QComboBox {{
    background-color: {C["surface"]};
    border: 1px solid {C["border"]};
    border-radius: 8px;
    padding: 6px 10px;
    color: {C["text"]};
    font-size: 13px;
    min-width: 140px;
}}
QComboBox:hover {{
    border: 1px solid {C["accent"]};
}}
QComboBox:focus {{
    border: 1px solid {C["accent"]};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    padding-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {C["surface2"]};
    border: 1px solid {C["border2"]};
    border-radius: 8px;
    color: {C["text"]};
    selection-background-color: {C["accent_dim"]};
    outline: none;
    padding: 4px;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    border-radius: 6px;
    min-height: 28px;
}}

/* checkbox */
QCheckBox {{
    spacing: 8px;
    color: {C["text2"]};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid {C["border2"]};
    background-color: {C["surface"]};
}}
QCheckBox::indicator:checked {{
    background-color: {C["accent"]};
    border: 1px solid {C["accent"]};
}}
QCheckBox::indicator:hover {{
    border: 1px solid {C["accent"]};
}}
"""


# settings - load/save json to disk
DEFAULT_SETTINGS = {
    "log_dir":       str(SESSION_LOGS_DIR),
    "sections_dir":  str(SECTIONS_DIR),
    "serial_port":   "auto",
    "serial_baud":   115200,
    "auto_connect":  True,
}

def settings_path():
    return BASE_DIR / "tapin_settings.json"

def load_settings():
    p = settings_path()
    if p.exists():
        try:
            with open(p) as f:
                s = json.load(f)
            return {**DEFAULT_SETTINGS, **s}
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)

def save_settings(s):
    try:
        with open(settings_path(), "w") as f:
            json.dump(s, f, indent=2)
    except Exception as e:
        print(f"[TapIn] save_settings error: {e}")


# session logger - writes every tap + event to a .log file
class SessionLogger:
    def __init__(self, log_dir=None):
        self.log_dir = Path(log_dir) if log_dir else SESSION_LOGS_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.path = self.log_dir / f"session_{ts}.log"
        self._write("SESSION START")

    def _write(self, line):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.path, "a") as f:
                f.write(f"[{ts}] {line}\n")
        except Exception:
            pass

    def log_tap(self, uid, issue, student_id, name=None, status="OK", note=""):
        self._write(f"TAP | UID={uid} | ISSUE={issue} | ID={student_id} | "
                    f"NAME={name or 'UNKNOWN'} | STATUS={status} | {note}")

    def log_event(self, msg):
        self._write(f"EVENT | {msg}")

    def change_dir(self, new_dir):
        self.log_dir = Path(new_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.path = self.log_dir / f"session_{ts}.log"
        self._write("SESSION CONTINUED")


# csv helpers - read/write section files and attendance logs
def sections_dir_from_settings(s):
    return Path(s.get("sections_dir", str(SECTIONS_DIR)))

def parse_section_file(path):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        if not rows:
            return None, None, []
        h = rows[0]
        course  = h[0].strip() if len(h) > 0 else "?"
        section = h[1].strip() if len(h) > 1 else "?"
        students = [{"first": r[0].strip(), "last": r[1].strip(),
                     "student_id": r[2].strip()}
                    for r in rows[1:] if len(r) >= 3]
        return course, section, students
    except Exception as e:
        print(f"parse_section_file: {e}")
        return None, None, []

def write_section_file(path, course, section, students):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([course, section])
            for s in students:
                w.writerow([s["first"], s["last"], s["student_id"]])
    except Exception as e:
        print(f"write_section_file: {e}")

def save_attendance_log(log_dir, course, section, students, attendance):
    cc = course.strip().replace(" ", "_")
    sc = section.strip().replace(" ", "_")
    folder = log_dir / cc / f"{cc}-{sc}"
    folder.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = folder / f"{cc}_{sc}_{date_str}.csv"
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([course, section, date_str])
            w.writerow(["FirstName", "LastName", "StudentID", "Status", "Timestamp"])
            for s in students:
                sid    = s["student_id"].strip()
                status = attendance.get(sid, {}).get("status", "ABSENT")
                ts     = attendance.get(sid, {}).get("time", "")
                w.writerow([s["first"], s["last"], sid, status, ts])
        return path
    except Exception as e:
        print(f"save_attendance_log: {e}")
        return None

def parse_attendance_log(path):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        if len(rows) < 2:
            return None, None, None, []
        h = rows[0]
        course   = h[0].strip() if len(h) > 0 else "?"
        section  = h[1].strip() if len(h) > 1 else "?"
        date_str = h[2].strip() if len(h) > 2 else path.stem
        students = []
        for r in rows[2:]:
            if len(r) >= 3 and r[0] != "FirstName":
                students.append({
                    "first": r[0].strip(), "last": r[1].strip(),
                    "student_id": r[2].strip(),
                    "status": r[3].strip() if len(r) > 3 else "ABSENT",
                    "time":   r[4].strip() if len(r) > 4 else "",
                })
        return course, section, date_str, students
    except Exception as e:
        print(f"parse_attendance_log: {e}")
        return None, None, None, []


# serial reader - background thread, reads from esp32, parses card data
class SerialReader(QThread):
    tap_received    = pyqtSignal(str, str, str)   # uid, issue num, student id
    status_changed  = pyqtSignal(bool)
    error_message   = pyqtSignal(str)

    def __init__(self, port, baud):
        super().__init__(None)
        self.port      = port
        self.baud      = baud
        self._stop     = threading.Event()
        self._uid_buf  = None

    def stop(self):
        self._stop.set()

    def run(self):
        ser = None
        retry = 2
        while not self._stop.is_set():
            try:
                self.error_message.emit(f"Connecting to {self.port}...")
                ser = serial.Serial(port=self.port, baudrate=self.baud, timeout=2)
                time.sleep(2)
                ser.reset_input_buffer()
                self.status_changed.emit(True)
                self.error_message.emit(f"Connected to {self.port}")
                retry = 2  # reset backoff
                self._uid_buf = None
                while not self._stop.is_set():
                    try:
                        raw = ser.readline()
                    except serial.SerialException as e:
                        self.error_message.emit(f"Read error: {e}")
                        break
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line:
                        self.error_message.emit(f"RX: {line}")
                        self._parse(line)
            except serial.SerialException as e:
                self.error_message.emit(f"SerialException: {e}")
                self.status_changed.emit(False)
                if ser:
                    try: ser.close()
                    except: pass
                    ser = None
                if not self._stop.is_set():
                    time.sleep(retry)
                    retry = min(retry * 2, 15)  # back off slowly
            except Exception as e:
                self.error_message.emit(f"Error: {e}")
                self.status_changed.emit(False)
                time.sleep(retry)
        if ser:
            try: ser.close()
            except: pass
        self.status_changed.emit(False)

    def _parse(self, line):
        if "UID:" in line and "Block" not in line:
            m = re.search(r"UID:\s*((?:[0-9A-Fa-f]{2}\s*)+)", line)
            if m:
                self._uid_buf = m.group(1).strip()
            return
        if "Block 52 (hex):" in line:
            return
        if "Block 52 (ASCII):" in line and self._uid_buf:
            m = re.search(r"Block 52 \(ASCII\):\s*(\S+)", line)
            if m:
                raw = m.group(1).strip()
                if len(raw) >= 3:
                    issue_num  = raw[:2]
                    student_id = raw[-6:] if len(raw) >= 6 else raw
                    self.tap_received.emit(self._uid_buf, issue_num, student_id)
            self._uid_buf = None

def auto_detect_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = (p.description or "").lower()
        if any(k in desc for k in ["cp210", "ch340", "usb serial", "uart", "esp"]):
            return p.device
    return ports[0].device if ports else None


# reusable widgets
class GradientWidget(QWidget):
    # paints the dark bg gradient
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # base fill
        painter.fillRect(0, 0, w, h, QColor(C["bg"]))

        # subtle teal glow top left
        grad1 = QRadialGradient(w * 0.15, h * 0.1, w * 0.55)
        grad1.setColorAt(0, QColor(15, 40, 60, 60))
        grad1.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, QBrush(grad1))

        # subtle purple glow bottom right
        grad2 = QRadialGradient(w * 0.85, h * 0.9, w * 0.5)
        grad2.setColorAt(0, QColor(40, 20, 70, 50))
        grad2.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, QBrush(grad2))
        painter.end()


class Card(QFrame):
    # rounded card container
    def __init__(self, parent=None, radius=12):
        super().__init__(parent)
        self._radius = radius
        self.setObjectName("Card")
        self.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {C["surface"]};
                border: 1px solid {C["border"]};
                border-radius: {radius}px;
            }}
        """)


class TapButton(QPushButton):
    # button with hover color + padding shift. no position animation (breaks splitters)
    STYLES = {
        "primary":   (C["accent_dim"],   C["accent"],       C["text"],  C["accent"]),
        "secondary": (C["surface2"],     C["surface3"],     C["text2"], C["border2"]),
        "danger":    (C["red_dim"],      C["red"],          C["text"],  C["red"]),
        "success":   (C["green_dim"],    C["green"],        C["text"],  C["green"]),
        "ghost":     ("transparent",     C["surface2"],     C["text3"], C["border"]),
    }

    def __init__(self, text, style="primary", parent=None):
        super().__init__(text, parent)
        self._style_key = style
        self._apply_style(False)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(36)

    def _apply_style(self, hovered):
        bg_idle, bg_hover, fg, border = self.STYLES[self._style_key]
        bg = bg_hover if hovered else bg_idle
        # shift padding on hover so text appears to lift slightly
        pt = "2px" if hovered else "4px"
        pb = "6px" if hovered else "4px"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 9px;
                padding: {pt} 8px {pb} 8px;
                font-family: "{_F_TEXT}";
                font-size: 13px;
                font-weight: 500;
                letter-spacing: 0.2px;
            }}
        """)

    def enterEvent(self, event):
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)


class StatusDot(QWidget):
    # the little dot in the bottom right showing reader connection
    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False
        self._glow_alpha = 0
        self._glow_growing = True
        self.setFixedSize(14, 14)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self._timer.start(50)

    def set_connected(self, v):
        self._connected = v
        self.update()

    def _pulse(self):
        if self._connected:
            if self._glow_growing:
                self._glow_alpha += 8
                if self._glow_alpha >= 160:
                    self._glow_growing = False
            else:
                self._glow_alpha -= 8
                if self._glow_alpha <= 40:
                    self._glow_growing = True
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(C["green"]) if self._connected else QColor(C["red"])

        if self._connected:
            glow = QColor(C["green"])
            glow.setAlpha(self._glow_alpha)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(glow))
            p.drawEllipse(0, 0, 14, 14)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        p.drawEllipse(2, 2, 10, 10)
        p.end()


class SectionTreeItem(QPushButton):
    # tree row button used in history + section pickers
    def __init__(self, text, indent=0, is_header=False, clickable=True):
        super().__init__(text)
        self.setFlat(True)
        self.setCursor(QCursor(
            Qt.CursorShape.PointingHandCursor if clickable
            else Qt.CursorShape.ArrowCursor
        ))
        if not clickable:
            self.setEnabled(False)

        if is_header:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 6px 12px 6px {12 + indent}px;
                    background-color: {C["surface2"]};
                    border: 1px solid {C["border"]};
                    border-radius: 8px;
                    color: {C["text"]};
                    font-family: "{_F_TEXT}";
                    font-size: 13px;
                    font-weight: 700;
                    margin: 1px 0;
                }}
                QPushButton:hover {{
                    background-color: {C["surface3"]};
                }}
            """)
        elif clickable:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 4px 12px 4px {12 + indent}px;
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    color: {C["text3"]};
                    font-family: "{_F_MONO}";
                    font-size: 11px;
                    margin: 0;
                }}
                QPushButton:hover {{
                    background-color: {C["accent_dim"]};
                    color: {C["text"]};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 4px 12px 4px {12 + indent}px;
                    background-color: transparent;
                    border: none;
                    color: {C["text2"]};
                    font-family: "{_F_TEXT}";
                    font-size: 12px;
                    font-weight: 600;
                    margin: 0;
                }}
            """)


def label(text, size=13, weight=400, color=None, mono=False):
    lbl = QLabel(text)
    family = _F_MONO if mono else _F_TEXT
    # needs to be stylesheet not setFont() or global qss wins
    lbl.setStyleSheet(f"""
        color: {color or C['text']};
        background: transparent;
        font-family: "{family}";
        font-size: {size}px;
        font-weight: {weight};
        letter-spacing: 0.1px;
    """)
    return lbl


def h_line():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color: {C['border']}; background-color: {C['border']};")
    f.setFixedHeight(1)
    return f


def make_input(placeholder="", width=None):
    e = QLineEdit()
    e.setPlaceholderText(placeholder)
    e.setFixedHeight(34)
    if width:
        e.setFixedWidth(width)
    return e


def make_combo(values):
    c = QComboBox()
    c.addItems(values)
    c.setFixedHeight(34)
    c.view().setSpacing(2)
    return c


# student row - used in both attendance view and history tab
class StudentRow(QWidget):
    present_clicked = pyqtSignal(str)
    absent_clicked  = pyqtSignal(str)

    def __init__(self, first, last, student_id, even=True, show_time=False, time_str=""):
        super().__init__()
        self._sid = student_id
        bg = C["surface"] if even else C["bg3"]
        self.setStyleSheet(f"""
            QWidget#StudentRow {{
                background-color: {bg};
                border-radius: 10px;
                border: 1px solid {C["border"]};
            }}
        """)
        self.setObjectName("StudentRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(0)

        # status dot
        self._dot_widget = DotIndicator()
        layout.addWidget(self._dot_widget)
        layout.addSpacing(12)

        # name and id stacked
        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = label(f"{first} {last}", size=14, weight=600)
        id_text = f"ID: {student_id}"
        if show_time and time_str:
            id_text += f"  ·  {time_str}"
        id_lbl = label(id_text, size=11, color=C["text3"])
        info.addWidget(name_lbl)
        info.addWidget(id_lbl)
        layout.addLayout(info)
        layout.addStretch()

        # manual present/absent buttons on the right
        override = QFrame()
        override.setStyleSheet(f"""
            QFrame {{
                background-color: {C["bg2"]};
                border: 1px solid {C["border"]};
                border-radius: 8px;
            }}
        """)
        ob = QHBoxLayout(override)
        ob.setContentsMargins(6, 4, 6, 4)
        ob.setSpacing(4)

        self._btn_present = self._make_override_btn("✓  Present", C["green"])
        self._btn_absent  = self._make_override_btn("✕  Absent",  C["red"])
        self._btn_present.clicked.connect(lambda: self.present_clicked.emit(self._sid))
        self._btn_absent.clicked.connect(lambda: self.absent_clicked.emit(self._sid))
        ob.addWidget(self._btn_present)
        ob.addWidget(self._btn_absent)

        layout.addWidget(override)

    def _make_override_btn(self, text, hover_color):
        btn = QPushButton(text)
        btn.setFixedHeight(28)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: {C["text2"]};
                font-family: "{_F_TEXT}";
                font-size: 12px;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                color: white;
            }}
        """)
        return btn

    def set_state(self, state):
        self._dot_widget.set_state(state)


class DotIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self._state = "absent"
        self.setFixedSize(22, 22)

    def set_state(self, state):
        self._state = state
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(C["green"]) if self._state == "present" else QColor(C["red"])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        p.drawEllipse(1, 1, 20, 20)
        p.setPen(QPen(QColor("white"), 1.5))
        p.setFont(QFont(_F_TEXT, 11, QFont.Weight.Bold))
        p.drawText(QRect(1, 1, 20, 20), Qt.AlignmentFlag.AlignCenter,
                   "✓" if self._state == "present" else "✗")
        p.end()


# attendance view tab
class AttendanceView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app             = app
        self.loaded_course   = None
        self.loaded_section  = None
        self.loaded_students = []
        self.attendance      = {}
        self.tapped_ids      = set()
        self.active          = False
        self._row_widgets    = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # top bar with title + buttons
        top = QHBoxLayout()
        top.setSpacing(10)
        title = label("Attendance View", size=17, weight=700)
        top.addWidget(title)
        top.addStretch()
        self.btn_save = TapButton("Save Log", "secondary")
        self.btn_save.setFixedWidth(110)
        self.btn_save.clicked.connect(self._save_log)
        self.btn_activate = TapButton("Activate Logging", "success")
        self.btn_activate.setFixedWidth(170)
        self.btn_activate.clicked.connect(self._toggle_active)
        top.addWidget(self.btn_save)
        top.addWidget(self.btn_activate)
        root.addLayout(top)

        # splitter - left is student list, right is section picker + activity
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)

        # left side - student list
        left_card = Card()
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(8)

        lh = QHBoxLayout()
        self.lbl_section = label("No section loaded", size=15, weight=700)
        self.lbl_count   = label("", size=11, color=C["text3"])
        lh.addWidget(self.lbl_section)
        lh.addStretch()
        lh.addWidget(self.lbl_count)
        left_layout.addLayout(lh)
        left_layout.addWidget(h_line())

        self.student_scroll = QScrollArea()
        self.student_scroll.setWidgetResizable(True)
        self.student_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.student_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._student_container = QWidget()
        self._student_layout = QVBoxLayout(self._student_container)
        self._student_layout.setContentsMargins(0, 4, 0, 4)
        self._student_layout.setSpacing(4)
        self._student_layout.addStretch()
        self.student_scroll.setWidget(self._student_container)
        left_layout.addWidget(self.student_scroll)

        # right side - section picker + activity feed
        right_card = Card()
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 14, 16, 14)
        right_layout.setSpacing(10)

        # section list at top of right panel
        right_layout.addWidget(label("Section", size=11, color=C["text3"]))
        self.section_scroll = QScrollArea()
        self.section_scroll.setWidgetResizable(True)
        self.section_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.section_scroll.setFixedHeight(180)
        self._section_container = QWidget()
        self._section_layout = QVBoxLayout(self._section_container)
        self._section_layout.setContentsMargins(0, 0, 0, 0)
        self._section_layout.setSpacing(2)
        self._section_layout.addStretch()
        self.section_scroll.setWidget(self._section_container)
        right_layout.addWidget(self.section_scroll)

        self._selected_path = None
        btn_row = QHBoxLayout()
        btn_refresh = TapButton("Refresh", "secondary")
        btn_refresh.setFixedWidth(90)
        btn_refresh.clicked.connect(self._refresh_sections)
        btn_load = TapButton("Load", "primary")
        btn_load.setFixedWidth(90)
        btn_load.clicked.connect(self._load_selected)
        btn_row.addWidget(btn_refresh)
        btn_row.addStretch()
        btn_row.addWidget(btn_load)
        right_layout.addLayout(btn_row)
        right_layout.addWidget(h_line())

        # activity log at bottom
        right_layout.addWidget(label("Activity", size=11, color=C["text3"]))
        self.activity = QTextEdit()
        self.activity.setReadOnly(True)
        self.activity.setFont(QFont(_F_MONO, 11))
        right_layout.addWidget(self.activity, 1)

        splitter.addWidget(left_card)
        splitter.addWidget(right_card)
        splitter.setSizes([760, 520])
        root.addWidget(splitter, 1)

        self._refresh_sections()

    def _refresh_sections(self):
        while self._section_layout.count() > 1:
            item = self._section_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sdir = sections_dir_from_settings(self.app.settings)
        sdir.mkdir(parents=True, exist_ok=True)
        files = sorted(sdir.glob("*.csv"))
        if not files:
            self._section_layout.insertWidget(0, label("No sections found", size=11, color=C["text3"]))
            return
        for f in files:
            course, section, _ = parse_section_file(f)
            lbl_text = f"{course} — {section}" if course else f.name
            btn = QPushButton(lbl_text)
            btn.setFlat(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(30)
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 0 10px;
                    background: transparent;
                    border: none;
                    border-radius: 6px;
                    color: {C["text2"]};
                    font-family: "{_F_TEXT}";
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: {C["surface2"]};
                    color: {C["text"]};
                }}
            """)
            btn.clicked.connect(lambda checked, p=f, t=lbl_text: self._select_section(p, t))
            self._section_layout.insertWidget(self._section_layout.count() - 1, btn)

    def _select_section(self, path, label_text):
        self._selected_path = path
        self.log(f"Selected: {label_text}")

    def _load_selected(self):
        if not self._selected_path:
            self.log("⚠ No section selected.")
            return
        course, section, students = parse_section_file(self._selected_path)
        if not students:
            self.log("⚠ Section file empty or invalid.")
            return
        self.loaded_course   = course
        self.loaded_section  = section
        self.loaded_students = students
        self.attendance      = {}
        self.tapped_ids      = set()
        self.active          = False
        self.btn_activate.setText("Activate Logging")
        self.btn_activate._apply_style(False)
        self.btn_activate._style_key = "success"
        self.btn_activate._apply_style(False)
        self.lbl_section.setText(f"{course} — Section {section}")
        self.lbl_count.setText(f"{len(students)} students")
        self._build_student_rows()
        self.log(f"✓ Loaded {course}-{section} ({len(students)} students)")
        self.app.logger.log_event(f"Loaded {course}-{section}")

    def _build_student_rows(self):
        self._row_widgets = {}
        while self._student_layout.count() > 1:
            item = self._student_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, s in enumerate(self.loaded_students):
            sid = s["student_id"].strip()
            row = StudentRow(s["first"], s["last"], sid, even=(i % 2 == 0))
            row.present_clicked.connect(lambda s=sid: self._manual_override(s, "present"))
            row.absent_clicked.connect(lambda s=sid: self._manual_override(s, "absent"))
            self._student_layout.insertWidget(self._student_layout.count() - 1, row)
            self._row_widgets[sid] = row

    def _toggle_active(self):
        if not self.loaded_students:
            self.log("⚠ Load a section first.")
            return
        self.active = not self.active
        if self.active:
            self.btn_activate.setText("Stop Logging")
            self.btn_activate._style_key = "danger"
            self.btn_activate._apply_style(False)
            self.log("● Attendance logging active.")
            self.app.logger.log_event("Logging activated")
        else:
            self.btn_activate.setText("Activate Logging")
            self.btn_activate._style_key = "success"
            self.btn_activate._apply_style(False)
            self.log("■ Logging stopped.")
            self.app.logger.log_event("Logging deactivated")

    def on_tap(self, uid, issue, student_id):
        student_id = student_id.strip()
        if not self.active:
            self.log(f"[serial] tap ID={student_id} — logging not active")
            return
        if student_id in self.tapped_ids:
            self.log(f"↩ Duplicate tap — ID {student_id}")
            self.app.logger.log_tap(uid, issue, student_id, status="DUPLICATE")
            return
        match = next((s for s in self.loaded_students
                      if s["student_id"].strip() == student_id), None)
        self.log(f"→ Tap: ID={student_id}  match={'YES' if match else 'NO'}")
        if match:
            name = f"{match['first']} {match['last']}"
            ts   = datetime.now().strftime("%H:%M:%S")
            self.attendance[student_id] = {"status": "PRESENT", "time": ts}
            self.tapped_ids.add(student_id)
            if student_id in self._row_widgets:
                self._row_widgets[student_id].set_state("present")
            self.log(f"✓ {name}  ({student_id})  {ts}")
            self.app.logger.log_tap(uid, issue, student_id, name=name, status="PRESENT")
            present = sum(1 for v in self.attendance.values() if v["status"] == "PRESENT")
            self.lbl_count.setText(f"{present}/{len(self.loaded_students)} present")
        else:
            self.log(f"⚠ ID {student_id} not in {self.loaded_course}-{self.loaded_section}")
            self.app.logger.log_tap(uid, issue, student_id, status="WRONG_SECTION")

    def _manual_override(self, sid, state):
        student = next((s for s in self.loaded_students
                        if s["student_id"].strip() == sid), None)
        if not student:
            return
        name = f"{student['first']} {student['last']}"
        ts   = datetime.now().strftime("%H:%M:%S")
        if state == "present":
            self.attendance[sid] = {"status": "PRESENT", "time": ts}
            self.tapped_ids.add(sid)
            if sid in self._row_widgets:
                self._row_widgets[sid].set_state("present")
            self.log(f"✓ {name}  ({sid})  {ts}  [manual]")
            self.app.logger.log_tap("MANUAL", "00", sid, name=name,
                                    status="PRESENT", note="manual override")
        else:
            self.attendance.pop(sid, None)
            self.tapped_ids.discard(sid)
            if sid in self._row_widgets:
                self._row_widgets[sid].set_state("absent")
            self.log(f"✗ {name}  ({sid})  absent  [manual]")
            self.app.logger.log_tap("MANUAL", "00", sid, name=name,
                                    status="ABSENT", note="manual override")
        present = sum(1 for v in self.attendance.values() if v["status"] == "PRESENT")
        self.lbl_count.setText(f"{present}/{len(self.loaded_students)} present")

    def _save_log(self):
        if not self.loaded_students:
            self.log("⚠ Nothing to save — no section loaded.")
            return
        path = save_attendance_log(LOGS_DIR, self.loaded_course, self.loaded_section,
                                   self.loaded_students, self.attendance)
        if path:
            self.log(f"✓ Saved → {path.name}")
            self.app.logger.log_event(f"Attendance saved: {path}")
        else:
            self.log("✗ Save failed.")

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.activity.append(f'<span style="color:{C["text3"]}">{ts}</span>  '
                             f'<span style="color:{C["text2"]}">{msg}</span>')
        sb = self.activity.verticalScrollBar()
        sb.setValue(sb.maximum())


# class manager tab - create/edit/delete section rosters
class ClassManager(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app           = app
        self._current_file = None
        self._student_rows = []
        self._unsaved      = False
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)

        # left - section file list
        left_card = Card()
        ll = QVBoxLayout(left_card)
        ll.setContentsMargins(14, 14, 14, 14)
        ll.setSpacing(8)
        ll.addWidget(label("Section", size=15, weight=700))
        ll.addWidget(h_line())

        btns = QHBoxLayout()
        btn_new = TapButton("+ New", "primary")
        btn_new.setFixedWidth(90)
        btn_new.clicked.connect(self._new_section)
        btn_refresh = TapButton("Refresh", "secondary")
        btn_refresh.setFixedWidth(86)
        btn_refresh.clicked.connect(self._refresh_list)
        btns.addWidget(btn_new)
        btns.addStretch()
        btns.addWidget(btn_refresh)
        ll.addLayout(btns)

        self.file_scroll = QScrollArea()
        self.file_scroll.setWidgetResizable(True)
        self.file_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._file_container = QWidget()
        self._file_layout = QVBoxLayout(self._file_container)
        self._file_layout.setContentsMargins(0, 0, 0, 0)
        self._file_layout.setSpacing(2)
        self._file_layout.addStretch()
        self.file_scroll.setWidget(self._file_container)
        ll.addWidget(self.file_scroll, 1)

        # right - editor
        right_card = Card()
        rl = QVBoxLayout(right_card)
        rl.setContentsMargins(16, 14, 16, 14)
        rl.setSpacing(10)

        # header row with title + save/delete
        eh = QHBoxLayout()
        self.lbl_title = label("No file open", size=15, weight=700)
        self.lbl_unsaved = label("", size=11, color=C["warn"])
        eh.addWidget(self.lbl_title)
        eh.addWidget(self.lbl_unsaved)
        eh.addStretch()
        btn_save = TapButton("Save", "success")
        btn_save.setFixedWidth(90)
        btn_save.clicked.connect(self._save_section)
        btn_del = TapButton("Delete Section", "danger")
        btn_del.setFixedWidth(140)
        btn_del.clicked.connect(self._delete_section)
        eh.addWidget(btn_save)
        eh.addWidget(btn_del)
        rl.addLayout(eh)
        rl.addWidget(h_line())

        # course name + section letter
        meta = Card()
        meta.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {C["surface2"]};
                border: 1px solid {C["border"]};
                border-radius: 10px;
            }}
        """)
        ml = QHBoxLayout(meta)
        ml.setContentsMargins(14, 12, 14, 12)
        ml.setSpacing(20)
        cv = QVBoxLayout()
        cv.addWidget(label("Course Name", size=11, color=C["text3"]))
        self.inp_course = make_input("e.g. EGR232", 200)
        cv.addWidget(self.inp_course)
        sv = QVBoxLayout()
        sv.addWidget(label("Section Letter", size=11, color=C["text3"]))
        self.inp_section = make_input("e.g. A", 100)
        sv.addWidget(self.inp_section)
        ml.addLayout(cv)
        ml.addLayout(sv)
        ml.addStretch()
        rl.addWidget(meta)

        # student list editor
        stu_card = Card()
        sl = QVBoxLayout(stu_card)
        sl.setContentsMargins(14, 12, 14, 12)
        sl.setSpacing(6)

        sh = QHBoxLayout()
        sh.addWidget(label("Students", size=11, color=C["text3"]))
        sh.addStretch()
        btn_add = TapButton("+ Add Student", "secondary")
        btn_add.setFixedWidth(130)
        btn_add.clicked.connect(lambda: self._add_student_row())
        sh.addWidget(btn_add)
        sl.addLayout(sh)

        # column headers
        hdr = QHBoxLayout()
        hdr.setContentsMargins(4, 0, 44, 0)
        for txt in ["First Name", "Last Name", "Student ID"]:
            hdr.addWidget(label(txt, size=10, color=C["text3"]), 1)
        sl.addLayout(hdr)
        sl.addWidget(h_line())

        self.student_scroll = QScrollArea()
        self.student_scroll.setWidgetResizable(True)
        self.student_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._stu_container = QWidget()
        self._stu_layout = QVBoxLayout(self._stu_container)
        self._stu_layout.setContentsMargins(0, 0, 0, 0)
        self._stu_layout.setSpacing(4)
        self._stu_layout.addStretch()
        self.student_scroll.setWidget(self._stu_container)
        sl.addWidget(self.student_scroll, 1)
        rl.addWidget(stu_card, 1)

        splitter.addWidget(left_card)
        splitter.addWidget(right_card)
        splitter.setSizes([300, 980])
        root.addWidget(splitter)

        self.inp_course.textChanged.connect(self._mark_unsaved)
        self.inp_section.textChanged.connect(self._mark_unsaved)
        self._refresh_list()

    def _refresh_list(self):
        while self._file_layout.count() > 1:
            item = self._file_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        sdir = sections_dir_from_settings(self.app.settings)
        sdir.mkdir(parents=True, exist_ok=True)
        files = sorted(sdir.glob("*.csv"))
        if not files:
            self._file_layout.insertWidget(0, label("No sections yet", size=11, color=C["text3"]))
            return
        for f in files:
            course, section, _ = parse_section_file(f)
            txt = f"{course} — {section}" if course else f.name
            btn = QPushButton(txt)
            btn.setFlat(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(32)
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 0 10px;
                    background: transparent;
                    border: none;
                    border-radius: 6px;
                    color: {C["text2"]};
                    font-family: "{_F_TEXT}";
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: {C["surface2"]};
                    color: {C["text"]};
                }}
            """)
            btn.clicked.connect(lambda checked, p=f, t=txt: self._open_file(p, t))
            self._file_layout.insertWidget(self._file_layout.count() - 1, btn)

    def _open_file(self, path, title):
        if self._unsaved:
            r = QMessageBox.question(self, "Unsaved Changes",
                "Discard unsaved changes and open new file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if r != QMessageBox.StandardButton.Yes:
                return
        course, section, students = parse_section_file(path)
        self._current_file = path
        self.inp_course.blockSignals(True)
        self.inp_section.blockSignals(True)
        self.inp_course.setText(course or "")
        self.inp_section.setText(section or "")
        self.inp_course.blockSignals(False)
        self.inp_section.blockSignals(False)
        self.lbl_title.setText(title)
        self._clear_student_rows()
        for s in students:
            self._add_student_row(s["first"], s["last"], s["student_id"])
        self._unsaved = False
        self.lbl_unsaved.setText("")

    def _clear_student_rows(self):
        for r in self._student_rows:
            r["widget"].deleteLater()
        self._student_rows = []

    def _add_student_row(self, first="", last="", sid=""):
        w = QWidget()
        w.setStyleSheet(f"""
            QWidget {{
                background-color: {C["surface2"]};
                border-radius: 6px;
            }}
        """)
        rl = QHBoxLayout(w)
        rl.setContentsMargins(4, 4, 4, 4)
        rl.setSpacing(4)

        fv = make_input("First")
        lv = make_input("Last")
        iv = make_input("Student ID")
        fv.setText(first); lv.setText(last); iv.setText(sid)
        fv.setFixedHeight(32); lv.setFixedHeight(32); iv.setFixedHeight(32)

        for e in [fv, lv, iv]:
            e.textChanged.connect(self._mark_unsaved)
            rl.addWidget(e, 1)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                color: {C["text3"]};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {C["red"]};
                color: white;
            }}
        """)

        entry = {"widget": w, "first": fv, "last": lv, "id": iv}
        del_btn.clicked.connect(lambda checked, e=entry: self._remove_row(e))
        rl.addWidget(del_btn)

        self._stu_layout.insertWidget(self._stu_layout.count() - 1, w)
        self._student_rows.append(entry)

    def _remove_row(self, entry):
        entry["widget"].deleteLater()
        self._student_rows = [r for r in self._student_rows if r is not entry]
        self._mark_unsaved()

    def _mark_unsaved(self):
        self._unsaved = True
        self.lbl_unsaved.setText("● Unsaved changes")

    def _save_section(self):
        course  = self.inp_course.text().strip()
        section = self.inp_section.text().strip()
        if not course or not section:
            QMessageBox.warning(self, "TapIn", "Course name and section letter are required.")
            return
        students = []
        for r in self._student_rows:
            f = r["first"].text().strip()
            l = r["last"].text().strip()
            i = r["id"].text().strip()
            if f or l or i:
                students.append({"first": f, "last": l, "student_id": i})
        sdir = sections_dir_from_settings(self.app.settings)
        path = self._current_file or (sdir / f"{course}_{section}.csv".replace(" ", "_"))
        write_section_file(path, course, section, students)
        self._current_file = path
        self._unsaved = False
        self.lbl_unsaved.setText("✓ Saved")
        self.lbl_title.setText(f"{course} — {section}")
        QTimer.singleShot(2500, lambda: self.lbl_unsaved.setText(""))
        self._refresh_list()
        self.app.logger.log_event(f"Saved section {course}-{section}")

    def _new_section(self):
        if self._unsaved:
            r = QMessageBox.question(self, "Unsaved Changes",
                "Discard unsaved changes and create new?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if r != QMessageBox.StandardButton.Yes:
                return
        self._current_file = None
        self.inp_course.blockSignals(True)
        self.inp_section.blockSignals(True)
        self.inp_course.clear(); self.inp_section.clear()
        self.inp_course.blockSignals(False)
        self.inp_section.blockSignals(False)
        self.lbl_title.setText("New Section")
        self._clear_student_rows()
        self._unsaved = False
        self.lbl_unsaved.setText("")

    def _delete_section(self):
        if not self._current_file:
            return
        r = QMessageBox.question(self, "Delete Section",
            f"Permanently delete {self._current_file.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r != QMessageBox.StandardButton.Yes:
            return
        try:
            self._current_file.unlink()
            self.app.logger.log_event(f"Deleted {self._current_file.name}")
        except Exception as e:
            QMessageBox.critical(self, "TapIn", f"Could not delete: {e}")
            return
        self._current_file = None
        self.inp_course.clear(); self.inp_section.clear()
        self.lbl_title.setText("No file open")
        self._clear_student_rows()
        self._unsaved = False
        self.lbl_unsaved.setText("")
        self._refresh_list()

    def has_unsaved(self):
        return self._unsaved


# attendance history tab - browse past logs
class AttendanceHistory(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app              = app
        self._hist_students   = []
        self._hist_attendance = {}
        self._hist_meta       = None
        self._hist_rows       = {}
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)

        # left - log tree browser
        left_card = Card()
        ll = QVBoxLayout(left_card)
        ll.setContentsMargins(14, 14, 14, 14)
        ll.setSpacing(8)
        lh = QHBoxLayout()
        lh.addWidget(label("Attendance Logs", size=15, weight=700))
        lh.addStretch()
        btn_ref = TapButton("Refresh", "secondary")
        btn_ref.setFixedWidth(86)
        btn_ref.clicked.connect(self.refresh)
        lh.addWidget(btn_ref)
        ll.addLayout(lh)
        ll.addWidget(h_line())

        self.tree_scroll = QScrollArea()
        self.tree_scroll.setWidgetResizable(True)
        self.tree_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._tree_container = QWidget()
        self._tree_layout = QVBoxLayout(self._tree_container)
        self._tree_layout.setContentsMargins(0, 0, 0, 0)
        self._tree_layout.setSpacing(1)
        self._tree_layout.addStretch()
        self.tree_scroll.setWidget(self._tree_container)
        ll.addWidget(self.tree_scroll, 1)

        # right - log viewer
        right_card = Card()
        rl = QVBoxLayout(right_card)
        rl.setContentsMargins(16, 14, 16, 14)
        rl.setSpacing(4)

        self.lbl_log_title = label("Select a log from the left", size=15, weight=700)
        self.lbl_log_title.setContentsMargins(0, 18, 0, 4)
        self.lbl_log_meta  = label("", size=11, color=C["text3"])
        self.lbl_log_meta.setContentsMargins(0, 0, 0, 4)
        rl.addWidget(self.lbl_log_title)
        rl.addWidget(self.lbl_log_meta)
        rl.addWidget(h_line())

        self.log_scroll = QScrollArea()
        self.log_scroll.setWidgetResizable(True)
        self.log_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._log_container = QWidget()
        self._log_layout = QVBoxLayout(self._log_container)
        self._log_layout.setContentsMargins(0, 4, 0, 4)
        self._log_layout.setSpacing(4)
        self._log_layout.addStretch()
        self.log_scroll.setWidget(self._log_container)
        rl.addWidget(self.log_scroll, 1)

        splitter.addWidget(left_card)
        splitter.addWidget(right_card)
        splitter.setSizes([600, 680])
        root.addWidget(splitter)

        self.refresh()

    def refresh(self):
        while self._tree_layout.count() > 1:
            item = self._tree_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not LOGS_DIR.exists():
            self._tree_layout.insertWidget(0, label("No logs yet", size=11, color=C["text3"]))
            return

        courses = sorted([d for d in LOGS_DIR.iterdir() if d.is_dir()])
        if not courses:
            self._tree_layout.insertWidget(0, label("No logs yet", size=11, color=C["text3"]))
            return

        idx = 0
        for course_dir in courses:
            btn = SectionTreeItem(f"  {course_dir.name}", indent=0, is_header=True, clickable=False)
            self._tree_layout.insertWidget(idx, btn); idx += 1

            sections = sorted([d for d in course_dir.iterdir() if d.is_dir()])
            for sec_dir in sections:
                sec_btn = SectionTreeItem(f"  ├─  {sec_dir.name}", indent=8,
                                          is_header=False, clickable=False)
                self._tree_layout.insertWidget(idx, sec_btn); idx += 1

                logs  = sorted(sec_dir.glob("*.csv"), reverse=True)
                total = len(logs)
                for li, log_file in enumerate(logs):
                    is_last = li == total - 1
                    prefix  = "└─" if is_last else "├─"
                    stem    = log_file.stem
                    parts   = stem.split("_")
                    date    = parts[-1] if parts else stem
                    log_btn = SectionTreeItem(f"        {prefix}  {date}",
                                              indent=16, is_header=False, clickable=True)
                    log_btn.clicked.connect(lambda checked, p=log_file: self._load_log(p))
                    self._tree_layout.insertWidget(idx, log_btn); idx += 1

    def _load_log(self, path):
        course, section, date_str, students = parse_attendance_log(path)
        if not students:
            self.lbl_log_title.setText("Could not read log file")
            return
        present = sum(1 for s in students if s["status"] == "PRESENT")
        self.lbl_log_title.setText(f"{course} — Section {section}  ·  {date_str}")
        self.lbl_log_meta.setText(
            f"{len(students)} students  •  {present} present  •  {len(students)-present} absent")
        self._hist_students   = students
        self._hist_attendance = {s["student_id"]: {"status": s["status"], "time": s["time"]}
                                  for s in students}
        self._hist_meta       = (course, section, date_str, path)
        self._build_log_rows()

    def _build_log_rows(self):
        self._hist_rows = {}
        while self._log_layout.count() > 1:
            item = self._log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, s in enumerate(self._hist_students):
            sid    = s["student_id"].strip()
            status = s["status"]
            row = StudentRow(s["first"], s["last"], sid, even=(i % 2 == 0),
                             show_time=True, time_str=s["time"])
            row.present_clicked.connect(lambda s=sid: self._hist_override(s, "present"))
            row.absent_clicked.connect(lambda s=sid: self._hist_override(s, "absent"))
            row.set_state("present" if status == "PRESENT" else "absent")
            self._log_layout.insertWidget(self._log_layout.count() - 1, row)
            self._hist_rows[sid] = row

    def _hist_override(self, sid, state):
        ts = datetime.now().strftime("%H:%M:%S")
        if state == "present":
            self._hist_attendance[sid] = {"status": "PRESENT", "time": ts}
            if sid in self._hist_rows:
                self._hist_rows[sid].set_state("present")
        else:
            self._hist_attendance[sid] = {"status": "ABSENT", "time": ""}
            if sid in self._hist_rows:
                self._hist_rows[sid].set_state("absent")

        if self._hist_meta:
            course, section, date_str, path = self._hist_meta
            try:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow([course, section, date_str])
                    w.writerow(["FirstName","LastName","StudentID","Status","Timestamp"])
                    for s in self._hist_students:
                        s_sid  = s["student_id"].strip()
                        status = self._hist_attendance.get(s_sid, {}).get("status", "ABSENT")
                        t      = self._hist_attendance.get(s_sid, {}).get("time", "")
                        w.writerow([s["first"], s["last"], s_sid, status, t])
            except Exception as e:
                print(f"hist_override save error: {e}")

        present = sum(1 for v in self._hist_attendance.values()
                      if v.get("status") == "PRESENT")
        n = len(self._hist_students)
        self.lbl_log_meta.setText(
            f"{n} students  •  {present} present  •  {n - present} absent")
        self.app.logger.log_event(f"HIST_OVERRIDE | ID={sid} | {state.upper()}")


# settings dialog
class SettingsDialog(QDialog):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.setWindowTitle("TapIn — Settings")
        self.setMinimumSize(860, 640)
        self.setStyleSheet(f"background-color: {C['bg']}; color: {C['text']};")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)
        root.addWidget(label("Settings", size=17, weight=700))
        root.addWidget(h_line())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 8, 0)
        cl.setSpacing(16)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # serial / reader connection section
        cl.addWidget(label("Reader / Serial Connection", size=11, color=C["text3"]))
        serial_card = Card()
        sl = QVBoxLayout(serial_card)
        sl.setContentsMargins(16, 14, 16, 14)
        sl.setSpacing(10)

        # port selection
        pr = QHBoxLayout()
        pr.addWidget(label("Serial Port", size=12))
        ports = [p.device for p in serial.tools.list_ports.comports()] or ["(none found)"]
        saved = self.app.settings.get("serial_port", "auto")
        if saved not in ports and saved != "auto":
            ports.insert(0, saved)
        self.combo_port = make_combo(ports)
        if saved in ports:
            self.combo_port.setCurrentText(saved)
        self.combo_port.setFixedWidth(200)
        pr.addWidget(self.combo_port)
        btn_scan = TapButton("Scan Ports", "secondary")
        btn_scan.setFixedWidth(110)
        btn_scan.clicked.connect(self._scan_ports)
        pr.addWidget(btn_scan)
        pr.addStretch()
        sl.addLayout(pr)

        # baud rate
        br = QHBoxLayout()
        br.addWidget(label("Baud Rate", size=12))
        self.combo_baud = make_combo(["115200", "57600", "38400", "9600"])
        self.combo_baud.setCurrentText(str(self.app.settings.get("serial_baud", 115200)))
        self.combo_baud.setFixedWidth(130)
        br.addWidget(self.combo_baud)
        br.addStretch()
        sl.addLayout(br)

        # auto connect toggle
        ar = QHBoxLayout()
        ar.addWidget(label("Auto-connect on launch", size=12))
        self.chk_auto = QCheckBox()
        self.chk_auto.setChecked(self.app.settings.get("auto_connect", True))
        ar.addWidget(self.chk_auto)
        ar.addStretch()
        sl.addLayout(ar)

        # connect disconnect buttons
        cr = QHBoxLayout()
        btn_conn = TapButton("Connect", "success")
        btn_conn.setFixedWidth(110)
        btn_conn.clicked.connect(self._connect)
        btn_disc = TapButton("Disconnect", "danger")
        btn_disc.setFixedWidth(120)
        btn_disc.clicked.connect(self._disconnect)
        self.lbl_conn_status = label("", size=11, color=C["text3"])
        cr.addWidget(btn_conn)
        cr.addWidget(btn_disc)
        cr.addWidget(self.lbl_conn_status)
        cr.addStretch()
        sl.addLayout(cr)

        # show recent serial activity
        sl.addWidget(label("Recent serial activity", size=11, color=C["text3"]))
        self.serial_log = QTextEdit()
        self.serial_log.setReadOnly(True)
        self.serial_log.setFixedHeight(100)
        sl.addWidget(self.serial_log)
        self._populate_serial_log()
        cl.addWidget(serial_card)

        # log file directory
        cl.addWidget(label("Session Log Directory", size=11, color=C["text3"]))
        log_card = Card()
        ll = QHBoxLayout(log_card)
        ll.setContentsMargins(16, 14, 16, 14)
        self.inp_log_dir = QLineEdit(self.app.settings.get("log_dir", str(SESSION_LOGS_DIR)))
        self.inp_log_dir.setReadOnly(True)
        self.inp_log_dir.setFixedHeight(34)
        ll.addWidget(self.inp_log_dir, 1)
        btn_log = TapButton("Change…", "secondary")
        btn_log.setFixedWidth(100)
        btn_log.clicked.connect(self._change_log_dir)
        ll.addWidget(btn_log)
        cl.addWidget(log_card)

        # class sections folder
        cl.addWidget(label("Class Sections Directory", size=11, color=C["text3"]))
        sec_card = Card()
        secl = QHBoxLayout(sec_card)
        secl.setContentsMargins(16, 14, 16, 14)
        self.inp_sec_dir = QLineEdit(self.app.settings.get("sections_dir", str(SECTIONS_DIR)))
        self.inp_sec_dir.setReadOnly(True)
        self.inp_sec_dir.setFixedHeight(34)
        secl.addWidget(self.inp_sec_dir, 1)
        btn_sec = TapButton("Change…", "secondary")
        btn_sec.setFixedWidth(100)
        btn_sec.clicked.connect(self._change_sec_dir)
        btn_refresh = TapButton("Refresh", "ghost")
        btn_refresh.setFixedWidth(90)
        btn_refresh.clicked.connect(self._refresh_all)
        secl.addWidget(btn_sec)
        secl.addWidget(btn_refresh)
        cl.addWidget(sec_card)
        cl.addStretch()

        # save button at the bottom
        save_row = QHBoxLayout()
        save_row.addStretch()
        btn_save = TapButton("Save Settings", "primary")
        btn_save.setFixedWidth(160)
        btn_save.clicked.connect(self._save)
        save_row.addWidget(btn_save)
        root.addLayout(save_row)

        self._update_conn_label()

    def _scan_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            ports = ["(none found)"]
        self.combo_port.clear()
        self.combo_port.addItems(ports)

    def _connect(self):
        port = self.combo_port.currentText().strip()
        if not port or port == "(none found)":
            QMessageBox.warning(self, "TapIn", "No port selected. Plug in ESP32 and click Scan Ports.")
            return
        try:
            baud = int(self.combo_baud.currentText())
        except ValueError:
            baud = 115200
        self.app.settings["serial_port"] = port
        self.app.settings["serial_baud"] = baud
        self.app.start_serial(port, baud)
        QTimer.singleShot(500, self._update_conn_label)
        QTimer.singleShot(3000, self._populate_serial_log)

    def _disconnect(self):
        self.app.stop_serial()
        QTimer.singleShot(200, self._update_conn_label)

    def _update_conn_label(self):
        if self.app._connected:
            self.lbl_conn_status.setText(f"● Connected — {self.app.settings.get('serial_port','?')}")
            self.lbl_conn_status.setStyleSheet(f"color: {C['green']}; background: transparent;")
        else:
            self.lbl_conn_status.setText("● Disconnected")
            self.lbl_conn_status.setStyleSheet(f"color: {C['red']}; background: transparent;")

    def _populate_serial_log(self):
        try:
            path = self.app.logger.path
            if path.exists():
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
                recent = [l for l in lines if "SERIAL:" in l or "EVENT" in l][-12:]
                self.serial_log.setPlainText("\n".join(recent))
        except Exception:
            pass

    def _change_log_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select log directory")
        if d:
            self.inp_log_dir.setText(d)

    def _change_sec_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select sections directory")
        if d:
            self.inp_sec_dir.setText(d)

    def _refresh_all(self):
        self.app.attendance_view._refresh_sections()
        self.app.class_manager._refresh_list()

    def _save(self):
        port = self.combo_port.currentText().strip()
        self.app.settings["serial_port"]  = port if port != "(none found)" else "auto"
        try:
            self.app.settings["serial_baud"] = int(self.combo_baud.currentText())
        except ValueError:
            self.app.settings["serial_baud"] = 115200
        self.app.settings["auto_connect"] = self.chk_auto.isChecked()
        self.app.settings["log_dir"]      = self.inp_log_dir.text()
        self.app.settings["sections_dir"] = self.inp_sec_dir.text()
        save_settings(self.app.settings)
        self.app.logger.change_dir(self.app.settings["log_dir"])
        self.app.logger.log_event("Settings saved")
        self.accept()


# tab bar buttons
class TabButton(QPushButton):
    """Nav tab pill button with active/inactive states."""
    def __init__(self, text, dot_color=None):
        super().__init__(text)
        self._active = False
        self._dot    = dot_color or C["accent"]
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(34)
        self._apply()

    def set_active(self, v):
        self._active = v
        self._apply()

    def _apply(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C["surface2"]};
                    color: {C["text"]};
                    border: 1px solid {C["border2"]};
                    border-radius: 9px;
                    padding: 0 12px;
                    font-family: "{_F_TEXT}";
                    font-size: 13px;
                    font-weight: 600;
                    letter-spacing: 0.2px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {C["text3"]};
                    border: 1px solid transparent;
                    border-radius: 9px;
                    padding: 0 12px;
                    font-family: "{_F_TEXT}";
                    font-size: 13px;
                    font-weight: 400;
                    letter-spacing: 0.2px;
                }}
                QPushButton:hover {{
                    background-color: {C["surface"]};
                    color: {C["text2"]};
                    border: 1px solid {C["border"]};
                }}
            """)


# main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings    = load_settings()
        if self.settings.get("log_dir") == str(BASE_DIR):
            self.settings["log_dir"] = str(SESSION_LOGS_DIR)
        self.logger      = SessionLogger(self.settings.get("log_dir", str(SESSION_LOGS_DIR)))
        self._serial_thr = None
        self._connected  = False

        SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        SESSION_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        sections_dir_from_settings(self.settings).mkdir(parents=True, exist_ok=True)

        self.setWindowTitle("TapIn • Attendance Platform")
        self.setMinimumSize(1000, 700)
        self.resize(1320, 820)

        self._build()
        self.logger.log_event("TapIn launched (Qt)")

        if self.settings.get("auto_connect", True):
            port = self.settings.get("serial_port", "auto")
            if port == "auto":
                port = auto_detect_port()
            baud = self.settings.get("serial_baud", 115200)
            if port:
                QTimer.singleShot(800, lambda: self.start_serial(port, baud))

    def _build(self):
        # central widget with gradient bg
        central = GradientWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # top chrome bar
        chrome = QWidget()
        chrome.setFixedHeight(72)
        chrome.setStyleSheet(f"""
            QWidget {{
                background-color: {C["bg2"]};
                border-bottom: 1px solid {C["border"]};
            }}
        """)
        cl = QHBoxLayout(chrome)
        cl.setContentsMargins(20, 0, 16, 0)
        cl.setSpacing(0)

        # app name / logo
        name_lbl = QLabel("TapIn")
        name_lbl.setStyleSheet(f"""
            color: {C['text']};
            background: transparent;
            font-family: "{_F_DISPLAY}";
            font-size: 36px;
            font-weight: 700;
        """)
        cl.addWidget(name_lbl)
        cl.addSpacing(32)

        # tab buttons
        self._tabs = {}
        tab_data = [
            ("attendance", "Attendance View",    C["green"]),
            ("manager",    "Class Manager",      C["accent"]),
            ("history",    "Attendance History", C["warn"]),
        ]
        for key, txt, dot in tab_data:
            btn = TabButton(txt, dot)
            btn.clicked.connect(lambda checked, k=key: self._switch_tab(k))
            self._tabs[key] = btn
            cl.addWidget(btn)
            cl.addSpacing(4)

        cl.addStretch()

        # settings cog button
        cog = QPushButton("⚙")
        cog.setFixedSize(36, 36)
        cog.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cog.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 8px;
                color: {C["text3"]};
                font-size: 18px;
            }}
            QPushButton:hover {{
                background: {C["surface"]};
                border: 1px solid {C["border"]};
                color: {C["text"]};
            }}
        """)
        cog.clicked.connect(self._open_settings)
        cl.addWidget(cog)

        main_layout.addWidget(chrome)

        # ── Stacked content ───────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        self.attendance_view = AttendanceView(self)
        self.class_manager   = ClassManager(self)
        self.history_view    = AttendanceHistory(self)

        self.stack.addWidget(self.attendance_view)
        self.stack.addWidget(self.class_manager)
        self.stack.addWidget(self.history_view)

        main_layout.addWidget(self.stack, 1)

        # status bar at bottom
        status_bar = QWidget()
        status_bar.setFixedHeight(40)
        status_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {C["bg2"]};
                border-top: 1px solid {C["border"]};
            }}
        """)
        sbl = QHBoxLayout(status_bar)
        sbl.setContentsMargins(16, 0, 20, 0)

        app_label = label("TapIn  •  NFC Attendance System  •  Created by tylerallen", size=11, color=C["text3"])
        sbl.addWidget(app_label)
        sbl.addStretch()

        self._status_lbl = label("Reader: Disconnected", size=13, weight=700, color=C["red"])
        self._status_dot = StatusDot()
        sbl.addWidget(self._status_lbl)
        sbl.addSpacing(8)
        sbl.addWidget(self._status_dot)

        main_layout.addWidget(status_bar)

        self._switch_tab("attendance")

    def _switch_tab(self, key):
        for k, btn in self._tabs.items():
            btn.set_active(k == key)
        idx = {"attendance": 0, "manager": 1, "history": 2}[key]
        self.stack.setCurrentIndex(idx)
        if key == "history":
            self.history_view.refresh()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def start_serial(self, port, baud):
        self.stop_serial()
        if not port:
            self.logger.log_event("start_serial: no port")
            return
        self.logger.log_event(f"Connecting: {port} @ {baud}")
        self._serial_thr = SerialReader(port, baud)
        self._serial_thr.tap_received.connect(self._on_tap)
        self._serial_thr.status_changed.connect(self._on_status)
        self._serial_thr.error_message.connect(self._on_serial_msg)
        self._serial_thr.start()

    def stop_serial(self):
        if self._serial_thr:
            self._serial_thr.stop()
            self._serial_thr.wait(2000)
            self._serial_thr = None
        self._on_status(False)

    def _on_tap(self, uid, issue, student_id):
        self.attendance_view.on_tap(uid, issue, student_id)

    def _on_serial_msg(self, msg):
        self.logger.log_event(f"SERIAL: {msg}")
        self.attendance_view.log(f"[serial] {msg}")

    def _on_status(self, connected):
        self._connected = connected
        self._status_dot.set_connected(connected)
        if connected:
            self._status_lbl.setText("Reader: Connected")
            self._status_lbl.setStyleSheet(f"color: {C['green']}; background: transparent; font-weight: 700;")
        else:
            self._status_lbl.setText("Reader: Disconnected")
            self._status_lbl.setStyleSheet(f"color: {C['red']}; background: transparent; font-weight: 700;")

    def closeEvent(self, event):
        if self.class_manager.has_unsaved():
            r = QMessageBox.question(self, "Unsaved Changes",
                "Class Manager has unsaved changes. Exit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if r != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        save_settings(self.settings)
        self.stop_serial()
        self.logger.log_event("TapIn closed")
        event.accept()


# entry point
if __name__ == "__main__":
    # hide console window when running as compiled exe
    if sys.platform == "win32" and getattr(sys, "frozen", False):
        try:
            sys.stdout = open(os.devnull, "w")
            sys.stderr = open(os.devnull, "w")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("TapIn")

    # load fonts manually - qt sometimes misses newly installed ones on windows
    if sys.platform == "win32":
        win_fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        font_files = [
            # Geist Sans (try common install names)
            "Geist-Regular.ttf", "Geist-Bold.ttf", "Geist-SemiBold.ttf",
            "Geist-Medium.ttf", "Geist-Light.ttf", "Geist-Black.ttf",
            "GeistVF.ttf", "Geist Variable.ttf", "GeistSans-Regular.ttf",
            # Geist Mono
            "GeistMono-Regular.ttf", "GeistMono-Bold.ttf",
            "GeistMono-Medium.ttf", "GeistMonoVF.ttf",
            # Inter fallback
            "Inter-Regular.ttf", "Inter-Bold.ttf", "Inter-SemiBold.ttf",
            "Inter_18pt-Regular.ttf", "Inter_18pt-Bold.ttf",
            "InterVariable.ttf", "Inter Variable.ttf",
        ]
        loaded = []
        for fname in font_files:
            fp = win_fonts / fname
            if fp.exists():
                QFontDatabase.addApplicationFont(str(fp))
                loaded.append(fname)
        if loaded:
            print(f"[TapIn] Loaded fonts from system: {loaded}")

    # resolve fonts now that qt is running
    _F_DISPLAY, _F_TEXT, _F_MONO = resolve_fonts()

    # apply styles
    app.setStyleSheet(build_qss())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
