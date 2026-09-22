# Fuel Station Research

Open-source template for monitoring the availability of AI-95 at selected fuel stations.

It collects public status signals from TutBenz, ГдеБЕНЗ and Yandex Maps, writes a local event history, can send a Pushover notification when fuel appears, and includes a browser-based map example.

## What is public here

This repository contains source code, a deliberately anonymized map example and a sample station configuration. It contains no runtime journal, Pushover credentials, LAN addresses, SSH details, home-automation components or the author's selected stations.

The original event history is intentionally not published because even public fuel-station coordinates can reveal a personal routine when combined over time. The monitor can produce a local history in `data/events.jsonl` after you configure your own stations.

## Quick start

1. Copy the configuration template:

   ```sh
   cp station_mapping.example.json station_mapping.json
   ```

2. Replace the placeholders with station IDs and coordinates you have verified through the public source interfaces.
3. Optionally add Pushover credentials to your local environment:

   ```sh
   export PUSHOVER_TOKEN='...'
   export PUSHOVER_USER_KEY='...'
   ```

4. Run a one-off check:

   ```sh
   python3 check_ai95.py
   ```

5. Start the monitor only when you are ready for a persistent local process:

   ```sh
   ./fuel-monitor.sh start
   ```

## Map example

Open [`dashboard/ai95-map.html`](dashboard/ai95-map.html) in a browser. All names, coordinates, statuses and time windows on this page are anonymized examples; they are not current fuel advice.

## Limits

An `unknown → available` transition can be source resynchronization rather than a delivery. Treat status changes as signals to verify before driving, not as a guarantee that fuel has physically arrived.

## License

MIT

