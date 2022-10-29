#include <SPI.h>
#include <SD.h>
#include <EEPROM.h>

#define SDPIN 10
SdFile root;
Sd2Card card;
SdVolume volume;

File myFile;
char filename[] = "hello.txt";


void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.setTimeout(3000);
  Serial.print("Initializing SD card...\n");

    if (!SD.begin(SDPIN)) {
    Serial.println(F("SD initialization failed!\n"));
    Serial.println(F("Is there an SD card inserted?"));
    return;
  }
  
  Serial.println("initialization done.");
  myFile = SD.open(filename, FILE_WRITE); 

  if (myFile) {
    Serial.print("Writing to file...");
    myFile.println("testing 1, 2, 3.");
    // close the file:
    myFile.flush();
    Serial.println("done.");
  } else {
    // if the file didn't open, print an error:
    Serial.println("error opening file");
  }
}

void loop() {
//exit(0);
}
