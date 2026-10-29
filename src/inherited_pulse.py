"""PA-09: deterministic, local proof-of-mechanism for inherited pulse behavior.

Not an LLM/Nebius test. Gen2 receives compact validated experience and state,
not the original Gen1 teaching transcript. Runtime selects action; LLM may
transform content after selection, not decide whether a process has NEXT.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Experience:
    trigger: str
    function: str
    conditions: frozenset
    status: str  # LAST_GOOD, KOMPOST, OTVORENI_POTENCIJAL
    evidence: str

@dataclass(frozen=True)
class ProcessState:
    phase: str  # OPEN, COMPLETE
    next_step: str = ''
    conditions: frozenset = frozenset()

@dataclass(frozen=True)
class PulseOutcome:
    action: str  # CONTINUE, STOP, UNKNOWN
    product: str
    evidence: str
    reason: str


def inherit_pulse(trigger, state, experience):
    """Use only verified inherited behavior whose conditions fit current state.

    'STOP' is a positive runtime outcome, not missing generation.  No action
    claim becomes VERIFIED without provenance.  Unknown context stays unknown.
    """
    if trigger != '.':
        return PulseOutcome('UNKNOWN', '', '', 'not a learned pulse')
    relevant = [x for x in experience if x.trigger == trigger and x.function == 'PULSE_CLOCK'
                and x.conditions <= state.conditions]
    confirmed = [x for x in relevant if x.status == 'LAST_GOOD' and x.evidence]
    if not confirmed:
        return PulseOutcome('UNKNOWN', '', '', 'no verified applicable inherited pulse')
    proof = confirmed[-1].evidence
    if state.phase == 'COMPLETE':
        return PulseOutcome('STOP', 'POTREBAN_NOVI_ULAZ', proof, 'process complete')
    if state.phase == 'OPEN' and state.next_step:
        return PulseOutcome('CONTINUE', state.next_step, proof, 'valid next step exists')
    return PulseOutcome('UNKNOWN', '', proof, 'insufficient state for action')


def example_generation1():
    """A compact confirmed record, as produced by a completed Gen1 cycle.

    This fixture is explicitly synthetic; a real system must source evidence
    from genuine readback before labeling LAST_GOOD.
    """
    return [Experience('.', 'PULSE_CLOCK', frozenset({'awc_process'}),
                       'LAST_GOOD', 'fixture:gen1_verified_pulse'),
            Experience('.', 'PULSE_CLOCK', frozenset({'awc_process', 'obsolete'}),
                       'KOMPOST', 'fixture:gen1_failed_application')]
