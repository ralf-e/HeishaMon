#include "hmx_status.h"
#include "hmx_model.h"
#include "hmx.h"
#if defined(ESP32) && HMX_ENABLED
#include <SPI.h>
#include <Wire.h>
#include <Preferences.h>
#include <Adafruit_GFX.h>
#include <atomic>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>
#include "../../webfunctions.h"
#include "../../decode.h"
#include "../../version.h"
#include "../../commands.h"
#include "hmx_policy.h"
#include "hmx_choice.h"
extern settingsStruct heishamonSettings;
extern HardwareSerial Serial1;
extern QueueHandle_t cmdQueue;
extern volatile bool sending;
extern char actData[], actDataExtra[], actOptData[];
extern dallasDataStruct *actDallasData;
extern int dallasDevicecount;
static_assert(HMX_PAGE_ROWS == 20, "480x320 layout requires 20 rows");
namespace {
SemaphoreHandle_t txMutex = nullptr;
hmx::Policy policy;
std::atomic<bool> passive{true};
bool ioOk = false, modeReady = false, prefsOpen = false, modeMenu = false;
Preferences modePreferences;
hmx::Choice choice;
uint32_t lastPoll = 0, lastTouchPoll = 0, lastTouch = 0;
uint8_t outputs = 0x06; // GP1/2 reset outputs high; GP0 unused
uint32_t rxAt[3] = {0,0,0};
bool received[3] = {false,false,false};
GFXcanvas16 canvas(480,24); // 23 KiB; no full-screen framebuffer
enum View { Overview, All, Extra, Optional, Dallas, Groups, Detail, ModelInfo };
View view = Overview, backView = All, modelBackView = Overview;
int modelBackFirst = 0;
String modelRaw;
hmx::ModelMatch modelMatch={nullptr,0,false};
int first = 0, backFirst = 0, detailIndex = 0, paintRow = 0;
bool repaint = true, touchDown = false, suppressTouch = false, observedRx = false;
uint32_t lastFrame = 0, repeatAt = 0;
int touchButton = -1;
constexpr uint16_t BG=0x0841, FG=0xffff, MUTED=0x9cf3, ACCENT=0x4e9f, WARN=0xfd20;
const int overviewIds[] = {0,44,13,1,6,5,7,46,14,94,36,42,94,37,43,4,10,9,8,26};
const char *overviewNames[] = {"Waermepumpe","Fehler","Haupttimer","Volumenstrom","Vorlauf","Ruecklauf","Vorlauf Soll","Puffer","Aussen","HK1 Status","HK1 Vorlauf Ist","HK1 Vorlauf Soll","HK2 Status","HK2 Vorlauf Ist","HK2 Vorlauf Soll","Warmwasser Status","Warmwasser","Warmwasser Soll","Verdichter","Abtauung"};
// 0=raw topic, 1=WW permission, 2=HK1 permission, 3=HK2 permission, 4=main timer.
const int overviewKinds[] = {0,0,4,0,0,0,0,0,0,2,0,0,3,0,0,1,0,0,0,0};
constexpr int overviewCount = sizeof(overviewIds)/sizeof(overviewIds[0]);
static_assert(overviewCount == sizeof(overviewNames)/sizeof(overviewNames[0]), "Overview labels must match IDs");
bool writeReg(uint8_t reg,uint8_t value) {
  Wire.beginTransmission(HMX_MCP_ADDR); Wire.write(reg); Wire.write(value);
  return Wire.endTransmission()==0;
}
bool readReg(uint8_t address,uint8_t reg,uint8_t *buf,size_t len) {
  Wire.beginTransmission(address); Wire.write(reg);
  if(Wire.endTransmission(false)!=0) return false;
  if(Wire.requestFrom(address,(uint8_t)len)!=(int)len) return false;
  for(size_t i=0;i<len;i++) buf[i]=Wire.read();
  return true;
}
void selectDisplay() {
  SPI.beginTransaction(SPISettings(HMX_SPI_HZ,MSBFIRST,SPI_MODE0));
  digitalWrite(HMX_LCD_CS,LOW);
}
void releaseDisplay() { digitalWrite(HMX_LCD_CS,HIGH); SPI.endTransaction(); }
void cmd(uint8_t c,const uint8_t *d=nullptr,size_t n=0) {
  selectDisplay(); digitalWrite(HMX_LCD_DC,LOW); SPI.transfer(c);
  digitalWrite(HMX_LCD_DC,HIGH);
  for(size_t i=0;i<n;i++) SPI.transfer(d[i]);
  releaseDisplay();
}
void command1(uint8_t c,uint8_t d) {cmd(c,&d,1);}
void drawStrip(int y,const uint16_t *pixels,int height=24) {
  // One 480x4 strip per SPI transaction: Ethernet can run between strips.
  for(int row=0;row<height;row+=4) {
    const int n=min(4,height-row);
    uint8_t x[]={0,0,1,223};
    const uint16_t y0=y+row,y1=y+row+n-1;
    uint8_t yy[]={(uint8_t)(y0>>8),(uint8_t)y0,(uint8_t)(y1>>8),(uint8_t)y1};
    selectDisplay();
    digitalWrite(HMX_LCD_DC,LOW);SPI.transfer(0x2a);
    digitalWrite(HMX_LCD_DC,HIGH);SPI.transferBytes(x,nullptr,4);
    digitalWrite(HMX_LCD_DC,LOW);SPI.transfer(0x2b);
    digitalWrite(HMX_LCD_DC,HIGH);SPI.transferBytes(yy,nullptr,4);
    digitalWrite(HMX_LCD_DC,LOW);SPI.transfer(0x2c);
    digitalWrite(HMX_LCD_DC,HIGH);
    SPI.writePixels((const void *)(pixels+row*480),480*n*2);
    releaseDisplay();
  }
}
String clean(String s) {
  s.replace("°","");s.replace("³","3");s.replace("²","2");
  s.replace("ä","ae");s.replace("ö","oe");s.replace("ü","ue");
  s.replace("Ä","Ae");s.replace("Ö","Oe");s.replace("Ü","Ue");s.replace("ß","ss");
  for(size_t i=0;i<s.length();i++) if((uint8_t)s[i]<32 || (uint8_t)s[i]>126) s.setCharAt(i,'?');
  return s;
}
String fit(String s,int chars) {
  s=clean(s); return (int)s.length()>chars?s.substring(0,chars-1)+"~":s;
}
void text(int x,int y,String s,uint16_t color=FG,int size=2) {
  canvas.setTextSize(size);canvas.setTextColor(color);canvas.setCursor(x,y);canvas.print(s);
}
int countFor(View v) {
  switch(v) {
    case Overview:return overviewCount;
    case All:return NUMBER_OF_TOPICS;
    case Extra:return NUMBER_OF_TOPICS_EXTRA;
    case Optional:return NUMBER_OF_OPT_TOPICS;
    case Groups:return 6;
    case Detail:return 1;
    case ModelInfo:return 1;
    case Dallas:{
      int n=0;if(heishamonSettings.use_1wire && actDallasData)
        for(int i=0;i<dallasDevicecount;i++) if(actDallasData[i].known)n++;
      return n;
    }
  }return 0;
}
uint8_t blockFor(View v) {return v==Extra?1:v==Optional?2:0;}
String ageFor(uint8_t block) {
  if(!received[block])return "keine Daten";
  return String((uint32_t)(millis()-rxAt[block])/1000)+"s";
}
bool stale(uint8_t block) {return !received[block] || uint32_t(millis()-rxAt[block])>HMX_STALE_MS;}
void valueFor(View v,int i,String &name,String &value,String &id) {
  if(v==Dallas) {
    int slot=-1;
    if(actDallasData)for(int j=0;j<dallasDevicecount;j++)if(actDallasData[j].known && i--==0){slot=j;break;}
    if(slot<0){name="Keine Sensoren";value="--";return;}
    auto &s=actDallasData[slot]; name=strcmp(s.alias,"NOT SET")?s.alias:s.address;
    id=s.address;
    value=s.lastgoodtime?String(s.temperature,2)+" C":"keine Daten";
    if(!s.present)value+=" OFFLINE";
    else if(s.lastgoodtime && uint32_t(millis()-s.lastgoodtime)>HMX_STALE_MS)value+=" alt";
    return;
  }
  const int overviewRow=i;
  if(v==Overview) i=overviewIds[i];
  uint8_t b=blockFor(v);
  id=String(i);
  name=b==1?String(xtopics[i]):b==2?String(optTopics[i]):String(topics[i]);
  if(v==Overview) name=overviewNames[overviewRow];
  if(!received[b]){value="keine Daten";return;}
  if(v==Overview && overviewKinds[overviewRow]) {
    const int kind=overviewKinds[overviewRow];
    const int status=kind==4?hmx::timerPermission(getDataValue(actData,13).toInt()):
      hmx::overviewPermission(getDataValue(actData,0).toInt(),getDataValue(actData,4).toInt(),
        getDataValue(actData,94).toInt(),kind);
    value=status<0?"Unbekannt":status==0?"Aus":kind==4?"Ein (1)":"Freigegeben";
    id=kind==4?"TOP13 Haupttimer":kind==1?"TOP4 + TOP0 / WW-Freigabe":
      kind==2?"TOP94 + TOP4 + TOP0 / HK1":"TOP94 + TOP4 + TOP0 / HK2";
    return;
  }
  value=b==1?getDataValueExtra(actDataExtra,i):b==2?getOptDataValue(actOptData,i):getDataValue(actData,i);
  const char **desc=b==1?xtopicDescription[i]:b==2?opttopicDescription[i]:topicDescription[i];
  const int enums=atoi(desc[0]);
  if(enums==0) {
    if(strcmp(desc[1],"C")==0 || strstr(desc[1],"Celsius")) value+=" C";
    else if(strlen(desc[1])<12 && strcmp(desc[1],"Model")!=0)value+=" "+String(desc[1]);
  } else {
    int k=value.toInt();if(k>=0 && k<enums)value=String(desc[k+1])+" ("+value+")";
  }
  if(b==0 && (i==15||i==16||i==38||i==39||i==40||i==41) &&
     received[0] && (uint8_t)actData[0xc7]>=3)value="XTOP nutzen";
}
String detailAge(View v,int index) {
  if(v!=Dallas)return ageFor(blockFor(v));
  if(actDallasData)for(int j=0;j<dallasDevicecount;j++)if(actDallasData[j].known && index--==0){
    auto &s=actDallasData[j];return s.lastgoodtime?String(uint32_t(millis()-s.lastgoodtime)/1000)+"s":"keine Daten";
  }
  return "keine Daten";
}
void refreshModel() {
  if(!received[0]){modelRaw="";modelMatch={nullptr,0,false};return;}
  String raw=getDataValue(actData,92);
  if(raw!=modelRaw){modelRaw=raw;modelMatch=hmx::lookupModel(modelRaw.c_str());}
}
String modelButtonText() {
  return received[0]?String(hmx::modelShortName(modelMatch)):String("Modell: keine Daten");
}
String modelInfoLine(int row) {
  const bool known=received[0] && modelMatch.valid && modelMatch.count==1;
  const hmx::ModelRecord *m=known?modelMatch.record:nullptr;
  if(row==0)return "Geraeteinfo / TOP92";
  if(row==1)return String("Status: ")+(!received[0]?"keine Daten":
    !modelMatch.valid?"ungueltige Kennung":modelMatch.count==0?"unbekannt":
    modelMatch.count==1?"eindeutig zugeordnet":"mehrdeutig ("+String(modelMatch.count)+")");
  if(row>=2 && row<=7) {
    const char *labels[]={"Innen: ","Aussen: ","Kit: ","Leistung: ","Phasen: ","Typ: "};
    if(!known)return row==2?String("Keine sichere Modellzuordnung."):String("");
    const char *values[]={m->idu,m->odu,m->kit,m->power,m->phase,m->type};
    return String(labels[row-2])+values[row-2]+(row==5?" kW":"");
  }
  if(row==9)return "Kennung: "+(received[0]?modelRaw:String("keine Daten"));
  if(row==11)return "Quelle: HeishaMon / HeatPumpType.md";
  if(row==12)return "Tabelle: "+String(hmx::modelCount)+" Eintraege";
  if(row==13)return "Modelltabelle: "+String(hmx::modelTableCommit).substring(0,12);
  if(row==14)return "Firmwarebasis: "+String(HMX_UPSTREAM_COMMIT).substring(0,12);
  if(row==15)return "Empfang: "+ageFor(0)+(stale(0)?" / ALT":"");
  if(row==16)return String("HeishaMon: ")+HEISHAMON_VERSION;
  if(row==17)return String("Erweiterung: HMX ")+HMX_VERSION;
  if(row==18)return "Community-Zuordnung; keine WP-Befehle.";
  return "";
}
void openModelInfo() {
  if(view==ModelInfo)return;
  modelBackView=view;modelBackFirst=first;view=ModelInfo;first=0;
  repaint=true;paintRow=0;
}
const char *title() {
 switch(view){case Overview:return "Uebersicht";case All:return "Alle WP-Topics";
 case Extra:return "Zusatzdaten";case Optional:return "Optional PCB";case Dallas:return "Dallas 1-Wire";
 case Groups:return "Ansichten";case Detail:return "Wertdetails";case ModelInfo:return "Geraeteinfo";}return "";
}
void renderRow(int r) {
  canvas.fillScreen(BG);canvas.setTextWrap(false);
  if(r==0) {
    refreshModel();
    canvas.fillRect(4,0,232,22,0x10c4);canvas.drawRect(4,0,232,22,ACCENT);
    canvas.fillRect(244,0,232,22,0x10c4);canvas.drawRect(244,0,232,22,ACCENT);
    text(12,7,fit(modelButtonText(),34),ACCENT,1);text(220,7,">",ACCENT,1);
    text(260,7,fit(String(hmxModeText()),32),passive.load()?WARN:FG,1);
    text(460,7,">",ACCENT,1);
  } else if(r==1) {
    String line="WP: "+ageFor(0)+"  EXTRA: "+ageFor(1);
    line+="  "+String(ETH.hasIP()?"LAN":WiFi.isConnected()?"WLAN":"OFFLINE");
    if(modeMenu || view!=Overview)line=String(modeMenu?"Betriebsart":title())+" | "+line;
    text(8,0,fit(line,77),stale(0)?WARN:MUTED,1);
    if(!modeMenu && view!=Groups && view!=Detail && view!=ModelInfo) {
      text(8,12,"Nr.",ACCENT,1);
      text(42,12,"Topic",ACCENT,1);
      text(360,12,"Wert / Einheit",ACCENT,1);
    }
  } else if(r==12) {
    const char *buttons[]={modeMenu?"ABBRECHEN":"< ZURUECK",modeMenu||view==ModelInfo?"":"WEITER >",modeMenu?"":"ANSICHTEN",modeMenu?"":"START"};
    for(int i=0;i<(modeMenu?1:4);i++){canvas.drawRect(i*120,0,119,24,ACCENT);text(i*120+8,8,buttons[i],FG,1);}
  } else if(r==13) {
    const int count=countFor(view);
    String position=count?String(first+1)+"-"+String(min(first+HMX_PAGE_ROWS,count))+" / "+String(count):"0 / 0";
    text(8,1,modeMenu?"Betriebsart dauerhaft speichern":view==Detail?"Details: Zurueck zur Liste":view==ModelInfo?"Geraeteinfo: Zurueck zur Ansicht":position,MUTED,1);
    text(330,1,String("HMX ")+HMX_VERSION,MUTED,1);
  } else if(modeMenu) {
    if(r==2)text(12,4,"Auswahl wird dauerhaft gespeichert",MUTED,1);
    for(int option=0;option<2;option++) {
      const int top=option==0?4:7;
      if(r==top || r==top+1) {
        canvas.drawRect(12,(top-r)*24,456,48,ACCENT);
        if(r==top)text(24,12,String(choice.listenOnly==(option==1)?"* ":"  ")+
          (option==0?"Automatisch":"Listen only"),FG,2);
      }
    }
    if(r==10)text(12,4,choice.healthy?"Aktive Betriebsart steht immer oben":
      "Speicherfehler - Listen only; Wahl wiederholen",choice.healthy?MUTED:WARN,1);
    if(r==11)text(12,4,"Unten: Abbrechen / zur Anzeige zurueck",MUTED,1);
  } else if(view==Groups) {
    const char *labels[]={"Uebersicht","Alle WP-Topics","Zusatzdaten XTOP","Optional PCB","Dallas 1-Wire","Betriebsart"};
    int i=r-2;if(i<6)text(12,4,String(labels[i])+"  >",FG,2);
  } else if(view==ModelInfo) {
    for(int half=0;half<2;half++) {
      const int line=(r-2)*2+half;
      text(8,half*12+2,fit(modelInfoLine(line),77),
        line==0?ACCENT:line==15&&stale(0)?WARN:FG,1);
    }
  } else if(view==Detail) {
    String name,value,id;valueFor(backView,detailIndex,name,value,id);
    const int line=r-2;
    String s=line==0?id:line==1?name.substring(0,38):line==2?name.substring(38):
       line==4?value.substring(0,38):line==5?value.substring(38):
       line==7?"Empfang: "+detailAge(backView,detailIndex):
       line==8?"Nur Anzeige - keine WP-Befehle":"";
    text(8,4,s,line==4?ACCENT:FG,2);
  } else {
    for(int half=0;half<2;half++) {
      const int i=first+(r-2)*2+half, y=half*12;
      if(i<countFor(view)) {
        if(i%2==0)canvas.fillRect(4,y,472,12,0x10c4);
        String name,value,id;valueFor(view,i,name,value,id);
        const int number=view==Overview?overviewIds[i]:view==Dallas?i+1:i;
        text(8,y+2,String(number),ACCENT,1);
        text(42,y+2,fit(name,50),MUTED,1);
        text(360,y+2,fit(value,18),view==Dallas||!stale(blockFor(view))?FG:WARN,1);
      } else if(i==0) text(8,y+2,"Keine Werte / Funktion deaktiviert",MUTED,1);
    }
  }
  const int h=r==13?8:24;
  drawStrip(r*24,canvas.getBuffer(),h);
}
int buttonFor(int x,int y) {return y>=288&&y<312?min(3,x/120):-1;}
void navigate(int b) {
  if(modeMenu){modeMenu=false;repaint=true;paintRow=0;return;}
  if(view==ModelInfo && b==0){view=modelBackView;first=modelBackFirst;repaint=true;paintRow=0;return;}
  if(view==ModelInfo && b==1)return;
  if(view==Detail && b==0){view=backView;first=backFirst;repaint=true;paintRow=0;return;}
  if(b==0||b==1) first=hmx::clampPage(first+(b==0?-HMX_PAGE_ROWS:HMX_PAGE_ROWS),countFor(view),HMX_PAGE_ROWS);
  if(b==2){view=Groups;first=0;}
  if(b==3){view=Overview;first=0;}
  repaint=true;paintRow=0;
}
bool selectMode(bool listen) {
  if(!choice.needsWrite(listen)){modeMenu=false;repaint=true;paintRow=0;return true;}
  hmxTxLock();
  // Hold TX off during flash commit. A failed commit remains passive.
  Serial1.flush();if(cmdQueue)xQueueReset(cmdQueue);sending=false;
  passive.store(true);digitalWrite(HMX_ENABLE,LOW);
  if(!prefsOpen)prefsOpen=modePreferences.begin("hmx_mode",false);
  bool saved=prefsOpen && modePreferences.putBool("listen",listen)==1;
  choice.commit(listen,saved);
  policy.tick(millis(),ioOk && txMutex && choice.healthy,choice.listenOnly,
              heishamonSettings.listenonly,Serial1.available()>0,HMX_AUTO_OBSERVE_MS);
  passive.store(policy.passive());
  digitalWrite(HMX_ENABLE,hmxListenOnly()?LOW:HIGH);
  hmxTxUnlock();
  modeMenu=!saved;repaint=true;paintRow=0;
  return saved;
}
void pollTouch(uint32_t now) {
  if(uint32_t(now-lastTouchPoll)<30)return;lastTouchPoll=now;
  uint8_t d[5];
  bool ok=readReg(HMX_TOUCH_ADDR,0x02,d,sizeof(d));
  const bool down=ok && (d[0]&0x0f)>0;
  if(!down){touchDown=false;suppressTouch=false;touchButton=-1;return;}
  int x=((d[1]&0x0f)<<8)|d[2],y=((d[3]&0x0f)<<8)|d[4];
#if HMX_TOUCH_SWAP_XY
  int t=x;x=y;y=t;
#endif
#if HMX_TOUCH_INVERT_X
  x=479-x;
#endif
#if HMX_TOUCH_INVERT_Y
  y=319-y;
#endif
  #if HMX_TOUCH_DEBUG
  Serial.printf("HMX touch: x=%d y=%d\n",x,y);
#endif
  if(x<0||x>=480||y<0||y>=320)return;
  if(!touchDown) {
    // First tap after dimming wakes only, avoiding accidental navigation.
    suppressTouch=uint32_t(now-lastTouch)>HMX_DIM_AFTER_MS;
    lastTouch=now;ledcWrite(HMX_LCD_BL,HMX_BRIGHTNESS);
    touchDown=true;touchButton=buttonFor(x,y);repeatAt=now+600;
    if(suppressTouch)return;
    if(modeMenu) {
      if(y>=96 && y<144)selectMode(false);
      else if(y>=168 && y<216)selectMode(true);
      else if(touchButton==0)navigate(touchButton);
      suppressTouch=true;return;
    }
    const int header=hmx::headerTarget(x,y);
    if(header>=0) {
      if(header==0)openModelInfo();else {modeMenu=true;repaint=true;paintRow=0;}
      touchButton=-1;suppressTouch=true;return;
    }
    if(touchButton>=0)navigate(touchButton);
    else if(view==Groups && y>=48 && y<192) {
      const View pages[]={Overview,All,Extra,Optional,Dallas};
      const int group=(y-48)/24;
      if(group==5)modeMenu=true;else view=pages[group];
      first=0;repaint=true;paintRow=0;
    } else if(view!=Detail && view!=ModelInfo && y>=48 && y<288) {
      int i=first+(y-48)/12;
      if(i<countFor(view)){backView=view;backFirst=first;detailIndex=i;view=Detail;repaint=true;paintRow=0;}
    }
  } else if(!suppressTouch && touchButton>=0 && touchButton<2 &&
      buttonFor(x,y)==touchButton && (int32_t)(now-repeatAt)>=0) {
    navigate(touchButton);repeatAt=now+200;lastTouch=now;
  }
}
}
void hmxTxLock(){if(txMutex)xSemaphoreTakeRecursive(txMutex,portMAX_DELAY);}
void hmxTxUnlock(){if(txMutex)xSemaphoreGiveRecursive(txMutex);}
bool hmxListenOnly(){return passive.load() || heishamonSettings.listenonly;}
bool hmxModeAvailable(){return ioOk && choice.healthy;}
const char *hmxModeText(){
 if(!choice.healthy)return "SPEICHERFEHLER / PASSIV";
 switch(policy.mode){
 case hmx::Mode::Forced:return "WAHL: LISTEN ONLY";
 case hmx::Mode::Configured:return "AUTO / WEB: LISTEN ONLY";
 case hmx::Mode::Traffic:return "AUTO / RX: LISTEN ONLY";
 case hmx::Mode::Observing:return "AUTO / PRUEFUNG";
 case hmx::Mode::Active:return "AUTO / AKTIV";
 case hmx::Mode::IoFault:return "I2C-FEHLER: LISTEN ONLY";
 }return "";
}
void hmxEarly(){
 txMutex=xSemaphoreCreateRecursiveMutex();
 pinMode(HMX_ENABLE,OUTPUT);digitalWrite(HMX_ENABLE,LOW);
 pinMode(HMX_LCD_CS,OUTPUT);digitalWrite(HMX_LCD_CS,HIGH);
 pinMode(HMX_ETH_CS,OUTPUT);digitalWrite(HMX_ETH_CS,HIGH);
}
void hmxBegin(bool pendingTraffic){
 pinMode(HMX_LCD_CS,OUTPUT);digitalWrite(HMX_LCD_CS,HIGH);
 pinMode(HMX_LCD_DC,OUTPUT);
 pinMode(HMX_LCD_BL,OUTPUT);digitalWrite(HMX_LCD_BL,LOW);
 Wire.begin(HMX_I2C_SDA,HMX_I2C_SCL,100000);Wire.setTimeOut(5);
 // MCP23008: all inputs except GP1/GP2; pull-ups on input pins.
 ioOk=writeReg(0x0a,outputs) && writeReg(0x00,0xf9) && writeReg(0x06,0xf9);
 uint8_t g=0xff;ioOk=ioOk && readReg(HMX_MCP_ADDR,0x09,&g,1);
 prefsOpen=modePreferences.begin("hmx_mode",false);
 bool hasChoice=prefsOpen && modePreferences.isKey("listen");
 uint8_t savedChoice=hasChoice?modePreferences.getUChar("listen",0xff):0;
 bool valid=!hasChoice || (modePreferences.getType("listen")==PT_U8 && savedChoice<=1);
 choice.load(prefsOpen,valid,savedChoice==1);
 policy.boot(ioOk&&txMutex&&choice.healthy,choice.listenOnly,heishamonSettings.listenonly,pendingTraffic || Serial1.available()>0);
 passive.store(policy.passive());modeReady=true;
 digitalWrite(HMX_ENABLE,hmxListenOnly()?LOW:HIGH);
}
void hmxWriteEnable(uint8_t value){
 if(!modeReady){digitalWrite(HMX_ENABLE,LOW);return;}
 hmxTxLock();
 bool p=hmxListenOnly();
 if(p) {Serial1.flush();if(cmdQueue)xQueueReset(cmdQueue);}
 digitalWrite(HMX_ENABLE,p?LOW:value);
 hmxTxUnlock();
}
void hmxRx(uint8_t b){if(b<3){rxAt[b]=millis();received[b]=true;}}
void hmxDisplayBegin(){
 if(!canvas.getBuffer())return;
 SPI.begin(HMX_SCK,HMX_MISO,HMX_MOSI); // same object as ETH, same pin mapping
 if(ioOk){
   writeReg(0x0a,outputs & ~(1<<HMX_MCP_LCD_RESET) & ~(1<<HMX_MCP_TOUCH_RESET));delay(20);
   writeReg(0x0a,outputs);delay(120);
 }
 cmd(0x01);delay(150);
 // ST7796S unlock and panel setup, RGB565, landscape.
 command1(0xf0,0xc3);command1(0xf0,0x96);command1(0x36,HMX_LCD_MADCTL);command1(0x3a,0x55);
 command1(0xb4,0x01);
 const uint8_t b6[]={0x80,0x02,0x3b};cmd(0xb6,b6,sizeof(b6));
 command1(0xf0,0x3c);command1(0xf0,0x69);
 cmd(HMX_LCD_INVERT?0x21:0x20);cmd(0x11);delay(120);cmd(0x29);
 ledcAttach(HMX_LCD_BL,5000,8);ledcWrite(HMX_LCD_BL,HMX_BRIGHTNESS);
 lastTouch=millis();repaint=true;paintRow=0;
}
void hmxLoop(){
 uint32_t now=millis();
 observedRx = observedRx || Serial1.available()>0;
 if(uint32_t(now-lastPoll)>=20) {
   lastPoll=now;uint8_t g=0xff;
   bool ok=readReg(HMX_MCP_ADDR,0x09,&g,1);
   // On recovery, reconfigure reset outputs and unused-input pull-ups.
   if(ok&&!ioOk)ok=writeReg(0x0a,outputs)&&writeReg(0x00,0xf9)&&writeReg(0x06,0xf9);
   ioOk=ok;
   hmxTxLock();
   bool old=passive.load();
   auto prev=policy.mode;
   policy.tick(now,ioOk&&txMutex&&choice.healthy,choice.listenOnly,heishamonSettings.listenonly,
               observedRx,HMX_AUTO_OBSERVE_MS);
   observedRx=false;
   bool next=policy.passive();
   if(old!=next || prev!=policy.mode){
     // Drain the UART before removing the physical TX enable.
     Serial1.flush();if(cmdQueue)xQueueReset(cmdQueue);sending=false;
     passive.store(next);
     digitalWrite(HMX_ENABLE,next?LOW:HIGH);
     repaint=true;paintRow=0;
   }
   hmxTxUnlock();
 }
 if(!canvas.getBuffer())return;
 pollTouch(now);
 if(uint32_t(now-lastTouch)>HMX_DIM_AFTER_MS)ledcWrite(HMX_LCD_BL,HMX_DIM_BRIGHTNESS);
 if(!repaint && uint32_t(now-lastFrame)>=1000){repaint=true;paintRow=0;}
 if(repaint){renderRow(paintRow++);if(paintRow>=14){repaint=false;lastFrame=now;}}
}
#endif
