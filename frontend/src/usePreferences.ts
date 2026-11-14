import { useRef, useState } from 'react';
import type { Experiment, Weights } from './types';
import { api } from './model';
import { hasPositiveWeights } from './diagnostics';

const initial:Weights={coverage:.55,equity:.35,cost:.1};
const same=(a:Weights,b:Weights)=>Object.keys(initial).every(key=>Math.abs(a[key as keyof Weights]-b[key as keyof Weights])<1e-9);

/** A single writer: subsequent saves replace the queued desired snapshot.
 * Approval is allowed only after GET confirms the latest desired preferences.
 */
export function usePreferences(onAcknowledge:(experiment:Experiment)=>void){
  const [weights,setWeights]=useState<Weights>(initial);
  const [pending,setPending]=useState(false),[dirty,setDirty]=useState(false),[error,setError]=useState(''),[reverting,setReverting]=useState(false);
  const desired=useRef(initial),acknowledged=useRef<Experiment|null>(null);
  const version=useRef(0),running=useRef(false);
  const queued=useRef<{weights:Weights;version:number}|null>(null);

  function initialize(experiment:Experiment|null){
    acknowledged.current=experiment;const values=experiment?.comparison.weights??initial;
    desired.current=values;setWeights(values);version.current++;queued.current=null;
    setDirty(false);setError('');
  }
  function edit(next:Weights){
    desired.current=next;setWeights(next);version.current++;
    setDirty(!acknowledged.current||!same(next,acknowledged.current.comparison.weights));
    // A newer invalid edit cancels queued work, never the already-started write.
    if(!hasPositiveWeights(next))queued.current=null;
  }
  async function drain(){
    if(running.current)return;
    running.current=true;setPending(true);
    try{
      while(queued.current){
        const request=queued.current;queued.current=null;
        const current=acknowledged.current;
        if(!current||!hasPositiveWeights(request.weights))continue;
        try{
          await api(`/experiments/${current.id}/preferences`,request.weights);
          const fresh=await api<Experiment>(`/experiments/${current.id}`);
          acknowledged.current=fresh;onAcknowledge(fresh);setError('');
          if(version.current===request.version){
            desired.current=fresh.comparison.weights;setWeights(fresh.comparison.weights);setDirty(false);
          }else setDirty(!same(desired.current,fresh.comparison.weights));
        }catch(cause){
          // The server might have accepted a POST whose response was lost.
          // Retain dirty state and require retry or a fresh GET before reverting.
          setError((cause as Error).message);setDirty(true);queued.current=null;break;
        }
      }
    }finally{running.current=false;setPending(false)}
  }
  function save(){
    if(!hasPositiveWeights(desired.current)){queued.current=null;return}
    queued.current={weights:{...desired.current},version:version.current};
    void drain();
  }
  async function revert(){
    const current=acknowledged.current;if(!current||running.current)return;
    running.current=true;setPending(true);setReverting(true);
    try{
      const fresh=await api<Experiment>(`/experiments/${current.id}`);
      onAcknowledge(fresh);initialize(fresh);
    }catch(cause){setError((cause as Error).message);setDirty(true)}
    finally{running.current=false;setPending(false);setReverting(false)}
  }
  const ready=!!acknowledged.current&&hasPositiveWeights(weights)&&!pending&&!dirty&&!error&&same(weights,acknowledged.current.comparison.weights);
  const message=!hasPositiveWeights(weights)?'Choose at least one priority above zero. Approval and export are blocked.':error?`Preferences could not be saved: ${error}`:reverting?'Loading saved preferences. Approval and export are blocked.':pending?'Saving preferences. Approval and export are blocked.':dirty?'Preferences are unsaved. Save or revert before approval and export.':'Preferences saved';
  return {weights,pending,reverting,dirty,error,ready,message,initialize,edit,save,revert};
}
