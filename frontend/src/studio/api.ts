export class RequestError extends Error {status:number;constructor(message:string,status:number){super(message);this.status=status;}}
export async function request<T>(path:string,data?:unknown,idempotencyKey?:string):Promise<T>{
  const response=await fetch(`/api/studio${path}`,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json',...(idempotencyKey?{'Idempotency-Key':idempotencyKey}:{})},body:JSON.stringify(data)});
  if(!response.ok){let message=`Request failed (${response.status})`;try{const body=await response.json();message=typeof body.detail==='string'?body.detail:JSON.stringify(body.detail??body)}catch{/* retain status */}throw new RequestError(message,response.status)}
  return response.json() as Promise<T>;
}
