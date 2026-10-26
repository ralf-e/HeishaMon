#pragma once
namespace hmx {
// Storage result handling, independent from Arduino/NVS for host verification.
class Choice {
public:
 bool listenOnly = true;
 bool healthy = false;
 constexpr void load(bool opened, bool valid, bool saved) {
  healthy=opened && valid;listenOnly=healthy?saved:true;
 }
 constexpr bool needsWrite(bool requested) const {return !healthy || requested!=listenOnly;}
 constexpr void commit(bool requested, bool success) {
  healthy=success;listenOnly=success?requested:true;
 }
};
}
