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

Setup is two steps:

1. **Server address and API version.** Go to Settings → Devices & Services → Add Integration → WG Easy, then enter:
   - **Server address** – just the base address, e.g. `https://your-wg-easy-host` or `https://your-wg-easy-host/subpath` if it's behind a reverse proxy on a subpath. No need to add any API path yourself.
   - **wg-easy API version** – `auto` (default), `v14`, or `v15`.
   - **Verify SSL certificate** – on by default; turn off only if your server uses a self-signed certificate you trust (see below).

   On submit, the integration makes an unauthenticated check against the server to confirm it's reachable and (in `auto` mode) to detect which API generation it's running. A bad address or an unreachable server is reported right here, before you're asked for anything sensitive.

2. **Credentials.** Based on what was detected (or what you picked manually), you're asked for exactly one value: **password** if v14, **API token** if v15. It's verified with a real request before the entry is created.

### Which wg-easy version am I running?

This integration supports both wg-easy **v14** and **v15**:

- **`auto`** (default): probes the server (no credentials needed for this step) to tell v14 and v15 apart, and shows you the matching credential field in step 2.
- **`v14`**: always shows the password field, regardless of what the probe would have guessed.
- **`v15`**: always shows the token field, regardless of what the probe would have guessed.

Existing installs configured before this option existed keep working unchanged – they're treated as `v15` automatically.

### Where do I get the password (v14)?

Use the same password you use to log in to the wg-easy web UI. This is set via the `PASSWORD_HASH` (bcrypt hash) environment variable when the wg-easy container was started — enter the plain-text password here, not the hash. Note: wg-easy v14 refuses to start at all if the plain-text `PASSWORD` variable is set (it's not just deprecated, it's a hard error) — `PASSWORD_HASH` is the only supported option.

### Where do I get the token (v15)?

In the wg-easy v15 admin panel, go to **Admin Panel → General → Metrics**, and set (or read) the **Bearer Password** for the metrics endpoint. That's the value this integration sends as the API token.

wg-easy v15 has no general Bearer-token JSON API – the only endpoint secured by this Bearer password is the metrics feature. This integration automatically talks to its JSON variant, `{your server address}/metrics/json`, which returns exactly the peer data needed (client list, transfer stats, handshake times) – you don't need to add `/metrics/json` to the address yourself, just enter the base server address in step 1. Note that wg-easy's officially documented general API (`/api/...`) uses HTTP Basic Auth (same username/password as the web UI) and is unrelated to this token.

### SSL certificate verification

Certificate verification is on by default. If your wg-easy server is only reachable with a self-signed certificate (e.g. an internal address with no public CA-issued cert), turn "Verify SSL certificate" off in step 1. Only do this on a trusted network – it removes protection against a machine-in-the-middle intercepting the connection to your wg-easy server.

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
- wg-easy v14 and v15 API support (auto-detected during setup, or manually selected)
- Optional SSL certificate verification, for self-signed wg-easy servers
- On v14, the `endpoint` and `ipv6 address` sensors (which v14 never provides) are created but disabled by default, instead of showing as permanently unavailable

---

## License

This project is licensed under the MIT License.

Copyright (c) 2026 [metaathron](https://github.com/metaathron/)

You are free to use, modify, and distribute this software in accordance with the MIT License.

If you find this project useful, attribution and a link back to the original repository are appreciated:
<https://github.com/metaathron/ha-wgeasy>
