/*
 * Smart Home Voice Control — Arduino firmware
 *
 * Pin map (matches team breadboard schematic):
 *   RED_LED   D11  — password unlock indicator
 *   GREEN_LED D12  — music indicator
 *   WHITE_LED D10  — light indicator
 *   BUZZER    D13
 *   TMP36     A0
 *
 * 2-LED breadboard fallback (no white LED wired):
 *   Leave WHITE_LED on D10 unwired — LIGHT_ON/OFF become no-ops visually.
 *   Optional remapping if you only have red+green: put light on GREEN and
 *   use the buzzer alone for music cues (edit constants below).
 *
 * Serial protocol (9600 baud, newline-terminated):
 *   PASSWORD_OK | PASSWORD_FAIL
 *   LIGHT_ON | LIGHT_OFF
 *   MUSIC_ON | MUSIC_OFF
 *   SEND_TEMP  → replies "Temperature: <float> C"
 */

const int TEMP_PIN = A0;
const int BUZZER = 13;
const int RED_LED = 11;
const int GREEN_LED = 12;
const int WHITE_LED = 10;

bool passwordOk = false;

void setup() {
  Serial.begin(9600);
  pinMode(BUZZER, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(WHITE_LED, OUTPUT);
  pinMode(TEMP_PIN, INPUT);

  allOff();
}

void loop() {
  if (Serial.available() <= 0) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command == "PASSWORD_OK") {
    handlePasswordOk();
  } else if (command == "PASSWORD_FAIL") {
    handlePasswordFail();
  } else if (passwordOk) {
    if (command == "LIGHT_ON") {
      digitalWrite(WHITE_LED, HIGH);
    } else if (command == "LIGHT_OFF") {
      digitalWrite(WHITE_LED, LOW);
    } else if (command == "MUSIC_ON") {
      digitalWrite(GREEN_LED, HIGH);
      tone(BUZZER, 880, 200);
    } else if (command == "MUSIC_OFF") {
      digitalWrite(GREEN_LED, LOW);
      noTone(BUZZER);
    } else if (command == "SEND_TEMP") {
      Serial.print("Temperature: ");
      Serial.print(readTemperatureC());
      Serial.println(" C");
    } else {
      Serial.println("Unknown command");
    }
  } else {
    Serial.println("Locked: send PASSWORD_OK first");
  }
}

void handlePasswordOk() {
  passwordOk = true;
  digitalWrite(RED_LED, HIGH);
  // Short confirmation beeps (non-blocking pattern kept short to avoid stalling USB)
  for (int i = 0; i < 3; i++) {
    tone(BUZZER, 1000, 150);
    delay(250);
  }
  noTone(BUZZER);
}

void handlePasswordFail() {
  passwordOk = false;
  allOff();
  tone(BUZZER, 400, 400);
  delay(450);
  noTone(BUZZER);
}

void allOff() {
  digitalWrite(RED_LED, LOW);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(WHITE_LED, LOW);
  noTone(BUZZER);
}

// TMP36: 10 mV/°C with 500 mV offset at 0°C
float readTemperatureC() {
  int reading = analogRead(TEMP_PIN);
  float volts = reading * (5.0 / 1023.0);
  return (volts - 0.5) * 100.0;
}
