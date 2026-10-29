"""AWM PA-09: minimalni deterministički CPU referentni proces, bez vanjskih ovisnosti."""
from dataclasses import dataclass
from enum import Enum
from threading import Lock

class Verdict(str, Enum):
    VALID = "VALJANO"
    INVALID = "NEVALJANO"
    UNKNOWN = "NEUTVRĐENO"

@dataclass(frozen=True)
class Trace:
    function: str
    conditions: frozenset
    status: str
    outcome: str
    parent: str
    evidence: str

class Memory:
    def __init__(self):
        self.traces = []
        self.version = 10
        self.last_good = "INIT"
        self._lock = Lock()

    def inherit(self, conditions):
        query = frozenset(conditions)
        # Podudarnost je minimalni mehanizam; konkretni HACK može dodati robusnije uvjete.
        return sorted(self.traces, key=lambda t: (-len(query & t.conditions), t.function))

    def commit(self, expected_version, value, evidence):
        with self._lock:
            verdict = sentinel(self.version, expected_version, value, evidence)
            if verdict == Verdict.VALID:
                self.version += 1
                self.last_good = value
            return verdict

def sentinel(current_version, expected_version, proposal, evidence):
    if current_version != expected_version:
        return Verdict.INVALID
    if not proposal or evidence is None:
        return Verdict.UNKNOWN
    return Verdict.VALID

def choose_from_experience(memory, conditions):
    """Referentni izbor: izbjegni naučeni kompost ako se uvjet preklapa;
    izaberi odgovarajući LAST GOOD; inače razmotri otvoreni potencijal.
    Ovo NIJE opća semantika stvarnog svijeta.
    """
    ranked = memory.inherit(conditions)
    query = frozenset(conditions)
    for t in ranked:
        if t.conditions & query and t.status == "LAST_GOOD":
            return t.function, "naslijeđeni LAST GOOD"
    for t in ranked:
        if t.conditions & query and t.status == "OTVORENI_POTENCIJAL":
            return t.function, "naslijeđeni otvoreni potencijal"
    return "NOVI_POKUSAJ", "potrebno istraživanje"

def run_two_generations():
    memory = Memory()
    # G1: naslijeđeni proizvod, iskustvo neuspjeha i nedovršena mogućnost.
    memory.traces.extend([
        Trace("F_REZ", frozenset(["mekan"]), "LAST_GOOD", "uspjelo", "G1", "R_d:1"),
        Trace("F_VISOKA_SILA", frozenset(["mekan"]), "KOMPOST", "oštećenje", "G1", "R_d:2"),
        Trace("F_NISKA_SILA", frozenset(["tvrd"]), "OTVORENI_POTENCIJAL", "neispitano", "G1", "R_d:3"),
    ])
    # G2 prepoznaje relevantan naslijeđeni potencijal u novim uvjetima.
    conditions = {"tvrd", "visoka_temperatura"}
    function, reason = choose_from_experience(memory, conditions)
    verdict = memory.commit(10, function, evidence="G2_SIMULIRANI_READBACK")
    if verdict == Verdict.VALID:
        memory.traces.append(Trace(function, frozenset(conditions), "LAST_GOOD", "simulirano", "G2", "R_d:G2"))
    return {"function": function, "reason": reason, "sentinel": verdict.value,
            "version": memory.version, "last_good": memory.last_good,
            "traces": len(memory.traces)}

if __name__ == "__main__":
    print(run_two_generations())
