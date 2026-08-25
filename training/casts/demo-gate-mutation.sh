#!/usr/bin/env bash
# Episode 5's core demonstration: prove each gate can actually fail.
#
# Breaks one thing at a time, shows exactly one gate go red, restores, and
# leaves the tree byte-identical. Costs nothing — no agents are involved.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

BACKUP=$(mktemp)
cp app/pricing.py "$BACKUP"
restore() { cp "$BACKUP" app/pricing.py; rm -f "$BACKUP"; }
trap restore EXIT

gates() {
  printf '  '
  uv run --with ruff   ruff check   >/dev/null 2>&1 && printf 'lint=PASS  ' || printf 'lint=FAIL  '
  uv run --with mypy   mypy         >/dev/null 2>&1 && printf 'typecheck=PASS  ' || printf 'typecheck=FAIL  '
  uv run --with pytest pytest -q    >/dev/null 2>&1 && printf 'test=PASS' || printf 'test=FAIL'
  printf '   <- %s\n\n' "$1"
}

echo "=== A gate you have not seen fail is not a gate ==="
echo
gates "clean tree"

echo "1. Add an unused import  ->  only LINT should notice"
python3 - <<'PY'
s = open('app/pricing.py').read()
open('app/pricing.py', 'w').write(s.replace('from typing import Protocol',
                                            'from typing import Protocol\nimport os', 1))
PY
gates "dead import"
cp "$BACKUP" app/pricing.py

echo "2. Strip a type annotation  ->  only TYPECHECK should notice"
python3 - <<'PY'
s = open('app/pricing.py').read()
open('app/pricing.py', 'w').write(s.replace(
    'def _percent_of(amount_cents: int, percent: float) -> int:',
    'def _percent_of(amount_cents, percent):', 1))
PY
gates "annotations removed"
cp "$BACKUP" app/pricing.py

echo "3. Decimal(str(percent)) -> Decimal(percent)  ->  only TEST should notice"
echo "   (8.7% of 500c is 44c exact, 43c through binary float)"
python3 - <<'PY'
s = open('app/pricing.py').read()
open('app/pricing.py', 'w').write(s.replace('* Decimal(str(percent))', '* Decimal(percent)', 1))
PY
gates "float precision broken"
cp "$BACKUP" app/pricing.py

gates "restored"
echo "Each gate failed on its own defect class, and on nothing else."
