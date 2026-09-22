#!/usr/bin/env python3
"""Resilient monitor; looping is enabled only with --loop."""
import argparse,fcntl,json,logging,os,random,re,time,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
R=Path(__file__).resolve().parent;D=R/'data';S=D/'state.json';H=D/'health.json';L=D/'monitor.lock';E=D/'events.jsonl'; ST=json.loads((R/'station_mapping.json').read_text())['stations']; OK={'IN_STOCK','available','has','yes','queue','limit'}
def ts():return datetime.now(timezone.utc).isoformat()
def atom(p,x):
 p.parent.mkdir(exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,ensure_ascii=False));os.replace(q,p)
def load(p,d):
 try:return json.loads(p.read_text())
 except (OSError,json.JSONDecodeError):return d
log=logging.getLogger('fuel');log.setLevel(logging.INFO);D.mkdir(exist_ok=True);fh=RotatingFileHandler(D/'fuel-monitor.log',maxBytes=524288,backupCount=4);log.addHandler(fh)
def event(s,fuel,source,old,new):
 """Append transition history; rotate before it can consume Android storage."""
 try:
  if E.exists() and E.stat().st_size>=1048576:
   for i in range(6,0,-1):
    p=E.with_suffix(f'.jsonl.{i}');q=E.with_suffix(f'.jsonl.{i+1}')
    if p.exists():p.replace(q)
   E.replace(E.with_suffix('.jsonl.1'))
  with E.open('a',encoding='utf8')as f:f.write(json.dumps({'at':ts(),'station':s['station_name'],'address':s.get('address'),'fuel':fuel,'source':source,'old_status':old,'new_status':new,'available':new in OK},ensure_ascii=False)+'\n')
 except OSError as e:log.error('event write %s',e)
def get(u,method='GET',data=None):
 q=urllib.request.Request(u,data=data,method=method,headers={'User-Agent':'fuel-monitor/2','Accept':'application/json,text/html'})
 for n in range(3):
  try:
   with urllib.request.urlopen(q,timeout=20) as r:return r.read().decode('utf8','replace')
  except urllib.error.HTTPError as e:
   if e.code in(403,429):raise RuntimeError(f'HTTP {e.code} rate/access limit')
   if n==2:raise
  except Exception:
   if n==2:raise
  time.sleep(2**n+random.random())
def source(s,name,gde):
 if name=='tutbenz':
  if not s.get('tutbenz_id'):return[]
  j=json.loads(get('https://tutbenz.app/api/stations/'+s['tutbenz_id']));return[(x['fuelType'],x.get('status'))for x in j.get('states',[])if x.get('fuelType')in('ai95','ai95_plus','ai95premium')]
 if name=='yandex':
  b=get('https://yandex.ru/maps/org/x/'+s['yandex_id']+'/');m=re.search(r'"fuel":(\[\{.*?\}\]),"status"',b)
  if not m:raise ValueError('fuel block missing')
  return[('ai95'if x['fuelType']=='AI95'else'ai95_premium',x.get('status'))for x in json.loads(m.group(1))if x.get('fuelType')in('AI95','AI95_PREMIUM')]
 x=gde.get(str(s.get('gdebenz_id')));return[]if not x else[('ai95','yes'if'95'in(x.get('fuels_now')or'').split(',')else'unknown')]
def push(t,m,p=0):
 tok=os.getenv('PUSHOVER_TOKEN');usr=os.getenv('PUSHOVER_USER_KEY')
 if not(tok and usr):raise RuntimeError('Pushover secrets missing')
 get('https://api.pushover.net/1/messages.json','POST',urllib.parse.urlencode({'token':tok,'user':usr,'title':t,'message':m,'priority':p}).encode())
