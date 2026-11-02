"""Frozen English surface measures for a single dialogue. Indicators are per reply."""
import re

WORDS = re.compile(r"[a-z]+(?:'[a-z]+)?")
EMOTION = re.compile(r"\b(?:hurt|sad(?:ness)?|upset|angry|anger|embarrass(?:ed|ing|ment)|ashamed|shame|anxious|anxiety|nervous|awkward(?:ness)?|uncomfortable|uneasy|confus(?:ed|ing|ion)|happy|happiness|joy|amused|lonely|afraid|worried|humiliated|frustrat(?:ed|ion)|discomfort)\b")
INVITE = re.compile(r"\b(?:if you (?:want|like|feel (?:like|comfortable))|(?:only )?if you're (?:ready|comfortable)|when(?:ever)? you're ready|would you like|do you (?:want|feel like)|no (?:rush|pressure)|take your time|at your own pace|you don't have to)\b")
UNCERTAIN = re.compile(r"\b(?:maybe|perhaps|might|i wonder|could be|not sure|don't know|hard to (?:say|tell|name)|not knowing|uncertain|unsure|no need to (?:name|label|figure)|don't have to (?:name|label|figure))\b")
LAUGHTER = re.compile(r"\blaugh(?:ed|ing|ter|s)?\b")
BODY = re.compile(r"\b(?:body|bodily|physical(?:ly)?|chest|stomach|throat|breath(?:ing)?|shoulders?|heartbeat|sensation|tension)\b")
ATTRIBUTION = re.compile(r"\byou (?:were|are|felt|feel|must (?:have felt|feel)) (?:really |so |a little |very )?(?:hurt|sad|upset|angry|embarrassed|ashamed|anxious|nervous|uncomfortable|uneasy|confused|happy|afraid|humiliated|frustrated)\b")


def normalize(text):
    return text.lower().replace('’', "'").replace('‘', "'")


def words(text):
    return WORDS.findall(normalize(text))


def features(text):
    s = normalize(text)
    return {
        'question': int('?' in s),
        'emotion_word': int(bool(EMOTION.search(s))),
        'words': len(words(text)),
        'invitation': int(bool(INVITE.search(s))),
        'uncertainty': int(bool(UNCERTAIN.search(s))),
        'laughter_anchor': int(bool(LAUGHTER.search(s))),
        'body_word': int(bool(BODY.search(s))),
        'direct_attribution': int('?' not in s and bool(ATTRIBUTION.search(s))),
    }
