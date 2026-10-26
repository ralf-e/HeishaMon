#pragma once
namespace hmx {
// HeishaMon decoded enums: 0..8 Heat, Cool, AutoHeat, DHW, HeatDHW,
// CoolDHW, AutoHeatDHW, AutoCool, AutoCoolDHW. -1 means unknown.
constexpr int overviewPermission(int wp, int mode, int zones, int kind) {
  if(wp==0)return 0;
  if(wp!=1 || mode<0 || mode>8)return -1;
  if(kind==1)return (mode==3 || mode==4 || mode==5 || mode==6 || mode==8)?1:0;
  if(kind!=2 && kind!=3)return -1;
  if(mode==3)return 0;
  if(zones<0 || zones>2)return -1;
  return zones==2 || zones==(kind==2?0:1)?1:0;
}
constexpr int timerPermission(int raw) {return raw==0?0:raw==1?1:-1;}
} // namespace hmx
