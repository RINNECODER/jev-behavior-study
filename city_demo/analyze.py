"""Rebuild pilot summaries and exact per-question usage from immutable run traces."""
from pathlib import Path
import csv
import json
import statistics
import hashlib

ROOT = Path(__file__).resolve().parent

def analyze(folder):
    manifest = json.loads((folder / 'manifest.json').read_text())
    source = folder / 'source' if (folder / 'source').exists() else ROOT
    for name, expected in manifest['hashes'].items():
        assert hashlib.sha256((source / name).read_bytes()).hexdigest() == expected, 'Source changed: ' + name
    rows, calls, index = [], [], []
    for config in manifest['episodes']:
        name = '-'.join(config[k] for k in ['challenge', 'driver', 'timing'])
        path = folder / (name + '.json')
        if not path.exists():
            continue
        d = json.loads(path.read_text())
        assert d['config'] == config
        f = d['final']
        assert all(len(c['payload']['questions']) == 1 for r in d['decisions'] for c in r['result']['calls'])
        for decision in d['decisions']:
            if config['timing'] == 'paused':
                assert decision['observation_age_s'] == 0
            for c in decision['result']['calls']:
                q = next(iter(c['payload']['questions']))
                response = c.get('response', {})
                usage = response.get('usage', {})
                calls.append({'run': name, 'question': q, 'decision': decision['index'], 'valid': c['valid'],
                  'choice': response.get('answers', {}).get(q, {}).get('choice'),
                  'input_tokens': usage.get('input_tokens'), 'output_tokens': usage.get('output_tokens'),
                  'latency_ms': c['latency_ms'], 'observation_age_s': decision['observation_age_s']})
        rows.append({'run': name, 'status': f['status'], 'sim_seconds': f['t'], 'distance_m': round(f['distance'], 2),
          'stops': f['stops'], 'collisions': f['collisions'], 'red_lights': f['redLights'],
          'speeding_seconds': round(f['speedingSeconds'], 2), 'intersections': len(f['visited']),
          'clean_completion': f['status'] == 'completed' and f['redLights'] == 0 and f['speedingSeconds'] == 0,
          'decisions': len(d['decisions']), 'median_observation_age_s': statistics.median(r['observation_age_s'] for r in d['decisions']),
          'events': d['events']})
        index.append({'path': str(path.relative_to(ROOT)), 'label': f"{folder.name} · {name} · {f['status']}"})
    groups = {}
    for question in sorted(set(r['question'] for r in calls)):
        subset = [r for r in calls if r['question'] == question]
        measured = [r for r in subset if r['input_tokens'] is not None and r['output_tokens'] is not None]
        groups[question] = {'calls': len(subset), 'valid': sum(r['valid'] for r in subset), 'measured_usage': len(measured),
          'input_tokens_per_question_mean': statistics.mean(r['input_tokens'] for r in measured) if measured else None,
          'output_tokens_per_question_mean': statistics.mean(r['output_tokens'] for r in measured) if measured else None,
          'median_latency_ms': statistics.median(r['latency_ms'] for r in subset)}
    result = {'episodes': len(rows), 'complete_matrix': len(rows) == len(manifest['episodes']), 'runs': rows, 'per_question': groups,
      'calls': len(calls), 'valid_calls': sum(r['valid'] for r in calls)}
    (folder / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    if calls:
        with (folder / 'per-question.csv').open('w') as f:
            writer = csv.DictWriter(f, fieldnames=list(calls[0]), lineterminator='\n');writer.writeheader();writer.writerows(calls)
    return index, result

if __name__ == '__main__':
    index = []
    for name in ['pilot-v2', 'pilot-v1']:
        folder = ROOT / 'records' / name
        if folder.exists():
            entries, result = analyze(folder);index.extend(entries)
            print(name, result['episodes'], 'episodes;', result['calls'], 'calls;', result['valid_calls'], 'valid')
    (ROOT / 'records' / 'index.json').write_text(json.dumps(index, indent=2) + '\n')
