int reading ;
float volt ; 
float Celsieus ; 
bool pass_corr = false ;

const int temp_pin = A0 ; 
const int BUZZER = 11 ; 
const int GREEN_LED = 13 ; 
const int WHITE_LED = 12 ; 


void setup() {

Serial.begin(9600);
pinMode(BUZZER , OUTPUT);
pinMode(GREEN_LED , OUTPUT);
pinMode(WHITE_LED , OUTPUT);
pinMode(temp_pin, INPUT);

}

void loop() {

if (Serial.available() > 0) {
  String command  = Serial.readStringUntil('\n') ; 
  command.trim();

  if (command == "PASSWORD_OK" ) { 
    digitalWrite(BUZZER , HIGH) ; 
    delay(1000);
    digitalWrite(BUZZER , LOW) ; 
    delay(500);
    digitalWrite(BUZZER , HIGH) ; 
    delay(1000);
    digitalWrite(BUZZER , LOW) ; 
    delay(500);
    digitalWrite(BUZZER , HIGH) ; 
    delay(1000);
    digitalWrite(BUZZER , LOW) ; 
    pass_corr = true; } 

  else if (command == "PASSWORD_FAIL") {  
      digitalWrite(BUZZER, LOW); 
      pass_corr = false; 
  }  

  else if (pass_corr) {
     
      if      (command == "LIGHT_ON" )       digitalWrite(WHITE_LED , HIGH); 
     
      else if (command == "LIGHT_OFF")       digitalWrite(WHITE_LED , LOW);
     
      else if (command == "MUSIC_ON" )       digitalWrite(GREEN_LED , HIGH);
     
      else if (command == "MUSIC_OFF")       digitalWrite(GREEN_LED , LOW);
     
      else if (command == "SEND_TEMP")  {
        float temp = temprature();
        Serial.print("Temperature: ");
        Serial.print(temp);
        Serial.println(" C");
        
      }
     
      else Serial.print("Not a command !!");

}
}
}

float temprature() {
reading = analogRead(temp_pin);
volt = reading * (5.0 / 1024.0);
Celsieus =  volt * 100.0;
return Celsieus ;
}



