# WireGuard Easy – Home Assistant Integration

Custom integration for Home Assistant that connects to the WireGuard Easy (wg-easy) API and exposes peers as devices with sensors and binary sensors.

## Source project
https://github.com/wg-easy/wg-easy

---

## Installation

### Installation via HACS

1. Add this repository as a custom repository to HACS:

[![Add Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=metaathron&repository=ha-wgeasy&category=Integration)

2. Use HACS to install the integration.
3. Restart Home Assistant.
4. Set up the integration using the UI:

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=wg_easy)


### Manual Installation

1. Download the integration files from the GitHub repository.
2. Place the integration folder in the custom_components directory of Home Assistant.
3. Restart Home Assistant.
4. Set up the integration using the UI:

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=wg_easy)


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

## License

This project is licensed under the MIT License.

Copyright (c) 2026 [metaathron](https://github.com/metaathron/)

You are free to use, modify, and distribute this software in accordance with the MIT License.

If you find this project useful, attribution and a link back to the original repository are appreciated:
<https://github.com/metaathron/ha-wgeasy>
