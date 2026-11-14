# FORK implementation contract

Scenario time is **elapsed integer seconds since 09:00**; horizon 14400.
Quantities are integer meals; distance metres; money cents; emissions grams CO2e.
All data is synthetic. All worlds use the identical scenario hash and constraints.

## Ownership

- Engine worker: `backend/fork_engine/` except `verifier.py`; `tests/test_engine.py`.
- Verifier worker: `backend/fork_engine/verifier.py`, `tests/test_verifier.py`.
- Frontend worker: `frontend/` exclusively.
- Root: API, persistence, integration, agent adapter, docs, infrastructure, E2E.
Workers do not commit or modify shared configuration without coordination.

## Python interfaces (plain JSON-compatible dictionaries)

`from backend.fork_engine.scenario import create_scenario`
`create_scenario(seed: int = 26) -> dict`

Scenario fields: `id`, `name`, `seed`, `hash`, `start_time` ("09:00"),
`horizon` (14400), `inventory` ({ambient:192,chilled:48}), `nodes`, `edges`,
`depot_id` ("depot"), `vehicles`, `volunteers`, `assumptions`.
Nodes: `{id,name,x,y,kind:"depot"|"destination"|"junction",demand,commodity,
priority,window_start,window_end,due,service_seconds}`. Demand zero for junctions.
Coordinates use a 1000×700 viewBox. Edges `{id,source,target,distance_m,seconds}`.
Vehicles: `{id:"A"|"B"|"C",name,capacity,chilled,cost_per_km,emissions_per_km,
driver_id,shift_start,shift_end,color}`. Cost/emission coefficients in cents/grams.
Volunteers: `{id,name,vehicle_id,shift_start,shift_end}`. Synthetic names only.

`from backend.fork_engine.planner import plan_world`
`plan_world(scenario: dict, policy: str, policy_config: dict | None = None) -> dict`
Policies exactly `velocity`, `resilience`, `equity`.

`from backend.fork_engine.simulation import simulate_world`
`simulate_world(scenario: dict, plan: dict, disruption: dict | None = None,
                adapt: bool = True) -> dict`
Disruption `{vehicle_id:"A"|"B"|"C",time:int}`. Same resource/time across worlds.

Result fields: `id` (policy), `policy`, `name` (Velocity/Resilience/Equity),
`initial_hash`, `plan`, `trajectories`, `deliveries`, `events`, `final_state`,
`metrics`, `solver`, `policy_config`, `mode` ("deterministic").
Engine may add fields. All output must be JSON serializable, stable ordering.

Plan: `routes` list each `{vehicle_id,stops:[destination_id,...],...}` and manifests,
`policy`, `policy_config`, `solver` (actual algorithm/status/budget), `initial_hash`.

Trajectory: `{vehicle_id,from_id,to_id,depart,arrive,path:[[x,y],...],distance_m,
revision}`. Partial final leg ends at actual failure time/position with actual
travelled metres; not a trip to the original target. No teleportation.
Delivery: `{id,destination_id,vehicle_id,quantity,commodity,service_start,
completed_at,priority,on_time}`; only completed transfers appear here.
Event: `{id,seq,time,kind,vehicle_id?,node_id?,quantity?,commodity?,summary,...}`.
Kinds include `load`, `depart`, `arrive`, `service_start`, `delivery`, `return`,
`breakdown`, `replan`, `plan_accepted`, `horizon`. Add physical ledger values.
Final state: `{depot_inventory:{ambient,chilled},onboard:{A:{ambient,chilled},...},
stranded:{ambient,chilled},delivered:{ambient,chilled},vehicles:{...}}`.

Metrics: `{meals_delivered,demand,coverage,on_time_meals,on_time_coverage,
priority_coverage,priority_weighted_coverage,destinations_served,late_deliveries,
unserved_meals,distance_m,cost_cents,emissions_g,violations}`.
Fractions in [0,1]; priority_coverage uses priority=3 orders; denominator ALL demand
for coverage/on-time. Sim service completion <=due is on-time. Hard window end
and shift end apply to service completion/required return. Physical validity is
separate from demand satisfaction.

`from backend.fork_engine.verifier import verify_world`
`verify_world(scenario: dict, result: dict) -> dict`
Receipt `{valid:bool,violations:[{code,message,event_id?}],metrics:dict,
checks:[{id,label,passed,detail}],scenario_hash,event_hash,verified_at?,version}`.
Verifier must independently reconstruct resource and movement evidence rather
than trusting result.metrics. Avoid importing planner/simulation validation logic.

## Recovery restrictions

Atomic deliveries and loads; interrupted service does not complete. Complete old
events at exact t before breakdown. Failed vehicle cargo is stranded; unfinished
loading is cancelled with stock still at depot. Healthy ongoing edges/services
are locked until actual ready time. Exclude their pending completed orders from
residual planning and subtract cargo in projected readiness only. No rescue or
cross-vehicle transfer. One explicitly timed depot reload per healthy vehicle is
allowed. Joint commodity stock grants and load limits are enforced. Onboard cargo
may fulfill another compatible unfulfilled order; unused cargo remains occupancy.
Required return is waived only for failed stranded vehicles. No predetermined winner.

## Frontend API

`GET /api/scenario` -> scenario.
`POST /api/experiments` body `{seed?:26}` -> Experiment.
`GET /api/experiments/{id}` -> Experiment.
`POST /api/experiments/{id}/disrupt` body `{vehicle_id,time}` -> Experiment.
`POST /api/experiments/{id}/preferences` body `{coverage,equity,cost}` weights 0..1
-> comparison (frontend may also preview preference ranking locally).
`POST /api/experiments/{id}/approve` body `{world_id,revision}` -> Decision.
`GET /api/experiments/{id}/export?world_id=...&format=json|csv` -> approved artifact.

Experiment `{id,scenario,worlds:[Result + {verification,baseline_metrics?,
unadapted_metrics?}],disruption:null|{vehicle_id,time},comparison,mode,
created_at,revision,activity:[],baseline_worlds?:[],approved?:Decision}`.
Comparison `{recommended_id,pareto_ids:[],scores:{},weights:{coverage,equity,cost},
explanation,eligible_ids:[]}`. Verification metrics are authoritative.
Decision `{id,world_id,experiment_id,revision,approved_at,label}`.
API failures `{detail:string}` with meaningful HTTP status. API base same origin,
Vite proxies /api to localhost:8000. Backend later serves frontend/dist.

UI operates as synchronized event playback of actually computed results. Never
invent live LLM activity. Three maps, timeline, shock selector, baseline/delta,
counterfactual no-replan recovery gain, preference-sensitive recommendation,
inspectable verification, approval/export and reset are required journey.
