# Android / Termux deployment

The monitor can run on an Android device with Termux. Keep the device-specific connection details, SSH keys, LAN address, Pushover environment file and runtime history outside this repository.

Recommended local layout:

```text
~/fuel-station-research/
  station_mapping.json     # local, ignored by Git
  data/                    # local, ignored by Git
  .config/fuel-monitor.env # local, ignored by Git
```

Start a foreground or supervised local process only after checking that your station mapping and notification credentials work with `python3 check_ai95.py`.

