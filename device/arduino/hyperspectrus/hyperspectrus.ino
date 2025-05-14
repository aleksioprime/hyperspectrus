#include <Adafruit_NeoPixel.h>

#define PIN 5
#define NUM_PIXELS 16

Adafruit_NeoPixel strip(NUM_PIXELS, PIN, NEO_GRB + NEO_KHZ800);
String input = "";

void setup() {
  Serial.begin(9600);
  strip.begin();
  strip.show();
}

void loop() {
  if (Serial.available()) {
    input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("SET")) {
      int r, g, b;
      sscanf(input.c_str(), "SET %d,%d,%d", &r, &g, &b);
      for (int i = 0; i < NUM_PIXELS; i++) {
        strip.setPixelColor(i, strip.Color(r, g, b));
      }
      strip.show();
      delay(10);  // <--- буфер перед подтверждением
      Serial.println("OK");
    }

    else if (input == "PHOTO_DONE") {
      for (int i = 0; i < NUM_PIXELS; i++) {
        strip.setPixelColor(i, 0);
      }
      strip.show();
      Serial.println("OFF_DONE");
    }
  }
}
