"""One approved, bounded call. Credentials remain inside this process."""
import datetime as dt
import json
import os
import pathlib
import time
import urllib.request
import urllib.error
from continuation import prepare, validate

MODEL='nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B'
CATALOG='https://tokenfactory.nebius.com/api/public/models_info'
ENDPOINT='https://api.tokenfactory.nebius.com/v1/chat/completions'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def run(state, directory):
    directory=pathlib.Path(directory); directory.mkdir(exist_ok=True)
    marker=directory/'NEMOTRON_SINGLE_CALL.claim'
    output=directory/'NEMOTRON_CONTINUATION_LIVE.json'
    if marker.exists(): raise ValueError('Approved call already consumed; no retry permitted')
    request=prepare(state)
    payload={'model':MODEL,'messages':request['messages'],'temperature':0,
             'max_tokens':350,'stream':False,'chat_template_kwargs':{'enable_thinking':False}}
    data=json.dumps(payload,ensure_ascii=False).encode()
    if len(data)>12000: raise ValueError('Input exceeds approved bound')
    opener=urllib.request.build_opener(NoRedirect)
    with opener.open(CATALOG,timeout=30) as r: catalog=json.load(r)
    flavors=[f for model in catalog for f in model.get('flavors',[]) if f.get('model_id')==MODEL]
    if len(flavors)!=1: raise ValueError('Exact existing model price unavailable')
    f=flavors[0]; ip=float(f['input_price_per_million_tokens']); op=float(f['output_price_per_million_tokens'])
    # Byte upper bound plus generous chat framing allowance; output cap includes generation.
    input_bound=len(data)+4096
    ceiling=(input_bound*ip+350*op)/1_000_000
    if ip<0 or op<0 or not ceiling<0.01: raise ValueError('Cost preflight rejected')
    # Use the existing privately configured account. Never log, persist or return this value.
    key=os.environ.get('NEBIUS_API_KEY')
    if not key:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as registry:
            key=winreg.QueryValueEx(registry,'NEBIUS_API_KEY')[0]
    if not key: raise ValueError('Existing account credential unavailable')
    artifact={'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'model_requested':MODEL,'request':payload,'state':state,
              'approval':{'max_calls':1,'max_usd':1,'max_output_tokens':350},
              'pricing':{'source':CATALOG,'input_per_million_usd':ip,'output_per_million_usd':op,
                         'conservative_input_token_bound':input_bound,'calculated_upper_usd':ceiling},
              'status':'STARTED','attempts':1,'retry_allowed':False}
    def save(): output.write_text(json.dumps(artifact,ensure_ascii=False,indent=2),encoding='utf-8')
    # Exclusive on-disk claim survives crashes and prevents accidental second charge.
    with marker.open('x',encoding='utf-8') as claim: claim.write(artifact['started_utc'])
    save(); started=time.perf_counter()
    try:
        req=urllib.request.Request(ENDPOINT,data=data,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        with opener.open(req,timeout=90) as response:
            artifact['http_status']=response.status
            body=json.load(response)
        artifact['provider_response']=body
        artifact['latency_ms']=round((time.perf_counter()-started)*1000,2)
        usage=body.get('usage',{}); artifact['usage']=usage
        if isinstance(usage.get('prompt_tokens'),int) and isinstance(usage.get('completion_tokens'),int):
            artifact['calculated_usage_cost_usd']=(usage['prompt_tokens']*ip+usage['completion_tokens']*op)/1_000_000
        artifact['billing_note']='Calculated from provider token usage and public price; not an invoice settlement.'
        save()  # Preserve response and usage even if validation fails.
        choice=body['choices'][0]
        if choice.get('finish_reason')!='stop': raise ValueError('Output did not complete normally')
        artifact['answer']=validate(choice['message']['content'],request)
        artifact['status']='RESPONSE_VALIDATED'
    except urllib.error.HTTPError as exc:
        artifact['status']='FAIL'; artifact['http_status']=exc.code
        artifact['failure']='Provider HTTP error; no retry. Response headers and credentials omitted.'
    except Exception as exc:
        artifact['status']='FAIL'; artifact['failure_type']=type(exc).__name__
        artifact['failure']='Transport, parsing or validation failed; inspect preserved response. No retry.'
    finally:
        key=None; artifact['finished_utc']=dt.datetime.now(dt.timezone.utc).isoformat(); save()
    return artifact
