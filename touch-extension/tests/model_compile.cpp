#include "../extension/hmx_model.h"
constexpr bool modelChecks() {
  const auto known=hmx::lookupModel("C2 D3 0B 35 65 B2 D3 0B 96 65");
  if(!known.valid||known.count!=1||known.record->id!=21||
     !hmx::modelTextEqual(hmx::modelShortName(known),"WH-MDC09J3E5"))return false;
  const auto lower=hmx::lookupModel(" \tc2 d3 0b 35 65 b2 d3 0b 96 65\n");
  if(lower.count!=1)return false;
  if(hmx::lookupModel("").valid||hmx::lookupModel(nullptr).valid||
     hmx::lookupModel("C2 D3 0B 35 65 B2 D3 0B 96").valid||
     hmx::lookupModel("C2 D3 0B 35 65 B2 D3 0B 96 GG").valid||
     hmx::lookupModel("C2 D3 0B 35 65 B2 D3 0B 96 65 00").valid)return false;
  const auto unknown=hmx::lookupModel("00 00 00 00 00 00 00 00 00 00");
  if(!unknown.valid||unknown.count!=0)return false;
  const hmx::ModelRecord duplicate[]={hmx::modelRecords[0],hmx::modelRecords[0]};
  const auto ambiguous=hmx::lookupModelIn("E2 CF 0B 13 33 32 D1 0C 16 33",duplicate,2);
  if(ambiguous.count!=2||!hmx::modelTextEqual(hmx::modelShortName(ambiguous),"Modell mehrdeutig"))return false;
  for(unsigned i=0;i<hmx::modelCount;i++) {
    char raw[30]={};const char *hex="0123456789ABCDEF";
    for(unsigned j=0;j<10;j++) {
      raw[j*3]=hex[hmx::modelRecords[i].key[j]>>4];
      raw[j*3+1]=hex[hmx::modelRecords[i].key[j]&15];
      if(j<9)raw[j*3+2]=' ';
    }
    if(hmx::lookupModel(raw).count<1)return false;
  }
  return hmx::headerTarget(0,0)==0 && hmx::headerTarget(239,23)==0 &&
    hmx::headerTarget(240,0)==1 && hmx::headerTarget(479,23)==1 &&
    hmx::headerTarget(10,24)==-1 && hmx::headerTarget(-1,0)==-1 &&
    hmx::headerTarget(480,0)==-1;
}
static_assert(modelChecks(),"Model lookup, malformed/unknown/duplicate keys and header targets");
