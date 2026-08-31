"""Console.skill_engineering_report() — Phase 3 cost/trace visibility.

Console._emit always both prints AND logs a trace event (see console.py's own
docstring: "print and trace cannot drift"), so asserting on the logged event
is asserting on real behaviour, not a side channel — it's the SAME emission
the terminal line came from, not a separate mechanism we're reaching around.
"""

from __future__ import annotations

from adw_modules.console import Console


class _FakeTracer:
    def __init__(self):
        self.events = []

    def event(self, record):
        self.events.append(record)


def _messages(tracer: _FakeTracer) -> list[str]:
    return [e.payload["message"] for e in tracer.events]


def test_no_skills_emits_nothing():
    tracer = _FakeTracer()
    console = Console(tracer, adw_id="test")
    console.skill_engineering_report([], tokens_estimate=0, budget=None)
    assert tracer.events == []


def test_reports_skill_names_and_token_estimate():
    tracer = _FakeTracer()
    console = Console(tracer, adw_id="test")
    console.skill_engineering_report(
        ["adws/adw_data/skill_engineering/tdd.md"], tokens_estimate=1234, budget=None)
    messages = _messages(tracer)
    assert len(messages) == 1
    assert "tdd" in messages[0]
    assert "1,234" in messages[0]


def test_no_budget_set_never_warns():
    tracer = _FakeTracer()
    console = Console(tracer, adw_id="test")
    console.skill_engineering_report(
        ["adws/adw_data/skill_engineering/tdd.md"], tokens_estimate=999_999, budget=None)
    assert all(e.payload["level"] != "warn" for e in tracer.events)


def test_under_budget_does_not_warn():
    tracer = _FakeTracer()
    console = Console(tracer, adw_id="test")
    console.skill_engineering_report(
        ["adws/adw_data/skill_engineering/tdd.md"], tokens_estimate=100, budget=500)
    assert all(e.payload["level"] != "warn" for e in tracer.events)


def test_over_budget_warns_but_does_not_raise():
    tracer = _FakeTracer()
    console = Console(tracer, adw_id="test")
    # Must not raise — a soft budget only warns, per the PRD: never fails the run.
    console.skill_engineering_report(
        ["adws/adw_data/skill_engineering/tdd.md"], tokens_estimate=5000, budget=500)
    warnings = [e for e in tracer.events if e.payload["level"] == "warn"]
    assert len(warnings) == 1
    assert "5,000" in warnings[0].payload["message"]
    assert "500" in warnings[0].payload["message"]
