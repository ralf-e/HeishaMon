// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

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
