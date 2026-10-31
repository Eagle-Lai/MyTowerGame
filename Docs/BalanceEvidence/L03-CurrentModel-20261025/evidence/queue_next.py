from search import *
name=sys.argv[1];nextpath=sys.argv[2]
deadline=time.monotonic()+1800
while time.monotonic()<deadline:
    p=OUT/name/'status.json'
    if p.exists() and json.loads(p.read_text()).get('phase') in ['complete','exception','cancelled','batch_timeout']:
        time.sleep(5)
        print(start(nextpath),flush=True);break
    time.sleep(3)
