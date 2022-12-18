
/*
  UPDATED (17 December 2022): Removed OLED code and only records sipm voltage and muon count
  CosmicWatch Desktop Muon Detector Arduino Code

  Edited by: ISP Software Team

  Requirements: Sketch->Include->Manage Libraries:
  SPI, EEPROM, SD, and Wire are probably already installed.
  1. Adafruit SSD1306     -- by Adafruit Version 1.0.1
  2. Adafruit GFX Library -- by Adafruit Version 1.0.2
  3. TimerOne             -- by Jesse Tane et al. Version 1.1.0
*/

#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <TimerOne.h>
#include <Wire.h>
#include <SPI.h>
#include <EEPROM.h>

const int SIGNAL_THRESHOLD      = 50;    // Min threshold to trigger on. See calibration.pdf for conversion to mV.
const int RESET_THRESHOLD       = 25;    

const int LED_BRIGHTNESS        = 255;    // Brightness of the LED [0,255]

const long double cal[] = {-9.085681659276021e-27, 4.6790804314609205e-23, -1.0317125207013292e-19,
  1.2741066484319192e-16, -9.684460759517656e-14, 4.6937937442284284e-11, -1.4553498837275352e-08,
   2.8216624998078298e-06, -0.000323032620672037, 0.019538631135788468, -0.3774384056850066, 12.324891083404246};
   
const int cal_max = 1023;

//INTERUPT SETUP
#define TIMER_INTERVAL 1000000          // Every 1,000,000 us the timer will update the OLED readout


//initialize variables
unsigned long time_measurement                = 0L;      // Time stamp
unsigned long interrupt_timer                 = 0L;      // Time stamp
int start_time                                = 0L;      // Reference time for all the time measurements
unsigned long waiting_t1                      = 0L;
unsigned long measurement_t1;
unsigned long measurement_t2;

float sipm_voltage                            = 0;
long int count                                = 0L;      // A tally of the number of muon counts observed
float last_sipm_voltage                       = 0;

byte waiting_for_interupt                     = 0;
byte SLAVE;
byte MASTER;
byte keep_pulse                               = 0;


// This function converts the measured ADC value to a SiPM voltage via the calibration array
float get_sipm_voltage(float adc_value)
{
  float voltage = 0;
  for (int i = 0; i < (sizeof(cal)/sizeof(float)); i++) {
    voltage += cal[i] * pow(adc_value,(sizeof(cal)/sizeof(float)-i-1));
    }
    return voltage;
}

void setup() {
  analogReference (EXTERNAL);
  ADCSRA &= ~(bit (ADPS0) | bit (ADPS1) | bit (ADPS2));  // clear prescaler bits
  ADCSRA |= bit (ADPS0) | bit (ADPS1);                   // Set prescaler to 8
  Serial.begin(9600);
                                
  pinMode(3, OUTPUT);
  pinMode(6, INPUT);
  if (digitalRead(6) == HIGH) {
      SLAVE = 1;
      MASTER = 0;
      digitalWrite(3,HIGH);
      delay(1000);}

  else{
      delay(10);
      MASTER = 1;
      SLAVE = 0;
      pinMode(6, OUTPUT);
      digitalWrite(6, HIGH);}

  digitalWrite(3,LOW);
  if (MASTER == 1) {digitalWrite(6, LOW);}
  
  delay(900);

  Serial.println("Setup Finished");
}

void loop()
{
  
  while (1){
    if (analogRead(A0) > SIGNAL_THRESHOLD){ 

      // Make a measurement of the pulse amplitude
      int adc = analogRead(A0);
      
      // If Master, send a signal to the Slave
      if (MASTER == 1) {
          digitalWrite(6, HIGH);
          count++;
          keep_pulse = 1;}

      // Wait for ~8us
      analogRead(A3);
      
      // If Slave, check for signal from Master
      if (SLAVE == 1){
          if (digitalRead(6) == HIGH){
              keep_pulse = 1;
              count++;}}  

      // Wait for ~8us
      analogRead(A3);

      // If Master, stop signalling the Slave
      if (MASTER == 1) {
          digitalWrite(6, LOW);}
      


      measurement_t1 = micros();
      
      if (MASTER == 1) {
          analogWrite(3, LED_BRIGHTNESS);
          sipm_voltage = get_sipm_voltage(adc);
          last_sipm_voltage = sipm_voltage; 
          Serial.println((String)count + " " + sipm_voltage);}
  
      if (SLAVE == 1) {
          if (keep_pulse == 1) {   
              analogWrite(3, LED_BRIGHTNESS);
              sipm_voltage = get_sipm_voltage(adc);
              last_sipm_voltage = sipm_voltage; 
              Serial.println((String)count + " " + sipm_voltage);}}
      
      keep_pulse = 0;
      digitalWrite(3, LOW);
      while(analogRead(A0) > RESET_THRESHOLD){continue;}
    }
  }
}
