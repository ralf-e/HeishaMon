#include "../extension/hmx_status.h"
#include "../extension/hmx_policy.h"
#include "../extension/hmx_choice.h"
using hmx::Policy;using hmx::Mode;
constexpr bool checks() {
  Policy p;
  p.boot(true,false,false,false);if(p.passive())return false;
  p.boot(true,false,false,true);if(p.mode!=Mode::Traffic)return false;
  p.tick(0,true,false,false,false,500);if(p.mode!=Mode::Traffic)return false;
  p.tick(1,true,true,false,false,500);if(p.mode!=Mode::Forced)return false;
  p.tick(2,true,false,false,false,500);if(p.mode!=Mode::Observing)return false;
  p.tick(501,true,false,false,false,500);if(!p.passive())return false;
  p.tick(502,true,false,false,false,500);if(p.passive())return false;
  p.tick(503,false,false,false,false,500);if(p.mode!=Mode::IoFault)return false;
  p.tick(504,true,false,false,false,500);if(p.mode!=Mode::Observing)return false;
  p.tick(600,true,false,false,true,500);p.tick(1004,true,false,false,false,500);
  if(p.mode!=Mode::Traffic)return false;
  p.tick(1005,true,false,true,false,500);if(p.mode!=Mode::Configured)return false;
  p.tick(1006,true,true,true,false,500);if(p.mode!=Mode::Forced)return false;
  p.tick(0xfffffff0u,true,false,false,false,500);
  p.tick(0x1e4u,true,false,false,false,500);if(p.passive())return false;
  if(hmx::clampPage(140,144,10)!=140)return false;
  if(hmx::clampPage(150,144,10)!=140)return false;
  if(hmx::clampPage(-10,144,10)!=0)return false;
  if(hmx::clampPage(10,0,10)!=0)return false;
  if(hmx::clampPage(20,144,20)!=20)return false;
  if(hmx::clampPage(160,144,20)!=140)return false;
  return true;
}
static_assert(checks(),"HMX mode/pagination regression");

constexpr bool persistentChecks() {
 hmx::Choice c;c.load(true,true,false);
 if(c.listenOnly || !c.healthy || c.needsWrite(false) || !c.needsWrite(true))return false;
 c.commit(true,true);if(!c.listenOnly || !c.healthy || c.needsWrite(true))return false;
 hmx::Choice reboot;reboot.load(true,true,c.listenOnly);
 Policy p;p.boot(reboot.healthy,reboot.listenOnly,false,false);
 if(p.mode!=Mode::Forced)return false;
 c.commit(false,false);if(c.healthy || !c.listenOnly || !c.needsWrite(false))return false;
 p.tick(0,c.healthy,c.listenOnly,false,false,500);if(!p.passive())return false;
 c.commit(false,true);p.tick(1,c.healthy,c.listenOnly,false,false,500);
 if(p.mode!=Mode::Observing)return false;
 p.tick(501,true,false,false,false,500);if(p.passive())return false;
 c.load(false,true,false);if(c.healthy || !c.listenOnly)return false;
 c.load(true,false,false);if(c.healthy || !c.listenOnly)return false;
 return true;
}
static_assert(persistentChecks(),"Persistent touch selection and storage-failure regression");

constexpr bool overviewStatusChecks() {
  const bool dhw[]={false,false,false,true,true,true,true,false,true};
  for(int mode=0;mode<9;mode++) {
    if(hmx::overviewPermission(1,mode,2,1)!=int(dhw[mode]))return false;
    for(int zone=0;zone<3;zone++)for(int kind=2;kind<=3;kind++) {
      const int expected=mode!=3 && (zone==2 || zone==(kind==2?0:1));
      if(hmx::overviewPermission(1,mode,zone,kind)!=expected)return false;
      if(hmx::overviewPermission(0,mode,zone,kind)!=0)return false;
    }
  }
  return hmx::overviewPermission(-1,4,2,1)==-1 &&
    hmx::overviewPermission(1,-1,2,1)==-1 &&
    hmx::overviewPermission(1,9,2,1)==-1 &&
    hmx::overviewPermission(1,0,-1,2)==-1 &&
    hmx::overviewPermission(1,0,3,3)==-1 &&
    hmx::timerPermission(-1)==-1 && hmx::timerPermission(2)==-1 &&
    hmx::timerPermission(0)==0 && hmx::timerPermission(1)==1;
}
static_assert(overviewStatusChecks(), "Overview status: modes/zones/off/unknown/timer");