def format_notification(s,fuel,sources,queue='нет данных',updated=None):
 """Shared formatter for preview and production; T-Bank via TutBenz is excluded."""
 def status(name):
  x=next((v for f,v in sources.get(name,[]) if f==fuel),None)
  return 'есть' if x in OK else ('нет' if x in ('OUT_OF_STOCK','no') else 'нет данных')
 y,t,g=status('yandex'),status('tutbenz'),status('gdebenz'); confirmations=sum(x=='есть' for x in (y,t,g)); conflict=y=='нет' and t=='есть'; label='АИ-95+' if fuel=='ai95_premium' else 'АИ-95'
 icon={'нет':'🟢','средняя':'🟡','большая':'🔴'}.get(queue,'⚪️')
 title=(f'⚠️ ×{confirmations} {label} · конфликт · {icon}' if conflict else f'✅ ×{confirmations} {label} появился · {icon}')
 name=s['station_name']
 return title, f"{name}\n\nTutBenz: {t}\nЯндекс: {y}\nГдеБЕНЗ: {g}\n\nОбновлено: {updated or datetime.now().astimezone().strftime('%H:%M')}"
def yandex_queue(s):
 """Explicit queue field only; never infer a queue from fuel availability."""
 b=get('https://yandex.ru/maps/org/x/'+s['yandex_id']+'/');m=re.search(r'"queueStatus":"([^"]*)"',b)
 return {'LOW':'нет','MEDIUM':'средняя','HIGH':'большая'}.get(m.group(1) if m else '', 'нет данных')
def run(state,health,test=False):
 health['last_cycle_started_at']=ts();gde={};results={}
 try:gde={str(x.get('osm_id')):x for x in json.loads(get('https://gdebenz.ru/api/stations?lat1=55.70&lon1=37.64&lat2=55.75&lon2=37.72'))}
 except Exception as e:health.setdefault('source_errors',{})['gdebenz_map']=str(e);log.warning('gde map %s',e)
 first=not state.get('statuses');notes=[]
 for s in ST:
  for n in('tutbenz','yandex','gdebenz'):
   try:
    vals=source(s,n,gde);results.setdefault(s['station_name'],{})[n]=vals;health.setdefault('source_errors',{})[n]=0;health['last_successful_source_check']=ts()
    for f,new in vals:
     k='|'.join((s['station_name'],f,n));old=state.setdefault('statuses',{}).get(k,'unknown');state['statuses'][k]=new
     if old!=new:event(s,f,n,old,new)
     if not first and old not in OK and new in OK:notes.append((s,f,n,old,new))
     if old in OK and new not in OK:log.info('unavailable %s %s %s',s['station_name'],f,n)
   except Exception as e:health.setdefault('source_errors',{})[n]=health.get('source_errors',{}).get(n,0)+1;log.warning('%s %s: %s',n,s['station_name'],e)
 if test:notes.append(({'station_name':'Fuel monitor test','address':''},'ai95','Pushover','unknown','available'))
 for s,f,n,o,new in notes:
  try:q=yandex_queue(s)
  except Exception as e:log.warning('queue %s: %s',s['station_name'],e);q='нет данных'
  title,m=format_notification(s,f,results.get(s['station_name'],{}),q)
  try:push(title,m,1 if s.get('priority')==1 else 0)
  except Exception as e:state.setdefault('pending_notifications',[]).append(m);log.warning('push pending %s',e)
 health['last_cycle_finished_at']=ts();health['last_successful_full_cycle']=ts()if results else health.get('last_successful_full_cycle');health['next_check_at']=time.time()+random.randint(480,720);atom(S,state);atom(H,health)
def main():
 p=argparse.ArgumentParser();p.add_argument('--loop',action='store_true');p.add_argument('--test-push',action='store_true');a=p.parse_args()
 with L.open('w')as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:return 1
  s=load(S,{'statuses':{},'pending_notifications':[]});h=load(H,{'started_at':ts(),'source_errors':{}})
  while True:
   try:run(s,h,a.test_push)
   except Exception as e:log.exception('cycle %s',e);h['last_cycle_error']=str(e);atom(H,h)
   if not a.loop:return 0
   time.sleep(random.randint(480,720))
if __name__=='__main__':main()
