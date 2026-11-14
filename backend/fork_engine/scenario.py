"""Published synthetic fixture; no historical or operational data."""
import hashlib
import json
import math
import random


def create_scenario(seed: int = 26) -> dict:
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    nodes = []
    def node(id, name, x, y, kind='junction', demand=0, commodity='ambient', priority=0, window_start=0, window_end=14400, due=14400, service_seconds=0):
        nodes.append(dict(id=id,name=name,x=x,y=y,kind=kind,demand=demand,commodity=commodity,priority=priority,window_start=window_start,window_end=window_end,due=due,service_seconds=service_seconds))
    node('depot','Riverton Food Hub',480,340,'depot')
    for id,x,y in [('west',280,340),('east',700,340),('north',480,150),('south',480,540)]:
        node(id,id.title()+' Junction',x,y)
    sites=[('maple','Maple Centre',140,180,24,'ambient',1,2600,'west'),('river','River House',140,420,24,'ambient',2,3300,'west'),('cedar','Cedar Hall',230,590,24,'ambient',3,4800,'south'),('oak','Oak Pantry',350,90,24,'ambient',1,2700,'north'),('hill','Hill Community',630,80,24,'ambient',3,3000,'north'),('harbor','Harbor Centre',870,170,24,'ambient',2,3600,'east'),('garden','Garden Kitchen',890,440,24,'ambient',1,4200,'east'),('park','Park Shelter',750,590,24,'ambient',3,4600,'south'),('station','Station Pantry',380,660,24,'ambient',2,5300,'south'),('clinic','Clinic Meal Hub',570,230,16,'chilled',3,2000,'north'),('spruce','Spruce Centre',800,280,16,'chilled',2,3300,'east'),('linden','Linden House',580,630,16,'chilled',3,4800,'south')]
    connections=[('depot','west'),('depot','east'),('depot','north'),('depot','south'),('west','north'),('north','east'),('east','south'),('south','west')]
    for id,name,x,y,d,c,p,due,junction in sites:
        node(id,name,x,y,'destination',d,c,p,0,min(11000,due+3000),due,180+rng.choice([0,60,120]))
        connections.append((junction,id))
    by={n['id']:n for n in nodes}
    edges=[]
    for a,b in connections:
        distance=int(round(math.hypot(by[a]['x']-by[b]['x'],by[a]['y']-by[b]['y'])*9))
        for source,target in [(a,b),(b,a)]:
            edges.append(dict(id=f'{source}>{target}',source=source,target=target,distance_m=distance,seconds=math.ceil(distance/7)+35))
    vehicles=[dict(id='A',name='Atlas Van',capacity=100,chilled=False,cost_per_km=85,emissions_per_km=230,driver_id='v1',shift_start=0,shift_end=10800,color='#74e5c0'),dict(id='B',name='Birch Cargo',capacity=60,chilled=False,cost_per_km=48,emissions_per_km=95,driver_id='v2',shift_start=0,shift_end=9000,color='#ffc46b'),dict(id='C',name='Cobalt Cold Van',capacity=80,chilled=True,cost_per_km=110,emissions_per_km=280,driver_id='v3',shift_start=0,shift_end=12000,color='#aab3ff')]
    s=dict(id=f'riverton-{seed}',name='Riverton Meal Mission',seed=seed,start_time='09:00',horizon=14400,inventory={'ambient':192,'chilled':48},nodes=nodes,edges=edges,depot_id='depot',vehicles=vehicles,volunteers=[dict(id=v['driver_id'],name=f'Volunteer {i+1}',vehicle_id=v['id'],shift_start=v['shift_start'],shift_end=v['shift_end']) for i,v in enumerate(vehicles)],assumptions=['Entire scenario, names, priorities and coefficients are synthetic.','Each order is indivisible; loading takes 120 seconds. Initial routes make one trip; recovery permits at most one depot reload per healthy vehicle.','Cold-chain is vehicle compatibility only; no food-safety certification claim.','Roads are directed; shortest travel-time paths are used. Vehicles must return before their original shifts end.','Cost is distance × cents/km; emissions are distance × grams CO2e/km, rounded per vehicle. No fixed or service costs are modeled.','Planning wall time does not advance scenario time. Failed cargo is stranded without rescue or transfer.'])
    s['hash']=hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return s
