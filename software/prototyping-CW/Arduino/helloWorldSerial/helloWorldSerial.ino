void setup() {
  Serial.begin(9600); // Baudrate

}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.write("Hello world!\n");
  delay(1000);
}
