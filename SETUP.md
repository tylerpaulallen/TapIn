# TapIn — Setup & Installation Guide

---

## Requirements

### Software
- Python 3.10 or newer ([python.org](https://www.python.org/downloads/))
- Arduino IDE 2.x ([arduino.cc](https://www.arduino.cc/en/software))

### Python Packages
```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---|---|
| `pyserial` | ESP32 serial communication |
| `customtkinter` | UI framework |
| `Pillow` | Image support |
| `pyinstaller` | Optional — compile to `.exe` |

> **Important:** The correct serial package is `pyserial`, not `serial`. If you see an import error on launch, run:
> ```bash
> pip uninstall serial
> pip uninstall pyserial
> pip install pyserial
> ```

---

## Hardware Setup

### Components Needed
- ESP32-S3 DevKitC-1
- Elechouse PN532 NFC/RFID Module v3
- Jumper wires (female-to-female, 6 wires minimum)
- USB cable (USB-A to USB-C or Micro depending on your ESP32 board)

### PN532 Dip Switch Configuration

Before wiring, set the PN532 dip switches to **SPI mode** otherwise the PNC532 will never work:

| Switch | Position |
|---|---|
| SW1 | OFF |
| SW2 | ON |

> If the switches are in any other position the reader will not respond over SPI and you will never get an output to print ever.

### Wiring

| PN532 Pin | ESP32-S3 GPIO | ESP32 Physical Pin |
|---|---|---|
| SCK | GPIO12 | Physical Pin 12 |
| MISO | GPIO13 | Physical Pin 13 |
| MOSI | GPIO11 | Physical Pin 11 |
| SS / NSS | GPIO10 | Physical Pin 10 |
| VCC | — | 3.3V (Physical Pin 2) |
| GND | — | GND (Physical Pin 1) |

> Connect VCC to the **3.3V** pin, not 5V. Most Elechouse boards have an onboard regulator and can accept 5V, but 3.3V is always safe.

> **Tip:** For a reliable permanent-ish connection without soldering, seat both boards into a breadboard and run short jumper wires between them. The PN532 ships with loose header pins intended to be soldered — soldering them to the board first gives the most stable connection.

---

## Arduino Firmware

### Library Installation
1. Open Arduino IDE
2. Go to **Tools → Manage Libraries**
3. Search for `Adafruit PN532` and install it
4. Also install `Adafruit BusIO` if prompted

### Board Setup
1. Go to **File → Preferences** and add the ESP32 boards URL:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
2. Go to **Tools → Board → Boards Manager**, search `esp32`, and install the Espressif package
3. Select **Tools → Board → ESP32S3 Dev Module**

### Firmware Configuration
The firmware authenticates to a specific sector on the MIFARE Classic 1K card using an A sector key. The key must match the key provisioned on your institution's cards. Set the key in the firmware before flashing:

```cpp
uint8_t keyA[6] = { 0xXX, 0xXX, 0xXX, 0xXX, 0xXX, 0xXX };
```

> The sector key is specific to your institution's card system. Do not commit the key to a public repository.

### Flashing
1. Plug the ESP32 into your computer via USB
2. Select the correct port under **Tools → Port**
3. Click **Upload**
4. Open **Tools → Serial Monitor**, set baud to `115200`
5. Hold a card over the reader — you should see smiliar output like:
   ```
   Card detected. UID: A1 B2 C3 D4
   Auth OK.
   Block 52 (hex): 30 31 30 30 30 39 39 39 39 39 39 00 00 00 00 00
   Block 52 (ASCII): 01000999999
   ```

> **Close the Serial Monitor before launching TapIn.** Windows COM ports can only be held by one application at a time — if Arduino IDE's Serial Monitor is open, TapIn cannot connect.

---

## Running TapIn

```bash
python tapin.py
```

On first launch, TapIn will automatically create:
- `class_sections/` — for roster CSV files
- `attendance_logs/` — for dated attendance records
- `session_logs/` — for raw tap audit logs
- `tapin_settings.json` — application settings

---

## First-Time Setup Walkthrough

### 1. Connect the Reader
1. Plug the ESP32 into your computer via USB
2. Launch TapIn
3. Click the **⚙** cog icon (top-right) to open Settings
4. Under **Reader / Serial Connection**, click **Scan Ports**
5. Select the COM port corresponding to your ESP32 (typically labeled CP210x, CH340, or USB Serial)
6. Click **Connect**
7. The status dot in the bottom-right corner should turn **green**
8. Click **Save Settings**

### 2. Create a Class Section
1. Click the **Class Manager** tab
2. Click **+ New**
3. Enter the course name (e.g. `EGR400`) and section letter (e.g. `A`)
4. Click **+ Add Student** for each student and fill in first name, last name, and student ID
5. Click **Save**

### 3. Take Attendance
1. Click the **Attendance View** tab
2. In the right panel, select your class section and click **Load**
3. Click **Activate Logging**
4. Students tap their ID cards — each matched student turns green immediately
5. Use the **Present / Absent** buttons on any row for manual override
6. Click **Save Log** when the session is complete

### 4. Review Past Sessions
1. Click the **Attendance History** tab
2. Expand the course and section in the left tree
3. Click a date to load that session's attendance record
4. Use override buttons to make any corrections — changes save immediately

---

## Compiling to Executable (Windows)

To distribute TapIn as a standalone `.exe` that does not require Python to be installed:

```bash
pyinstaller --onefile --windowed --name TapIn tapin.py
```

The compiled executable will be in the `dist/` folder. Copy `TapIn.exe` to your preferred location. All data folders are created automatically next to the `.exe` on first run.

---

## CSV File Format Reference

### Class Section Roster

```
EGR400,A
FirstName,LastName,StudentID
Jane,Smith,999991
John,Doe,999992
Alex,Johnson,999993
```

- Line 1: `CourseName,SectionLetter`
- Line 2+: one student per row

### Attendance Log

```
EGR400,A,2026-03-10
FirstName,LastName,StudentID,Status,Timestamp
Jane,Smith,999991,PRESENT,09:04:22
John,Doe,999992,PRESENT,09:05:01
Alex,Johnson,999993,ABSENT,
```

- Line 1: `CourseName,SectionLetter,Date`
- Line 2: column headers
- Line 3+: one student per row with status and check-in time

---

## Troubleshooting

### Reader not connecting / status stays red
- Confirm the PN532 dip switches are **SW1=OFF, SW2=ON** (SPI mode)
- Check that Arduino IDE Serial Monitor is fully closed
- Click **Scan Ports** in Settings and reselect the port
- Try unplugging and replugging the ESP32, then scan ports again
- Confirm the ESP32 firmware has been flashed successfully

### Status goes green but no card reads appear
- Confirm the firmware is running — open Arduino IDE Serial Monitor briefly to verify card reads appear there, then close it before using TapIn
- Check all six wires are seated firmly, especially MISO (GPIO13) — a loose MISO wire is the most common cause of silent read failures
- Verify the PN532 power light is on

### `serial` import error on launch
```bash
pip uninstall serial
pip uninstall pyserial
pip install pyserial
```

### Student taps card but nothing happens in the activity feed
- Confirm **Activate Logging** has been clicked (button should read "Stop Logging" in red)
- Confirm a section has been loaded — the student list must be visible before logging works

### Student taps card but shows as wrong section
- Confirm the student's ID in the Class Manager matches the ID encoded on their card exactly (6 digits, no leading zeros dropped)
- Check the activity feed — it will print the received ID and the list of known IDs side by side for comparison

### `PermissionError: Access is denied` on COM port
- Another application (typically Arduino IDE Serial Monitor) has the port open
- Close all other applications using the serial port and click Connect again

### App opens but window is very small
- The minimum window size is 1000×700 — drag the window edges to resize
- All three pane dividers are draggable for further layout adjustment

---

## Security Notes

- The sector Key used to authenticate the id block is stored in the Arduino firmware source. Do not commit a public version of the firmware with a real institutional key embedded.
- TapIn stores all data locally with no network transmission. No student data leaves the machine running the application.
- Session log files contain card UIDs. Treat `session_logs/` as sensitive if UID traceability is a concern at your institution.
