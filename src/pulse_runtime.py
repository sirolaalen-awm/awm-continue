"""PA-09 v1.1: reference local pulse routing; no provider/network required.

Demonstrates functional linking and contextual compost; not a proof of domain truth.
"""
from dataclasses import dataclass
from awm_reference import Trace

@dataclass(frozen=True)
class Pulse:
    trigger: str
    function_ids: frozenset
    conditions: frozenset
    scope: frozenset = frozenset()

@dataclass(frozen=True)
class Decision:
    function: str
    reason: str
    matched_trace: tuple
    blocked_functions: tuple

class LocalCouplings:
    """Explicit function-to-function associations; local neighbors only."""
    def __init__(self, relations=()):
        self.relations = {}
        for a, b in relations:
            self.relations.setdefault(a, set()).add(b)
            self.relations.setdefault(b, set()).add(a)

    def neighborhood(self, function_ids):
        ids = set(function_ids)
        for identifier in function_ids:
            ids.update(self.relations.get(identifier, ()))
        return ids


def inherited_decision(traces, pulse, couplings):
    """Contextual rule: exact contextual failures veto same function; others remain eligible.

    No assertion that absence of evidence means real-world safety.
    """
    neighborhood = couplings.neighborhood(pulse.function_ids)
    matching = [t for t in traces if t.function in neighborhood]
    applicable = [t for t in matching if t.conditions <= pulse.conditions]
    blocked = {t.function for t in applicable if t.status == 'KOMPOST'}
    # A later successful observation in the SAME exact context can supersede a prior compost
    for f in list(blocked):
        candidates = [t for t in applicable if t.function == f]
        if candidates and candidates[-1].status == 'LAST_GOOD':
            blocked.remove(f)
    eligible = [t for t in applicable if t.function not in blocked and t.status in ('LAST_GOOD','OTVORENI_POTENCIJAL')]
    eligible.sort(key=lambda t: (t.status != 'LAST_GOOD', -len(t.conditions), t.function))
    if eligible:
        selected = eligible[0]
        return Decision(selected.function, 'lokalni naslijeđeni trag: '+selected.status,
                        (selected.parent, selected.evidence), tuple(sorted(blocked)))
    return Decision('NOVI_POKUSAJ', 'nema prikladnog lokalnog traga; otvoriti istraživanje', (), tuple(sorted(blocked)))


def demo_pulse():
    couplings = LocalCouplings([('F_REZ', 'F_NISKA_SILA'), ('F_REZ','F_VISOKA_SILA')])
    traces = [
        Trace('F_REZ', frozenset({'mekan'}), 'LAST_GOOD', 'uspjelo', 'G1', 'rd:1'),
        Trace('F_VISOKA_SILA', frozenset({'mekan'}), 'KOMPOST', 'oštećenje', 'G1', 'rd:2'),
        Trace('F_NISKA_SILA', frozenset({'tvrd'}), 'OTVORENI_POTENCIJAL', 'neispitano', 'G1', 'rd:3'),
    ]
    return inherited_decision(traces, Pulse('materijal_promijenjen', frozenset({'F_REZ'}), frozenset({'tvrd', 'vruće'})), couplings)

if __name__ == '__main__':
    print(demo_pulse())
