// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

#pragma once
#include "hmx_config.h"
#if defined(ESP32) && HMX_ENABLED
#include <Arduino.h>
inline bool hmxOwnsPin(unsigned int p) {
  return p==HMX_LCD_CS || p==HMX_LCD_DC || p==HMX_LCD_BL || p==HMX_I2C_SDA || p==HMX_I2C_SCL;
}
void hmxEarly();
void hmxBegin(bool pendingTraffic);
void hmxDisplayBegin();
void hmxLoop();
void hmxRx(uint8_t block);
bool hmxListenOnly();
void hmxWriteEnable(uint8_t value);
void hmxTxLock();
void hmxTxUnlock();
bool hmxModeAvailable();
const char *hmxModeText();
#else
inline void hmxEarly() {}
inline void hmxBegin(bool) {}
inline void hmxDisplayBegin() {}
inline void hmxLoop() {}
inline void hmxRx(uint8_t) {}
inline void hmxTxLock() {}
inline void hmxTxUnlock() {}
#endif
