#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/fuel-station-research"; PID="$ROOT/data/monitor.pid"; ENV="$HOME/.config/fuel-monitor.env"
if test -f "$ENV"; then set -a; source "$ENV"; set +a; fi; cd "$ROOT"; mkdir -p data
alive(){ test -f "$PID" && kill -0 "$(cat "$PID")" 2>/dev/null; }
case "${1:-once}" in
 once) exec python fuel_monitor.py;; test-push) exec python fuel_monitor.py --test-push;;
 start) alive && { echo "already running $(cat "$PID")"; exit 1; }; nohup python fuel_monitor.py --loop >>data/stdout.log 2>&1 & echo $! >"$PID";;
 stop) alive && kill "$(cat "$PID")" || true; rm -f "$PID";; restart) "$0" stop; "$0" start;;
 status) alive && echo "running pid=$(cat "$PID")" || echo stopped; test -f data/health.json && cat data/health.json;;
 logs) tail -n "${2:-100}" data/fuel-monitor.log;; *) echo 'start|stop|restart|status|logs|once|test-push';exit 2;;esac
