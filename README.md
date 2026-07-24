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
   - wg-easy API version (`auto`, `v14`, or `v15` – see below)
   - API token (v15) and/or password (v14), depending on your server

### Which wg-easy version am I running?

This integration supports both wg-easy **v14** and **v15**:

- **`auto`** (default): tries whichever credential you filled in – password first (v14), then token (v15) – and keeps the first one that connects. Fill in both if you're not sure which version your server is, and leave the version selector on `auto`.
- **`v14`**: only tries the password-based login. Use this if you know your server is on v14.
- **`v15`**: only tries the token-based request. Use this if you know your server is on v15.

Existing installs configured before this option existed keep working unchanged – they're treated as `v15` automatically.

### Where do I get the password (v14)?

Use the same password you use to log in to the wg-easy web UI. This is set via the `PASSWORD` (legacy) or `PASSWORD_HASH` environment variable when the wg-easy container was started.

### Where do I get the token (v15)?

In the wg-easy v15 admin panel, go to **Admin Panel → General → Metrics**, and set (or read) the **Bearer Password** for the metrics endpoint. That's the value this integration sends as the API token. Note that wg-easy's officially documented general API (`/api/...`) uses HTTP Basic Auth (same username/password as the web UI) – this Bearer password is specifically tied to the metrics feature. If you haven't enabled a metrics Bearer password yet, set one there first.

### A note on the `latest` Docker tag (as of 2026-07-24)

If you run wg-easy via the `ghcr.io/wg-easy/wg-easy:latest` tag, you are very likely still on **v14**, not v15 – the wg-easy maintainers have intentionally kept `latest` pointing at v14 to avoid breaking existing installs during the v15 migration (see [wg-easy/wg-easy#2167](https://github.com/wg-easy/wg-easy/issues/2167)). If you want to run v15, pin the image tag explicitly (e.g. `:15`) instead of relying on `latest`. Either way, leaving the API version selector on `auto` in this integration will keep working across that difference.

---

## Features

- Automatic peer discovery
- Dynamic device creation/removal
- Peer-level monitoring
- Transfer statistics (RX/TX, rates)
- Configurable online detection
- WireGuard server overview
- wg-easy v14 and v15 API support (auto-detected, or manually selected)

---

## License

This project is licensed under the MIT License.

Copyright (c) 2026 [metaathron](https://github.com/metaathron/)

You are free to use, modify, and distribute this software in accordance with the MIT License.

If you find this project useful, attribution and a link back to the original repository are appreciated:
<https://github.com/metaathron/ha-wgeasy>
