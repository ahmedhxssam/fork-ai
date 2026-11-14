import type { Scenario, Trajectory, World } from './types';
export const clock = (t:number) => `${String(9+Math.floor(t/3600)).padStart(2,'0')}:${String(Math.floor(t%3600/60)).padStart(2,'0')}`;
export const pct = (n:number) => `${Math.round(n*100)}%`;
export const dollars = (n:number) => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:2,maximumFractionDigits:2}).format(n/100);
export const metric = (w:Pick<World,'verification'|'metrics'>) => w.verification?.metrics ?? w.metrics;
export const sum = (obj:Record<string,number>|undefined) => Object.values(obj ?? {}).reduce((a,b)=>a+b,0);
export function pointOnPath(path:number[][], fraction:number):number[] {
  if (!path.length) return [0,0];
  const lengths=path.slice(1).map((p,i)=>Math.hypot(p[0]-path[i][0],p[1]-path[i][1]));
  let remaining=lengths.reduce((a,b)=>a+b,0)*Math.max(0,Math.min(1,fraction));
  for(let i=0;i<lengths.length;i++){ if(remaining<=lengths[i]){const k=lengths[i]?remaining/lengths[i]:0;return [path[i][0]+(path[i+1][0]-path[i][0])*k,path[i][1]+(path[i+1][1]-path[i][1])*k]} remaining-=lengths[i] }
  return path[path.length-1];
}
export function vehiclePoint(world:World, vehicle:string, time:number, scenario:Scenario):number[] {
  const depot=scenario.nodes.find(n=>n.id===scenario.depot_id)!;
  let position=[depot.x,depot.y];
  for(const leg of world.trajectories.filter(t=>t.vehicle_id===vehicle).sort((a,b)=>a.depart-b.depart)) {
    if(time<leg.depart)break;
    if(time>=leg.arrive){ position=leg.path.at(-1) ?? position;continue }
    return pointOnPath(leg.path,(time-leg.depart)/(leg.arrive-leg.depart));
  }
  return position;
}
export const pathString = (leg:Trajectory) => leg.path.map(p=>p.join(',')).join(' ');
export class ApiError extends Error {
  constructor(message:string,readonly status:number){super(message);this.name='ApiError'}
}
export async function api<T>(path:string, body?:unknown):Promise<T> {
  const response=await fetch(`/api${path}`,body===undefined?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!response.ok){const data=await response.json().catch(()=>({detail:`HTTP ${response.status}`}));throw new ApiError(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail),response.status)}
  return response.json();
}
export function custodyAt(world:World, scenario:Scenario, time:number){
  const depot={...scenario.inventory};const onboard=Object.fromEntries(scenario.vehicles.map(v=>[v.id,{ambient:0,chilled:0}])) as Record<string,Record<string,number>>;let stranded=0;
  for(const event of world.events){
    if(event.time>time)break;
    const cargo=event.vehicle_id?onboard[event.vehicle_id]:undefined;
    if(event.kind==='load'&&cargo){for(const [commodity,quantity] of Object.entries(event.manifest as Record<string,number>)){depot[commodity]-=quantity;cargo[commodity]=(cargo[commodity]??0)+quantity}}
    if(event.kind==='delivery'&&cargo&&event.commodity){cargo[event.commodity]-=event.quantity??0}
    if(event.kind==='breakdown'&&cargo){stranded+=sum(cargo);for(const commodity of Object.keys(cargo))cargo[commodity]=0}
  }
  return {depot:sum(depot),onboard:Object.values(onboard).reduce((a,c)=>a+sum(c),0),stranded};
}
export function traceUntil(leg:Trajectory,time:number):string {
  const fraction=Math.max(0,Math.min(1,(time-leg.depart)/(leg.arrive-leg.depart||1)));
  if(fraction>=1)return pathString(leg);
  const lengths=leg.path.slice(1).map((p,i)=>Math.hypot(p[0]-leg.path[i][0],p[1]-leg.path[i][1]));
  let left=lengths.reduce((a,b)=>a+b,0)*fraction;
  const points=[leg.path[0]];
  for(let i=0;i<lengths.length;i++){if(left<lengths[i])break;points.push(leg.path[i+1]);left-=lengths[i]}
  points.push(pointOnPath(leg.path,fraction));return points.map(p=>p.join(',')).join(' ');
}
