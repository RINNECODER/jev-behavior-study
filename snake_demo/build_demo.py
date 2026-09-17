"""Rebuild verified main replays plus separately labeled selected endurance runs."""
import json
from .analyze import analyze,ROOT
MAIN=ROOT/'records'/'20260917T013832Z-benchmark'
ENDURANCE=ROOT/'records'/'20260917T014718Z-endurance'
PILOT=ROOT/'records'/'20260917T013629Z-pilot'

def bundle():return json.loads((ROOT/'web'/'data.js').read_text().removeprefix('window.SNAKE_DATA = ').removesuffix(';\n'))
def main():
    analyze(PILOT,False)
    analyze(ENDURANCE);extra=bundle()
    analyze(MAIN);base=bundle()
    for game in base['runs']:game['phase']='main'
    for game in extra['runs']:
        game['id']='endurance-'+game['id'];game['phase']='endurance';base['runs'].append(game)
    base['extended_episodes']=extra['episodes'];base['extended_model_calls']=extra['model_calls'];base['extended_run']=extra['run']
    (ROOT/'web'/'data.js').write_text('window.SNAKE_DATA = '+json.dumps(base,separators=(',',':'))+';\n')
    print('Exported 96 main games plus six explicitly labeled selected endurance games.')
if __name__=='__main__':main()
