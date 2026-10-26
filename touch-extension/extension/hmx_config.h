// SPDX-License-Identifier: MPL-2.0
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

#pragma once
// HeishaMon Touch extension 0.1.0-dev.7. Logical GPIOs, NOT connector positions.
#define HMX_ENABLED 1
#define HMX_LCD_CS 33
#define HMX_LCD_DC 34
#define HMX_LCD_BL 35
#define HMX_I2C_SDA 36
#define HMX_I2C_SCL 37
#define HMX_SCK 12
#define HMX_MOSI 11
#define HMX_MISO 13
#define HMX_ETH_CS 10
#define HMX_ENABLE 5
#define HMX_MCP_ADDR 0x20
#define HMX_TOUCH_ADDR 0x38
#define HMX_MCP_TOUCH_RESET 1
#define HMX_MCP_LCD_RESET 2
#define HMX_SPI_HZ 8000000
#define HMX_STALE_MS 30000
#define HMX_AUTO_OBSERVE_MS 500
#define HMX_TOUCH_SWAP_XY 1
#define HMX_TOUCH_INVERT_X 0
#define HMX_TOUCH_INVERT_Y 1
#define HMX_BRIGHTNESS 180
#define HMX_DIM_BRIGHTNESS 35
#define HMX_DIM_AFTER_MS 60000
#define HMX_LCD_MADCTL 0x28
#define HMX_LCD_INVERT 1
#define HMX_TOUCH_DEBUG 0
#define HMX_VERSION "0.1.0-dev.7"

#define HMX_PAGE_ROWS 20

// Baseline commit of the integrated HeishaMon source; update after upstream review.
#define HMX_UPSTREAM_COMMIT "b3ef43691f21985c851903d69a0f2e8647ed31f8"
