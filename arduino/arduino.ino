#include <SPI.h>
#include <WiFiNINA.h>
#include <ArduinoLowPower.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <StreamUtils.h>

#include "arduino_secrets.h" 

char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
char bearer_token[] = BEARER_TOKEN;

int status = WL_IDLE_STATUS;
WiFiSSLClient client;
//StaticJsonDocument<200> filter;
// Function: https://us-east1-baserate-332800.cloudfunctions.net/gull-cannon/actions

void setup() {
//  filter["data"] = true;

  //Initialize serial and wait for port to open:
  Serial.begin(9600);
  // Note that Serial is lost when we go to low power sleep; waiting for it to come back breaks everything. :(
//  while (!Serial) {
//    ; // wait for serial port to connect. Needed for native USB port only
//  }

  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // don't continue
    while (true);
  }

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("Please upgrade the firmware");
  }
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(13, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  digitalWrite(13, LOW);
}

void loop() {
  int sleepTime = 5 * 60 * 1000;
  // attempt to connect to WiFi network:
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(ssid, pass);
    // Example code had a delay call here, but the above call seems to block anyway.
  }
  printWiFiStatus();

  Serial.println("\nStarting connection to server...");
  HttpClient http = HttpClient(client, "us-east1-baserate-332800.cloudfunctions.net", 443);
  http.beginRequest();
  http.get("/gull-cannon/actions");
  http.sendHeader("Authorization", bearer_token);
  http.endRequest();
  int statusCode = http.responseStatusCode();
  if (statusCode > 299) {
    Serial.println("unexpected status code: " + String(statusCode));
  }
  StaticJsonDocument<512> response;
  // DeserializationError err = deserializeJson(response, http.responseBody(), DeserializationOption::Filter(filter));
  DeserializationError err = deserializeJson(response, http.responseBody());

  Serial.println("Got response:");
  serializeJson(response, Serial);
  Serial.println("");

  if (err == DeserializationError::Ok) {
    Serial.println("Successfully deserialized response.");
    Serial.println("Next callback in: " + response["delay"].as<String>());
    int newSleepTime = response["delay"].as<int>();
    if (newSleepTime != 0) {
      sleepTime = newSleepTime;
    }
    int n_actions = response["actions"].size();
    if (n_actions > 0) {
      Serial.println("Found " + String(n_actions) + " actions.");
      // We only do the first one, but mark it completed immediately.
      String id = response["actions"][0]["id"].as<String>();
      String action = response["actions"][0]["action"].as<String>();
      int fireDuration = response["actions"][0]["duration"].as<int>();
      String completed_message = "{\"id\":\"" + id + "\",\"completed\":true}";
      bool success = fireCannon(fireDuration);
      Serial.println("Marking message as done with message: " + completed_message);
      http.beginRequest();
      http.put("/gull-cannon/actions/" + String(id));
      http.sendHeader("Authorization", bearer_token);
      http.sendHeader("Content-Type", "application/json");
      http.sendHeader("Content-Length", completed_message.length());
      http.beginBody();
      http.print(completed_message);
      http.endRequest();

      int statusCode = http.responseStatusCode();
      if (statusCode > 299) {
        Serial.println("unexpected status code: " + String(statusCode));
      }              
    } else {
      Serial.println("No actions found.");
    }
  } else {
    Serial.println("Unable to parse response.");
    Serial.println(err.c_str());
  }
  response.clear();
  http.stop();

  // Turn off wifi module
  Serial.println("Going to sleep for " + String(sleepTime) + " millis.");
  WiFi.end();
  status = WL_IDLE_STATUS;
  LowPower.sleep(sleepTime);
//  delay(sleepTime);  // During debugging, use delay to avoid resetting serial by going into low power mode.
}

bool fireCannon(int duration) {
  Serial.println("Firing cannon for " + String(duration) + " millis.");
  digitalWrite(13, HIGH);
  digitalWrite(LED_BUILTIN, HIGH);
  int startMillis = millis();
  while (millis() < startMillis + duration) {
    delay(500);
  }
  digitalWrite(13, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  return true;
}


void printWiFiStatus() {
//  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}
