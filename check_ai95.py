#!/usr/bin/env python3
"""One-off, unauthenticated check. It does not schedule or persist monitoring."""
import json, re, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIONS = json.loads((ROOT / "station_mapping.json").read_text())['stations']
HEADERS = {'User-Agent': 'fuel-station-research/1.0 (+one-off status check)', 'Accept': 'application/json,text/html'}

def get(url):
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except urllib.error.URLError as e:
        return 'NETWORK_ERROR', str(e.reason)

def tutbenz(station_id):
    if not station_id: return 'not mapped'
    code, body = get('https://tutbenz.app/api/stations/' + station_id)
    if code != 200: return 'HTTP ' + str(code)
    states = json.loads(body).get('states', [])
    wanted = [x for x in states if x.get('fuelType') in ('ai95', 'ai95_plus', 'ai95premium')]
    return ', '.join(f"{x['fuelType']}={x.get('status','unknown')}" + (' (stale)' if x.get('stale') else '') for x in wanted) or '95 not listed'

def yandex(station_id):
    code, body = get('https://yandex.ru/maps/org/x/' + station_id + '/')
    if code != 200: return 'HTTP ' + str(code)
    match = re.search(r'"fuel":(\[\{.*?\}\]),"status"', body)
    if not match: return 'fuel block not present'
    try:
        fuels = json.loads(match.group(1))
    except json.JSONDecodeError: return 'fuel block parse error'
    wanted = [x for x in fuels if x.get('fuelType') in ('AI95', 'AI95_PREMIUM')]
    return ', '.join(f"{x.get('localizedName',x.get('fuelType'))}={x.get('status','UNKNOWN')}" for x in wanted) or '95 not listed'

def gdebenz():
    code, body = get('https://gdebenz.ru/api/stations?lat1=55.70&lon1=37.64&lat2=55.75&lon2=37.72')
    if code != 200: return {}, 'HTTP ' + str(code)
    return {str(x.get('osm_id')): x for x in json.loads(body)}, None

gde, gde_error = gdebenz()
for station in STATIONS:
    gde_row = gde.get(str(station['gdebenz_id']))
    gde_status = gde_error or ('not mapped' if not gde_row else f"overall={gde_row.get('status') or 'unknown'}; fuels_now={gde_row.get('fuels_now') or 'none'}")
    print(f"{station['priority']}. {station['station_name']}")
    print('   TutBenz: ' + tutbenz(station['tutbenz_id']))
    print('   Yandex:  ' + yandex(station['yandex_id']))
    print('   ГдеБЕНЗ: ' + gde_status)
    print('   T-Bank:  station endpoint not public; authenticated mobile-app flow (not queried)')
