#include <f401reMap.h>
#include <Wire.h>
#include <SharpIR.h>

#define ir1 A0
#define ir2 A1
#define model 1080

SharpIR SharpIR1(ir1, model);
SharpIR SharpIR2(ir2, model);

struct pin{
    int magnet; //magnet sensori pin
    int solenoid; //solenoidi juhtimis pin
};

struct kapp{
    int kapi_number; // mitmes uks on

    pin pinnid; //sensorite ja solenoidi pinnid
    int magnet_sensor; //0 kinni / 1 lahti

                    // võib ka siia veel inte lisada mis salestavad kapi mõõdud
    int ir_sensor; //kas kapis on midagi: 0 ei ole/ 1 on
    int uks; //siin vaatame mis seisunids uks tegelt peaks olema, : 0 kinni / 1 lahti
                                // ehk kui uks peaks lahti olema ja magnet näitab et on kinni siis teeme ukse lahti
    int error;
};

const int kappide_arv = 2;
struct kapp kapid[kappide_arv] = {{1,{8,9},0,0,0},    //kapi structide list ning muutujate algväärtustamine
                        {2,{11,12},0,0,0}};
int mis_kapp=0;

void setup()
{
  
  Serial.println("start");
  for(int i = 0; i < kappide_arv; i++){ //kappide_arv asemel oli 2
    pinMode(kapid[i].pinnid.solenoid, OUTPUT);
    pinMode(kapid[i].pinnid.magnet, INPUT_PULLUP);
  }

  Wire.begin(10);                 // join i2c bus with address #10
  Wire.onReceive(receiveData);    // register Data
  Wire.onRequest(sendData);       // Set up the function to call when master requests data
  Serial.begin(115200);           // start serial for output
}

int ava_uks(int i){
  kapid[i].uks = 0;   //muudame kapi ukse 'intended' oleku suletuks, st kapi uks PEAKS olema kinni

  kapid[i].magnet_sensor = 0;     //digitalRead(kapid[i].pinnid.magnet); //==========================UNCOMMENT, kui teine magnet lyliti on lisatud

  if(kapid[i].magnet_sensor == 0){
    Serial.println("opening solenoid");
    digitalWrite(kapid[i].pinnid.solenoid, HIGH); //kui uks peaks lahti olema aga ei ole siis tee solenoid lahti
    // MAGNET/DOOR OPEN
  }
  delay(1000);//oota Nats et kapp avaneks, hetkel 1 sekund
  kapid[i].magnet_sensor = 1;//digitalRead(kapid[i].pinnid.magnet); //==========================UNCOMMENT, kui teine magnet lyliti on lisatud
  digitalWrite(kapid[i].pinnid.solenoid, LOW);

  if(kapid[i].magnet_sensor == 0){
    //TODO: kui endiseltmagnet et uks kinni siis, proovi uuesti ja kui ikka siis lülita solenoid välja ja saada raspile info et error 1
    //recursive perhaps, extra sisend, ava_uks(int i, bool uuesti)
    return 1;   //kapp ei avane
  }
  delay(3000);  //nüüd peaks ootama kuni uks sulgub
  kapid[i].magnet_sensor = 0;   //digitalRead(kapid[i].pinnid.magnet); //==========================UNCOMMENT, kui teine magnet lyliti on lisatud
  if(kapid[i].magnet_sensor == 1){
    //uks ikka lahti ja raspile info
    return 2;   //kapp ei sulgu
  }
  return 0;   //kapp avanes ja sulgus aegselt
}

void loop()
{
    int dis1 = SharpIR1.distance(); // distance from IR sensor 1
    int dis2 = SharpIR2.distance(); // distance from IR sensor 2


    if (dis1 >= 7 && dis1 <= 20) { //sellega peab veel nussima
        kapid[0].ir_sensor = 1; // IR sensor 1 detects something
    } else {
        kapid[0].ir_sensor = 0; // IR sensor 1 doesn't detect anything
    }

    if (dis2 >= 7 && dis2 <= 20) { //sellega peab veel nussima
        kapid[1].ir_sensor = 1; // IR sensor 2 detects something
    } else {
        kapid[1].ir_sensor = 0; // IR sensor 2 doesn't detect anything
    }

  if(kapid[mis_kapp - 1].uks == 1){   //kontrollime konstantselt kas yhegi kapi uks PEAKS lahti olema
    kapid[mis_kapp - 1].error = ava_uks(mis_kapp-1);
  }

}
//sendData(requestData) saadab masteri soovil talle infot
void sendData() {
    // Combine error states and IR sensor states for both boxes into a single integer
    int combinedData = (kapid[0].error * 1000 + kapid[0].ir_sensor * 100) + (kapid[1].error * 10 + kapid[1].ir_sensor);
    
    // Send the combined data to the master
    Wire.write(combinedData);
    
    Serial.print("Combined data for Box 1 and Box 2: ");


}
// receiveData votab masterilt infot vastu
void receiveData(int howMany)
{
  int x;
  int i = 0;
  while(0 < Wire.available()) // loop through all but the last
  {
    // receive byte
    x = Wire.read();
    Serial.println(x,HEX);
  }

  mis_kapp = x;
    if(mis_kapp <= kappide_arv && mis_kapp > 0){
      Serial.print("Avan kapi ");
      Serial.println(mis_kapp);
      kapid[mis_kapp - 1].uks = 1;    //anname kindlale kapile signaali et see PEAKS lahti minema
    }
}
