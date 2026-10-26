// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

#pragma once
// Display-only lookup. No changes to HeishaMon's TOP92/MQTT representation.
namespace hmx {
struct ModelRecord {
  unsigned char key[10];
  const char *idu,*odu,*kit,*power,*phase,*type;
  unsigned id;
};
#include "hmx_model_data.h"
struct ModelMatch {const ModelRecord *record;unsigned count;bool valid;};
constexpr int hexDigit(char c) {
  return c>='0'&&c<='9'?c-'0':c>='A'&&c<='F'?c-'A'+10:
    c>='a'&&c<='f'?c-'a'+10:-1;
}
constexpr bool modelSpace(char c){return c==' '||c=='\t'||c=='\r'||c=='\n';}
constexpr bool parseModelKey(const char *s,unsigned char *out) {
  if(!s)return false;
  for(unsigned i=0;i<10;i++) {
    while(modelSpace(*s))++s;
    if(!*s)return false;
    const int hi=hexDigit(*s++);if(hi<0||!*s)return false;
    const int lo=hexDigit(*s++);if(lo<0)return false;
    out[i]=static_cast<unsigned char>((hi<<4)|lo);
    if(i<9 && !modelSpace(*s))return false;
  }
  while(modelSpace(*s))++s;
  return *s==0;
}
constexpr ModelMatch lookupModelIn(const char *raw,const ModelRecord *records,unsigned n) {
  unsigned char key[10]={};
  if(!parseModelKey(raw,key))return {nullptr,0,false};
  ModelMatch found={nullptr,0,true};
  for(unsigned i=0;i<n;i++) {
    bool same=true;
    for(unsigned j=0;j<10;j++)if(records[i].key[j]!=key[j])same=false;
    if(same){if(!found.record)found.record=&records[i];++found.count;}
  }
  return found;
}
constexpr ModelMatch lookupModel(const char *raw){return lookupModelIn(raw,modelRecords,modelCount);}
constexpr bool modelTextEqual(const char *a,const char *b) {
  while(*a && *a==*b){++a;++b;}return *a==*b;
}
constexpr const char *modelShortName(ModelMatch m) {
  if(!m.valid)return "Modellkennung ungueltig";
  if(m.count==0)return "Modell unbekannt";
  if(m.count!=1)return "Modell mehrdeutig";
  return *m.record->odu && !modelTextEqual(m.record->odu,"Monoblock")?m.record->odu:
    *m.record->idu && !modelTextEqual(m.record->idu,"Monoblock")?m.record->idu:m.record->kit;
}
// The touch targets include the narrow visual button margins.
constexpr int headerTarget(int x,int y) {
  return x<0||x>=480||y<0||y>=24?-1:x<240?0:1;
}
} // namespace hmx
