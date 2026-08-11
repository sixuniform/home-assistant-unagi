# Unagi Electricity Price Forecast for Home Assistant

Unofficial Home Assistant custom integration for the public **Unagi** Swedish electricity-price forecast feed.

Unagi provides hourly forecasts for Swedish bidding areas **SE1, SE2, SE3 and SE4**, covering today through up to seven days ahead. The integration deliberately exposes Nordpool-style `today`, `tomorrow`, `raw_today` and `raw_tomorrow` attributes so existing Home Assistant templates and energy-management code can reuse the familiar `start` / `end` / `value` structure.

## Features

- UI setup; no YAML required.
- Select **SE1 / SE2 / SE3 / SE4** during setup.
- Configurable network polling: **3, 6, 12 or 24 hours** (default **6 hours**).
- One coordinated HTTP request per configured area per polling interval.
- No per-entity polling and no tight retry loop.
- Current price advances locally every hour from cached data without making another HTTP request.
- Nordpool-compatible core attributes:
  - `today`
  - `tomorrow`
  - `raw_today`
  - `raw_tomorrow`
  - `current_price`
  - `average`, `min`, `max`, `mean`
  - `off_peak_1`, `peak`, `off_peak_2`
  - `tomorrow_valid`
  - `low_price`
  - `price_percent_to_average`
  - `region`, `currency`, `unit`
- Extended days:
  - `day_2` … `day_7`
  - `raw_day_2` … `raw_day_7`
  - matching `_date`, `_kind`, `_daily_avg` and `_cheapest_hours` attributes
- Full Unagi metadata in `raw_forecast`, including `forecast`, `low`, `high`, `kind` and `horizon_days`.
- Unagi's live forecast accuracy block exposed as `accuracy`.
- Home Assistant diagnostics with compact feed/configuration health information.
- Large list attributes are marked unrecorded to avoid unnecessary Recorder/database growth.

## Important price-basis note

Unagi's public feed is **SEK/kWh excluding VAT, grid fees and retailer markup**. This integration intentionally keeps those source values unchanged. It does not apply Home Assistant Nordpool integration VAT/additional-cost templates.

Unagi's public feed is hourly (`PT1H`). Settled values are hourly averages of Nord Pool's 15-minute settlement prices. The integration therefore keeps native hourly periods instead of pretending the forecasts have 15-minute resolution.

## Installation through HACS

1. Upload this repository to GitHub as a **public repository**.
2. In `custom_components/unagi/manifest.json`, replace `YOUR_GITHUB_USERNAME` in `documentation` and `issue_tracker` with your GitHub username/repository path.
3. Optional but recommended before publishing broadly: add your GitHub handle to `codeowners`, for example:

   ```json
   "codeowners": ["@your-github-name"]
   ```

4. In HACS, open **Custom repositories**.
5. Add your repository URL and choose **Integration**.
6. Install **Unagi Electricity Price Forecast**.
7. Restart Home Assistant.
8. Go to **Settings → Devices & services → Add integration → Unagi Electricity Price Forecast**.
9. Select the bidding area and polling interval.

You may add multiple entries if you want multiple Swedish bidding areas; an individual area can only be configured once.

## Updating the polling interval

Open **Settings → Devices & services → Unagi → Configure** and select 3, 6, 12 or 24 hours. Home Assistant reloads the integration automatically after the option changes.

The source feed itself is CDN-cached and normally regenerated only a few times daily, so there is usually little reason to select a very short interval. Six hours is the default compromise.

## Entity and attributes

For SE3 the entity will normally be named:

```text
sensor.unagi_se3
```

Example `raw_today` item:

```yaml
start: 2026-08-11 00:00:00+02:00
end: 2026-08-11 01:00:00+02:00
value: 0.8421
```

Example extended forecast use:

```jinja
{% for p in state_attr('sensor.unagi_se3', 'raw_day_3') or [] %}
  {{ p.start }} → {{ p.end }}: {{ p.value }} SEK/kWh
{% endfor %}
```

The richer `raw_forecast` attribute contains records such as:

```yaml
date: "2026-08-14"
kind: forecast
horizon_days: 3
start: 2026-08-14 12:00:00+02:00
end: 2026-08-14 13:00:00+02:00
value: 0.812
forecast: 0.812
low: 0.421
high: 1.337
```

`tomorrow_valid` is deliberately stricter than merely checking whether a forecast exists. It becomes `true` only when Unagi identifies tomorrow as `kind: actual` and the settled day is complete. Before Nord Pool publication, `tomorrow` can contain speculative Unagi values while `tomorrow_valid` remains `false`.

## Data source and attribution

Forecast data is provided by **Unagi — unagieel.net** using its public v1 JSON feed.

Unagi states that its forecast and accuracy data are free for **personal, non-commercial use with attribution**. Commercial use requires permission from Unagi. Forecasts are estimates, provided as-is, and are not financial or trading advice.

This repository contains original Home Assistant integration code and does **not** redistribute Unagi's source code.

## HACS / repository notes

The repository follows the HACS custom-integration layout:

```text
custom_components/
  unagi/
    __init__.py
    api.py
    config_flow.py
    const.py
    coordinator.py
    sensor.py
    manifest.json
    strings.json
    translations/
    brand/
hacs.json
README.md
LICENSE
```

A GitHub release is optional for a custom HACS repository. HACS can install directly from the default branch.

## License

The Home Assistant integration code in this repository is MIT licensed. Unagi forecast data remains subject to Unagi's separate data-use terms described above.
