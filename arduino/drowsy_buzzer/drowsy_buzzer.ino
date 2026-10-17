// Drowsy Driver Alert - Arduino Uno
// Receives 'S' (sleepy) or 'A' (awake) from Python over USB serial, 9600 baud.
// Wiring: Buzzer (+) -> pin 8, Buzzer (-) -> GND. LED = built-in pin 13.

const int BUZZER_PIN = 8;
const int LED_PIN = 13;

const unsigned long BEEP_ON_MS = 300;
const unsigned long BEEP_OFF_MS = 200;
const unsigned long LINK_TIMEOUT_MS = 2000; // no data for 2 s -> alarm off

bool sleepy = false;
bool outputOn = false;
unsigned long lastToggle = 0;
unsigned long lastRx = 0;

void setOutput(bool on) {
  outputOn = on;
  digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
  digitalWrite(LED_PIN, on ? HIGH : LOW);
}

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);

  setOutput(true); // power-up self-test beep
  delay(200);
  setOutput(false);
  lastRx = millis();
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == 'S') { sleepy = true; lastRx = millis(); }
    if (c == 'A') { sleepy = false; lastRx = millis(); }
  }

  if (millis() - lastRx > LINK_TIMEOUT_MS) sleepy = false; // failsafe

  if (sleepy) {
    unsigned long now = millis();
    if (now - lastToggle >= (outputOn ? BEEP_ON_MS : BEEP_OFF_MS)) {
      setOutput(!outputOn);
      lastToggle = now;
    }
  } else if (outputOn) {
    setOutput(false);
  }
}