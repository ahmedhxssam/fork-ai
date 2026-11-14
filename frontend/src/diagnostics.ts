/** Presentation projections of persisted evidence; no planner behavior lives here. */
type VerifiedMeals={verification:{valid?:boolean;metrics:{meals_delivered:number}}};
export function controlAdvantage(controls:(VerifiedMeals&{name:string})[],worlds:VerifiedMeals[]){
  const validWorlds=worlds.filter(w=>w.verification.valid);
  if(!validWorlds.length)return null;
  const highestNamed=Math.max(...validWorlds.map(w=>w.verification.metrics.meals_delivered));
  const best=controls.filter(w=>w.verification.valid).sort((a,b)=>b.verification.metrics.meals_delivered-a.verification.metrics.meals_delivered)[0];
  return best&&best.verification.metrics.meals_delivered>highestNamed?{name:best.name,extra:best.verification.metrics.meals_delivered-highestNamed}:null;
}
export function recommendationLabel(comparison:{recommended_id:string|null;tied_ids?:string[]},worlds:{id:string;name:string}[]){
  if((comparison.tied_ids?.length??0)>1)return 'Preference tie';
  return worlds.find(w=>w.id===comparison.recommended_id)?.name??'No eligible plan';
}
export function hasPositiveWeights(weights:{coverage:number;equity:number;cost:number}){return weights.coverage+weights.equity+weights.cost>0}
function quantities(value:unknown):number|null{
  if(!value||typeof value!=='object'||Array.isArray(value))return null;
  const numbers=Object.values(value);return numbers.every(n=>typeof n==='number'&&Number.isFinite(n))?numbers.reduce<number>((a,n)=>a+(n as number),0):null;
}
export function shockEvidence(world:{policy_config:unknown;events:{kind:string;time:number;vehicle_id?:string;[key:string]:unknown}[];verification:{metrics:{meals_delivered:number}};unadapted_metrics?:{meals_delivered:number}},shock:{vehicle_id:string;time:number}){
  const event=world.events.find(e=>e.kind==='breakdown'&&e.vehicle_id===shock.vehicle_id&&e.time===shock.time);
  const config=world.policy_config as Record<string,unknown>|null;
  const ambient=config?.reserve_ambient,chilled=config?.reserve_chilled;
  return {stranded:quantities(event?.stranded),reserve:typeof ambient==='number'&&typeof chilled==='number'?ambient+chilled:null,recovered:world.unadapted_metrics?world.verification.metrics.meals_delivered-world.unadapted_metrics.meals_delivered:null};
}
