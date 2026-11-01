"""The original one-dimensional generator, with explicit public parameters."""
import hashlib
import json
import math
import random
from .prompts import ROOT

REPLAY_ABS_TOL = 1e-14


def stable_seed(seed, scenario, stream):
    return int.from_bytes(hashlib.sha256(f'{seed}|{scenario}|{stream}'.encode()).digest()[:8], 'big')


def generate(protocol, scenario, seed):
    steps = protocol['budget']['steps']
    sid, params = scenario['id'], scenario['parameters']
    rng = random.Random(stable_seed(seed, sid, 'latent'))
    polarity = 1 if seed % 2 == 0 else -1
    if sid == 'stable':
        latent = [polarity * params['amplitude']] * steps
    elif sid == 'null':
        latent = [0.0] * steps
    elif sid == 'walk':
        latent = [polarity * params['initial_amplitude']]
        for _ in range(1, steps):
            latent.append(latent[-1] + rng.gauss(0, params['innovation_sd']))
    elif sid == 'abrupt':
        latent = [polarity * params['amplitude'] * (-1) ** sum(t >= event for event in params['flip_steps']) for t in range(steps)]
    elif sid == 'iid':
        latent = [params['amplitude'] * (1 if rng.random() < .5 else -1) for _ in range(steps)]
    else:
        raise ValueError('Unknown scenario')
    noise = random.Random(stable_seed(seed, sid, 'noise'))
    observed = [v + noise.gauss(0, protocol['observation']['noise_sd']) for v in latent]
    alpha = protocol['estimators']['ema']['alpha']
    memory = [observed[0]]
    for v in observed[1:]:
        memory.append((1 - alpha) * memory[-1] + alpha * v)
    labels = {'stable': '変わらない信号', 'null': '信号なし', 'walk': 'ゆっくり漂う', 'abrupt': '急な反転', 'iid': '毎回入れ替わる'}
    return {'id': sid, 'label': labels[sid], 'seed': seed, 'latent': latent, 'observation': observed, 'memory': memory}


def compare_portable_trace(actual, reference, thresholds):
    series = ('latent', 'observation', 'memory')
    if actual.keys() != reference.keys() or any(actual[k] != reference[k] for k in actual.keys() - set(series)):
        raise ValueError('Rebuilt scenario metadata differs')
    largest_delta = 0.0
    for name in series:
        for index, (a, b) in enumerate(zip(actual[name], reference[name], strict=True)):
            delta = abs(a - b)
            if not math.isfinite(delta) or delta > REPLAY_ABS_TOL:
                raise ValueError(f"{actual['id']} {name}[{index}] absolute difference {delta!r}")
            largest_delta = max(largest_delta, delta)
            if a == b:
                continue
            if name == 'latent':
                changed = ((a > 0) - (a < 0)) != ((b > 0) - (b < 0))
            else:
                changed = (a >= 0) != (b >= 0) or any((abs(a) >= t) != (abs(b) >= t) for t in thresholds)
            if changed:
                raise ValueError(f"{actual['id']} {name}[{index}] changes a truth label or threshold decision")
    return largest_delta


def verify_samples(root=ROOT, *, portable=False):
    protocol = json.loads((root / 'data/signal-protocol.json').read_text())
    saved = json.loads((root / 'data/signals.json').read_text())
    rebuilt = [generate(protocol, scenario, protocol['budget']['seeds'][0]) for scenario in protocol['scenarios']]
    result = {'verified_samples': len(rebuilt), 'steps_per_sample': protocol['budget']['steps']}
    if portable:
        manifest = json.loads((root / 'data/manifest.json').read_text())['files']
        for name in ('data/signals.json', 'data/signal-protocol.json'):
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != manifest[name]:
                raise ValueError(f'Recorded file differs from manifest: {name}')
        deltas = [compare_portable_trace(actual, reference, protocol['designation']['thresholds'])
                  for actual, reference in zip(rebuilt, saved['scenarios'], strict=True)]
        return {**result, 'max_absolute_difference': max(deltas), 'absolute_tolerance': REPLAY_ABS_TOL}
    if rebuilt != saved['scenarios']:
        raise ValueError('Rebuilt signal samples differ')
    return result
