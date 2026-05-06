#include <WiFi.h>
#include <ESP_Mail_Client.h>
#include <LiquidCrystal_I2C.h>
#include "ThingSpeak.h"

// ===============================
// LCD SETUP
// ===============================
LiquidCrystal_I2C LCD(0x27, 20, 4);

// ===============================
// WIFI DETAILS
// ===============================
const char* ssid = "Wokwi-GUEST";
const char* pass = "";

// ===============================
// THINGSPEAK DETAILS
// ===============================
WiFiClient client;
unsigned long channelNum = 2382396;
const char *API_Key = "UXAI8XW9H2TCNWPM";

// ===============================
// EMAIL DETAILS
// ===============================
#define SMTP_HOST "smtp.gmail.com"
#define SMTP_PORT 465

#define AUTHOR_EMAIL "b.vivek.b001@gmail.com"
#define AUTHOR_PASSWORD "YOUR_APP_PASSWORD"

#define RECIPIENT_EMAIL "b.vivek.b001@gmail.com"

SMTPSession smtp;
ESP_Mail_Session session;
SMTP_Message message;

// ===============================
// PINS
// ===============================
int sensorPin1 = 34;
int sensorPin2 = 35;
int buzzerPin  = 2;

// ===============================
// VARIABLES
// ===============================
int timer1 = 0;
int timer2 = 0;

float timeDuration = 0;
float distance = 5.0;       // meters
float vehicleSpeed = 0;

int flagStart = 0;
int flagEnd = 0;
int carCount = 0;

// ===============================
// EMAIL FUNCTION
// ===============================
void sendEmailAlert(float speed) {

  message.sender.name = "ESP32 Speed Monitor";
  message.sender.email = AUTHOR_EMAIL;
  message.subject = "Overspeed Alert!";
  message.addRecipient("User", RECIPIENT_EMAIL);

  String textMsg = "Warning!\n";
  textMsg += "Vehicle crossed speed limit.\n";
  textMsg += "Current Speed: ";
  textMsg += String(speed, 1);
  textMsg += " Km/h\n";
  textMsg += "Its Over Speed!";

  message.text.content = textMsg.c_str();

  if (MailClient.sendMail(&smtp, &message)) {
    Serial.println("Email Sent Successfully");
  } else {
    Serial.println("Email Failed");
  }

  message.clearRecipients();
}

// ===============================
// SETUP
// ===============================
void setup() {

  Serial.begin(115200);

  pinMode(sensorPin1, INPUT);
  pinMode(sensorPin2, INPUT);
  pinMode(buzzerPin, OUTPUT);

  LCD.init();
  LCD.backlight();

  LCD.setCursor(0,0);
  LCD.print("Speed Detector");

  // WIFI CONNECT
  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected");

  LCD.clear();
  LCD.setCursor(0,0);
  LCD.print("WiFi Connected");

  // THINGSPEAK
  ThingSpeak.begin(client);

  // EMAIL SESSION
  session.server.host_name = SMTP_HOST;
  session.server.port = SMTP_PORT;

  session.login.email = AUTHOR_EMAIL;
  session.login.password = AUTHOR_PASSWORD;

  session.time.ntp_server = "pool.ntp.org,time.nist.gov";

  delay(2000);
  LCD.clear();
}

// ===============================
// LOOP
// ===============================
void loop() {

  // SENSOR 1 DETECT
  if (digitalRead(sensorPin1) == LOW && flagStart == 0) {
    timer1 = millis();
    flagStart = 1;
  }

  // SENSOR 2 DETECT
  if (digitalRead(sensorPin2) == LOW && flagStart == 1 && flagEnd == 0) {
    timer2 = millis();
    flagEnd = 1;
  }

  // BOTH SENSOR DETECTED
  if (flagStart == 1 && flagEnd == 1) {

    timeDuration = abs(timer2 - timer1) / 1000.0;

    vehicleSpeed = (distance / timeDuration) * 3.6;

    carCount++;

    Serial.print("Speed: ");
    Serial.print(vehicleSpeed);
    Serial.println(" Km/h");

    LCD.clear();

    LCD.setCursor(0,0);
    LCD.print("Car Count:");
    LCD.print(carCount);

    LCD.setCursor(0,1);
    LCD.print("Speed:");
    LCD.print(vehicleSpeed,1);
    LCD.print(" Km/h");

    // OVER SPEED
    if (vehicleSpeed > 60) {

      LCD.setCursor(0,2);
      LCD.print("OVER SPEED!");

      digitalWrite(buzzerPin, HIGH);

      sendEmailAlert(vehicleSpeed);

      delay(2000);

      digitalWrite(buzzerPin, LOW);

    } else {

      LCD.setCursor(0,2);
      LCD.print("Normal Speed");
    }

    // SEND TO THINGSPEAK
    ThingSpeak.setField(1, vehicleSpeed);

    int status = ThingSpeak.writeFields(channelNum, API_Key);

    if (status == 200) {
      Serial.println("ThingSpeak Updated");
    } else {
      Serial.println("ThingSpeak Failed");
    }

    delay(3000);

    // RESET
    flagStart = 0;
    flagEnd = 0;
    vehicleSpeed = 0;

    LCD.clear();
  }

  // WAITING MESSAGE
  if (flagStart == 0 && flagEnd == 0) {
    LCD.setCursor(0,3);
    LCD.print("Waiting Vehicle...");
  }
}
