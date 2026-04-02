/*
 * TapIn — NFC Attendance Reader Firmware
 * ESP32-S3 + Elechouse PN532 (SPI mode)
 *
 * Reads a designated data block from MIFARE Classic 1K cards,
 * authenticates using a sector Key A, and outputs card data
 * over serial at 115200 baud for consumption by the TapIn desktop app.
 *
 * CONFIGURATION REQUIRED:
 *   - Set TARGET_BLOCK to the block number containing your card data
 *   - Set AUTH_KEY to the 6-byte Key A for that block's sector
 *     (these values are specific to your institution's card system)
 */

#include <SPI.h>
#include <Adafruit_PN532.h>

// SPI pin definitions (ESP32-S3 DevKitC-1)
#define PN532_SCK   12
#define PN532_MISO  13
#define PN532_MOSI  11
#define PN532_SS    10

Adafruit_PN532 nfc(PN532_SCK, PN532_MISO, PN532_MOSI, PN532_SS);

// ─────────────────────────────────────────────────────────────────
//  CONFIGURE THESE VALUES FOR YOUR INSTITUTION'S CARD SYSTEM
// ─────────────────────────────────────────────────────────────────

// The block number to read from each card.
// Must be a data block (not a sector trailer) in the authenticated sector.
// Replace XX with your target block number.
#define TARGET_BLOCK  XX  // <-- set your block number here

// The 6-byte Key A for the sector containing TARGET_BLOCK.
// Replace each 0x00 with your institution's actual key bytes.
// Do NOT commit real key bytes to a public repository.
// Enter HEX values from sector key for each "00" value after the 0x in each string below
uint8_t authKey[6] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };  // <-- set your Key A here

// ─────────────────────────────────────────────────────────────────

void setup() {
  USBSerial.begin(115200);  // force USB CDC serial on ESP32-S3
  Serial.begin(115200);
  delay(1000);

  Serial.println("=== Attendance Reader Init ===");

  pinMode(PN532_SS, OUTPUT);
  digitalWrite(PN532_SS, HIGH);
  delay(100);
  digitalWrite(PN532_SS, LOW);
  delay(100);

  nfc.begin();
  delay(500);

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("FAIL: PN532 not found. Check wiring.");
    while (1) delay(100);
  }

  Serial.print("Found PN5");
  Serial.println((versiondata >> 24) & 0xFF, HEX);
  nfc.SAMConfig();
  Serial.println("Ready — tap a card...");
}

void loop() {
  uint8_t uid[7]     = {0};
  uint8_t uidLength  = 0;

  bool success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 500);
  if (!success) return;

  // Print UID
  Serial.print("Card detected. UID: ");
  for (uint8_t i = 0; i < uidLength; i++) {
    if (uid[i] < 0x10) Serial.print("0");
    Serial.print(uid[i], HEX);
    Serial.print(" ");
  }
  Serial.println();

  // Authenticate the target sector using Key A
  uint8_t authSuccess = nfc.mifareclassic_AuthenticateBlock(
    uid, uidLength,
    TARGET_BLOCK,
    0,           // 0 = Key A
    authKey
  );

  if (!authSuccess) {
    Serial.println("AUTH FAIL: Wrong key or block. Check configuration.");
    delay(1000);
    return;
  }

  Serial.println("Auth OK.");

  // Read the target block (16 bytes)
  uint8_t blockData[16] = {0};
  uint8_t readSuccess   = nfc.mifareclassic_ReadDataBlock(TARGET_BLOCK, blockData);

  if (!readSuccess) {
    Serial.println("READ FAIL: Authenticated but could not read block.");
    delay(1000);
    return;
  }

  // Print raw hex
  Serial.print("Block ");
  Serial.print(TARGET_BLOCK);
  Serial.print(" (hex): ");
  for (uint8_t i = 0; i < 16; i++) {
    if (blockData[i] < 0x10) Serial.print("0");
    Serial.print(blockData[i], HEX);
    Serial.print(" ");
  }
  Serial.println();

  // Convert to ASCII — stop at null byte
  Serial.print("Block ");
  Serial.print(TARGET_BLOCK);
  Serial.print(" (ASCII): ");
  for (uint8_t i = 0; i < 16; i++) {
    if (blockData[i] >= 0x20 && blockData[i] <= 0x7E) {
      Serial.print((char)blockData[i]);
    } else if (blockData[i] == 0x00) {
      break;
    } else {
      Serial.print('.');
    }
  }
  Serial.println();

  delay(1000); // debounce before next read
}
