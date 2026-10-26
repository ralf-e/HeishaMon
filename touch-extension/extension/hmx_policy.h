// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

#pragma once
#include <stdint.h>
// No Arduino dependency: exercised on host with the real C++ implementation.
namespace hmx {
enum class Mode { Forced, Configured, Traffic, Observing, Active, IoFault };
class Policy {
public:
  Mode mode = Mode::IoFault;
  constexpr bool passive() const { return mode != Mode::Active; }
  constexpr void boot(bool io, bool forced, bool configured, bool traffic) {
    mode = !io ? Mode::IoFault : forced ? Mode::Forced :
           configured ? Mode::Configured : traffic ? Mode::Traffic : Mode::Active;
  }
  constexpr void tick(uint32_t now, bool io, bool forced, bool configured, bool traffic,
            uint32_t observationMs) {
    if (!io || forced || configured) {
      mode = !io ? Mode::IoFault : forced ? Mode::Forced : Mode::Configured;
      return;
    }
    if (mode == Mode::Forced || mode == Mode::Configured || mode == Mode::IoFault) {
      mode = Mode::Observing; since = now; seen = traffic;
    } else if (mode == Mode::Observing) {
      seen = seen || traffic;
      if (uint32_t(now - since) >= observationMs)
        mode = seen ? Mode::Traffic : Mode::Active;
    }
    // Traffic is latched until the stored touch selection is cycled or the device restarted.
  }
private:
  uint32_t since = 0;
  bool seen = false;
};
inline constexpr int clampPage(int first, int count, int rows) {
  if (count <= 0) return 0;
  const int last = ((count - 1) / rows) * rows;
  return first < 0 ? 0 : first > last ? last : first;
}
}
