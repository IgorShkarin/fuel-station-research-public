#!/usr/bin/env python3
"""Report first observed availability transitions; it never changes monitor state."""
import json
from collections import defaultdict
from pathlib import Path

events=Path(__file__).resolve().parent/'data'/'events.jsonl'
rows=defaultdict(list)
if events.exists():
    for line in events.read_text(encoding='utf8').splitlines():
        try:
            e=json.loads(line)
            if not e.get('old_status') in ('has','yes','IN_STOCK','available','queue','limit') and e.get('available'):
                rows[(e['station'],e['fuel'])].append((e['at'],e['source']))
        except (json.JSONDecodeError,KeyError):
            continue
for (station,fuel),hits in sorted(rows.items()):
    print(f'{station} | {fuel} | ' + ', '.join(f'{at} ({source})' for at,source in hits))
