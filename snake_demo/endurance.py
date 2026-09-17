"""Adaptive extension of the three guarded games that reached the main cap."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import json
from pathlib import Path
from .benchmark import episode,ROOT
from .controller import load_env
from .engine import LEVELS

def main():
    load_env(ROOT.parent/'.env')
    selected=[('open',103),('open',104),('classic',104)]
    jobs=[(level,controller,seed) for level,seed in selected for controller in ['jev_guarded','baseline']]
    out=ROOT/'records'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-endurance');out.mkdir()
    manifest={'model':'jev-1.13.0','pilot':False,'phase':'selected_endurance','seeds':[103,104],'levels':LEVELS,'jobs':jobs,'max_steps':600,'target':24,'starvation':50,'workers':3,
        'method':'Adaptive selected follow-up: replay initial seeds for the three guarded main games that reached eight foods. Fresh API calls, no copied actions or retries; 24-food and 600-move caps. Baseline paired on each selected board. Excluded from main estimates.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Saving',out,flush=True)
    summaries=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(episode,j,out,600,24,50) for j in jobs]
        for f in as_completed(futures):
            s=f.result();summaries.append(s);print(f'{len(summaries)}/6 {s["id"]}: food={s["score"]}, moves={s["moves"]}, {s["outcome"]}',flush=True)
    (out/'completion.json').write_text(json.dumps({'planned':6,'completed':len(summaries),'api_error_episodes':sum(s['outcome']=='api_error' for s in summaries)},indent=2)+'\n')
if __name__=='__main__':main()
