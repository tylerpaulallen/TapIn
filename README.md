# TapIn — NFC Attendance System

**TapIn** is a desktop attendance management system that uses NFC card scanning to automate student check-in for university courses. A professor loads a class roster, activates logging, and students tap their university ID cards on a physical reader to mark themselves present in real time — no apps, no QR codes, no manual roll call.

The system pairs an ESP32 microcontroller and a PN532 NFC reader with a Python desktop application built on PyQt6, communicating over USB serial. Everything runs locally with no internet connection required.

---

## How It Works

```
Student taps ID card → ESP32 reads NFC data block → Serial to TapIn → Student marked present
```

TapIn handles everything a professor needs to manage class attendance across multiple courses and sections — from building rosters to reviewing historical logs — through a single clean interface.

---

## Features

### Real-Time Attendance
- Students tap their MIFARE Classic 1K university ID card on the PN532 reader
- Student ID is extracted from the card's NFC data block and matched against the loaded roster
- Matched students are immediately marked **present** with a green indicator
- Unrecognized cards (wrong section, unknown ID) trigger a warning in the activity feed without disrupting the session
- Duplicate tap protection — a student can only be checked in once per session
- Live present/total count updates with every tap

### Manual Override
- Every student row has **Present** and **Absent** buttons for manual check-in
- Useful when a student forgets their ID card
- Manual overrides are logged identically to card taps, tagged as `[manual]`
- Works in both the live Attendance View and the Attendance History viewer for retroactive corrections

### Class Manager
- Create, edit, and delete class section rosters entirely through the UI — no raw CSV editing
- Per-student fields: first name, last name, student ID
- Add and remove individual students with inline delete buttons
- Unsaved changes indicator with confirmation dialog to prevent accidental data loss

### Attendance History
- All saved attendance logs are organized in a browsable tree by course and section
- Tree structure with visual branch indicators:
  ```
  EGR400
    ├─ EGR400-A
    │    ├─ 2026-03-10
    │    └─ 2026-03-12
    └─ EGR400-B
         └─ 2026-03-10
  ```
- Click any date to load the full attendance record for that session
- Shows name, student ID, status, and check-in timestamp per student
- Override buttons allow retroactive corrections that save immediately to disk

### Activity Feed
- Live feed in Attendance View shows every serial line from the ESP32, every card match, every override, and every warning
- Useful for confirming the reader is working without opening a terminal

### Session Logging
- Every card tap is written to a background session log: UID, issue number, student ID, matched name, status, and timestamp
- Completely separate from attendance CSV files — a raw audit trail of every tap event
- Status codes: `PRESENT`, `ABSENT`, `WRONG_SECTION`, `DUPLICATE`

### Reader Status
- Animated status dot always visible in the bottom-right corner regardless of active tab
- Green pulse animation when connected, red when disconnected
- Automatically attempts reconnection if the USB connection drops

### Settings
- Serial port dropdown with live device scan
- Auto-connect on launch toggle
- Configurable paths for session logs and class section CSVs
- All settings persisted across sessions in `tapin_settings.json`

---

## Hardware

| Component | Details |
|---|---|
| Microcontroller | ESP32-S3 DevKitC-1 (Espressif) |
| NFC Reader | Elechouse PN532 NFC/RFID Module v3 |
| Card Type | MIFARE Classic 1K (ISO 14443A) |
| Interface | SPI (software bit-bang via Adafruit PN532 library) |
| Host Connection | USB via ESP32 UART bridge |

### Card Data Format

TapIn authenticates a designated data block on each MIFARE Classic 1K card using a shared sector Key A configured in the firmware. The ASCII content of the block encodes:

```
IISSSSSS
```

| Field | Length | Description |
|---|---|---|
| `II` | 2 digits | Card issue number |
| `SSSSSS` | 6 digits | Student ID |

Example — student ID `999999`, issue number `01`:
```
Block XX (ASCII): 01000999999
```

The UID, issue number, and student ID are all captured and written to the session log on every tap.

---

## Data Storage

All data is stored locally. TapIn creates the following folder structure on first launch:

```
TapIn/
├── class_sections/           # Roster CSV files
│   ├── EGR400_A.csv
│   └── EGR300_B.csv
├── attendance_logs/          # Dated attendance records per session
│   └── EGR400/
│       └── EGR400-A/
│           └── EGR400_A_2026-03-10.csv
├── session_logs/             # Raw tap audit logs
│   └── session_2026-03-10_09-00-00.log
└── tapin_settings.json       # Application settings
```

---

## Security Note

Due to the nature of this program and its interaction with sensitive, institution-specific student credential data, all card data structures, storage details, and sector key information have been intentionally redacted from the publicly released source code and shall not be disclosed, distributed, or otherwise made publicly accessible under any circumstances.

It is in my best personal interest to prevent this sensitive data from being released publicly and to remain in good standing with the university while abiding by all student conduct guidelines. The public compiled .exe app file available in this repository allows a CBU student to build and test this entire platform using their own CBU ID card and contains all relevant parameters in order to allow for a full working build of this app without the need for private external keys or information to be obtained. This will remain exclusive to the obfuscated and precompiled program file only. 

If you are interested in creating your own GUI, or modifying the firmware code, I absolutely encourage you to do so, and please contact me and show me your work and improvements, as I would love to see someone else interested in RFID applications! But, I cannot and will not assist in obtaining access to secure credentials, violating any rule or guideline in the CBU student handbook, or harvesting and/or cloning student ID credentials without proper authorized permission from CBU staff or faculty. TapIn was developed in full compliance with all applicable California Baptist University guidelines, policies, and institutional standards, and no aspect of the project constitutes a violation of, or is otherwise inconsistent with, any provision set forth in the California Baptist University handbook.



## Important Compatibility Note

TapIn is designed specifically for the MIFARE Classic 1K card system and is configured around a card data storage format used in the CBU environment. While the underlying approach can be adapted to support other card types and formats, doing so would require modifications to both the ESP32 firmware and the way the GUI processes incoming data.

These adaptations are outside the scope of this project and are not covered in this repository. Supporting alternative card systems would require substantial changes to the TapIn architecture, including how card data is structured, read, and interpreted. Although this is absolutely feasible, it is not relevant to the intended use of this application.

## License

MIT License — see `LICENSE` for details.

