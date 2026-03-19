# WireGuard Easy – Home Assistant Integration

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=wg-easy)

Custom integration for Home Assistant that connects to the WireGuard Easy (wg-easy) API and exposes peers as devices with sensors and binary sensors.

## Source project
https://github.com/wg-easy/wg-easy

---

## Installation via HACS

[![Open your Home Assistant instance and show the add repository dialog](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=https://github.com/metaathron/ha-wgeasy&category=integration)

### Manual steps (if button does not work)

1. Open HACS
2. Go to Integrations
3. Click menu (⋮) → Custom repositories
4. Add:
   https://github.com/metaathron/ha-wgeasy
   Category: Integration

5. Install integration
6. Restart Home Assistant

---

## Setup

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Select WG Easy
4. Enter:
   - API URL
   - API Token

---

## Features

- Automatic peer discovery
- Dynamic device creation/removal
- Peer-level monitoring
- Transfer statistics (RX/TX, rates)
- Configurable online detection
- WireGuard server overview

---

## License

This project is free to use, modify, and distribute.

Author: metaathron  
Please retain attribution and link to the original repository:
https://github.com/metaathron/ha-wgeasy
