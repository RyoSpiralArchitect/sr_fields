"""Frozen surface measures and the cue vocabulary removed in the decoding check."""
import re
from features import EMOTION, features as previous_features, normalize, words

FAMILIES = {
    'embarrassed': frozenset('embarrass embarrassed embarrassing embarrassment embarrasses embarrassments awkward awkwardly awkwardness ashamed shame shameful humiliated humiliating humiliation selfconscious mortified mortifying mortification flustered'.split()),
    'happy': frozenset('happy happier happiest happily happiness joy joys joyful joyfully joyous glad gladly gladness pleased pleasure pleasurable delight delighted delightful enjoy enjoyed enjoying enjoyment enjoyable cheerful cheery elated elation'.split()),
}
ALL_CUES = FAMILIES['happy'] | FAMILIES['embarrassed']
CAUSAL_PROBE = re.compile(r"\b(?:why|what (?:made|makes|caused|led)|what was it (?:about|that)|what is it (?:about|that))\b")
CAUSAL_LINK = re.compile(r"\bbecause\b")
ADDED_IMPACT = re.compile(r"\b(?:more (?:than|to you than) you (?:realiz(?:e|ed)|expect(?:ed)?|thought|know)|(?:stronger|bigger|deeper) (?:impact|impression|meaning) than|more than just a joke|meant something (?:deeper|more))\b")
OTHERS_TARGET = re.compile(r"\b(?:laugh(?:ing|ed)? at you|making fun of you|made fun of you|mock(?:ed|ing) you|at your expense)\b")
LISTED = ('echo_exact', 'echo_family', 'other_listed_emotion', 'reason_question',
          'because', 'added_meaning_phrase', 'laughter_at_you')


def lexical_tokens(text):
    return words(normalize(text).replace('self-conscious', 'selfconscious').replace('self conscious', 'selfconscious'))


def masked_tokens(text):
    return [w for w in lexical_tokens(text) if w not in ALL_CUES]


def measure(text, case):
    base = previous_features(text)
    value = normalize(text)
    tokens = set(lexical_tokens(text))
    family = FAMILIES.get(case, frozenset())
    return {**base, 'echo_exact': int(case in tokens) if family else None,
            'echo_family': int(bool(tokens & family)) if family else None,
            'other_listed_emotion': int(any(hit.group() not in family for hit in EMOTION.finditer(value))),
            'reason_question': int('?' in value and bool(CAUSAL_PROBE.search(value))),
            'because': int(bool(CAUSAL_LINK.search(value))),
            'added_meaning_phrase': int(bool(ADDED_IMPACT.search(value))),
            'laughter_at_you': int(bool(OTHERS_TARGET.search(value)))}
