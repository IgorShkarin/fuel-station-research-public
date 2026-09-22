# Fuel Station Research

Open-source monitor for the availability of AI-95 at selected fuel stations.

It collects public status signals from TutBenz, ГдеБЕНЗ and Yandex Maps, writes an event history, can send a Pushover notification when fuel appears, and includes a browser-based map and notification timeline.

## What is public here

This repository contains the real monitored stations, public source IDs, the complete accumulated event journal and the map snapshot used by the project. The journal records timestamped source status changes and can be used to analyse recurring availability windows.

It contains no Pushover credentials, LAN addresses, SSH details, key paths, home-automation components, runtime state, logs or private backup data.

## Quick start

1. Optionally add Pushover credentials to your local environment:

   ```sh
   export PUSHOVER_TOKEN='...'
   export PUSHOVER_USER_KEY='...'
   ```

2. Run a one-off check:

   ```sh
   python3 check_ai95.py
   ```

3. Start the monitor only when you are ready for a persistent local process:

   ```sh
   ./fuel-monitor.sh start
   ```

## Map and notification history

Open [`dashboard/ai95-map.html`](dashboard/ai95-map.html) for the map and [`dashboard/notification-history.html`](dashboard/notification-history.html) for the raw chronology of status changes that could lead to a notification. The timeline loads [`data/events.jsonl`](data/events.jsonl); serve the repository over HTTP when opening it locally:

```sh
python3 -m http.server 8047
```

## Limits

An `unknown → available` transition can be source resynchronization rather than a delivery. Treat status changes as signals to verify before driving, not as a guarantee that fuel has physically arrived.

## License

MIT
