# From weather-report adws/adw_modules/gates.py. Paste into your gates.py (it uses
# that module's subprocess, Path, EnvelopeBase, GateReport and TAIL_CHARS), then add
# `gates.okf_maintained()` to every documenter phase's gates= list
# (adw_simple_sdlc.py, adw_document.py).

def okf_maintained(bundle: str = ".okf", validate_cmd: list[str] | None = None,
                   roadmap_check_cmd: list[str] | None = None):
    """Gate factory: the documenter must leave the OKF bundle updated and valid.

    Prompting alone didn't do it: live run 06458e59 composed the okf skill and the
    system.md duties and still touched nothing under .okf/. So the duty is
    checked mechanically: at least one existing bundle file declared in
    `artifacts`, including a roadmap concept, and the bundle's validator exits 0.
    When the repo generates its roadmap tables (scripts/sync_okf_roadmap.py),
    they must be in sync too, so a hand-edited ticket table fails. A repo with
    no bundle has nothing to maintain and passes.
    """
    command = validate_cmd or ["uv", "run", "scripts/okf_validate.py", bundle]
    if roadmap_check_cmd is None and Path("scripts/sync_okf_roadmap.py").is_file():
        roadmap_check_cmd = ["uv", "run", "scripts/sync_okf_roadmap.py", "--check"]

    def gate(envelope: EnvelopeBase, run) -> GateReport:
        report = GateReport()
        if not Path(bundle).is_dir():
            return report.check(bundle, True, "no bundle in this repo, nothing to maintain")
        declared = [a for a in envelope.artifacts
                    if Path(a).as_posix().startswith(f"{bundle}/") and a.endswith(".md")]
        for a in declared:
            report.check(a, Path(a).is_file(),
                         "exists" if Path(a).is_file() else "declared bundle file does not exist")
        report.check(f"{bundle}/ updated", bool(declared),
                     f"{len(declared)} bundle file(s) declared" if declared else
                     f"no {bundle}/*.md file in artifacts: update the concepts this change "
                     f"touches and its roadmap concept, then declare them")
        roadmap = [a for a in declared if Path(a).as_posix().startswith(f"{bundle}/roadmap/")
                   and Path(a).name != "index.md"]
        report.check(f"{bundle}/roadmap/ updated", bool(roadmap),
                     f"{roadmap[0]} declared" if roadmap else
                     f"no {bundle}/roadmap/<feature>.md in artifacts: record this ticket in its "
                     f"feature's roadmap concept (create it if missing), then declare it")
        checks = [command] + ([roadmap_check_cmd] if roadmap_check_cmd else [])
        for cmd in checks:
            result = subprocess.run(cmd, capture_output=True, text=True)
            note = f"exit {result.returncode}"
            if result.returncode != 0:
                note += "\n" + (result.stdout + result.stderr)[-TAIL_CHARS:]
            report.check(" ".join(cmd), result.returncode == 0, note)
        return report

    gate.__name__ = f"okf_maintained({bundle})"
    return gate
