import { test } from 'node:test';
import assert from 'node:assert/strict';
import { controlAdvantage, hasPositiveWeights, recommendationLabel, shockEvidence } from '../src/diagnostics.ts';

test('conventional controls can outperform named worlds and are not hidden',()=>{
  const control={name:'Greedy nearest',verification:{valid:true,metrics:{meals_delivered:224}}};
  const named=[{verification:{valid:true,metrics:{meals_delivered:216}}},{verification:{valid:true,metrics:{meals_delivered:192}}}];
  assert.deepEqual(controlAdvantage([control],named),{name:'Greedy nearest',extra:8});
});
test('a tie is distinguished from no eligible plan',()=>{
  assert.equal(recommendationLabel({recommended_id:null,tied_ids:['velocity','equity']},[]),'Preference tie');
  assert.equal(recommendationLabel({recommended_id:null,tied_ids:[]},[]),'No eligible plan');
});
test('all-zero weights never meet submission requirements',()=>{
  assert.equal(hasPositiveWeights({coverage:0,equity:0,cost:0}),false);
  assert.equal(hasPositiveWeights({coverage:0,equity:.05,cost:0}),true);
});
test('shock evidence comes from the exact breakdown event and actual policy config',()=>{
  const world={policy_config:{reserve_ambient:32,reserve_chilled:0},events:[{kind:'breakdown',time:1500,vehicle_id:'A',stranded:{ambient:48,chilled:0}}],verification:{metrics:{meals_delivered:192}},unadapted_metrics:{meals_delivered:168}};
  assert.deepEqual(shockEvidence(world,{vehicle_id:'A',time:1500}),{stranded:48,reserve:32,recovered:24});
  assert.deepEqual(shockEvidence(world,{vehicle_id:'B',time:1500}),{stranded:null,reserve:32,recovered:24});
});
