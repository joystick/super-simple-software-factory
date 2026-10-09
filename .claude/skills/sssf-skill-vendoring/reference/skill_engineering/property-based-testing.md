<!-- sssf:vendored
source: ~/Projects/training/super-simple-software-factory/downloads/trailofbits-skills/plugins/property-based-testing/skills/property-based-testing/SKILL.md
date: 2026-10-09
sha256: 9448cacb65c6237a7c22dc59602667177ecae405524079ae9ff92240590b995a
-->
<!-- sssf:flattened
kept: references/generating.md sha256:c0e72dfc89babe3c32de718b81b94044362c85e776d7475e950dfeaab78bb58e
kept: references/refactoring.md sha256:6eb5c206f575704791f089608bb06e41d6eed91b9d3c7fb27912f969aed07a18
kept: references/reviewing.md sha256:110b08118a1e7b1a2566def6e9d2a0bf43fc2deefce857d2ce3b4382b07bc774
kept: references/interpreting-failures.md sha256:dbae7db8773712ba03268a3d56ea5aa6720af0650a5189580bfd88aa2edc3f9a
kept: references/libraries.md sha256:f7218acf8e668130ef3048983472579d04e12030c5401926f666363e5f69c686
dropped: README.md -- human-facing plugin readme, duplicates SKILL.md
dropped: agents/openai.yaml -- harness display metadata, no prompt content
dropped: assets/trail-of-bits-mark.svg -- image, no prompt content
dropped: SKILL.md intro [references/refactoring.md](references/refactoring.md) link -- rewritten to point at "Refactoring to Expose a Property" below
dropped: SKILL.md "## Where to look next" "Load the one ..." line and the Task | File table's five references/*.md links -- content merged into that section; table kept as Task | Section with the merged section names
dropped: references/reviewing.md "the property catalog in SKILL.md" -- SKILL.md is the body of this file; rewritten to point at "Property catalog" above
dropped: references/*.md H1s -- demoted to ### subsections of "## Where to look next" (merged there, before "## Introducing PBT to a project that lacks it"); their ## and ### headings demoted to #### and #####; fenced code untouched
-->

---
name: property-based-testing
effort: low
description: "Writes, reviews, and debugs property-based tests — Hypothesis, fast-check, proptest, jqwik, rapid, and Echidna or Medusa for Solidity invariants. Use whenever tests should cover a whole input domain instead of a hand-picked list of examples: encode/decode and serialize/deserialize pairs, parsers, canonicalizers and normalizers, validators, numeric and Decimal types, comparators and sort order, data structures, and smart-contract state invariants. Also use when adding cases to an existing @given, fast-check, or proptest suite, when judging whether existing property tests assert anything real, and when a generator has shrunk a counterexample and you need to tell a wrong property from a genuine bug. Not for coverage-guided binary fuzzing (libFuzzer, AFL), mutation-testing campaigns, static analysis, benchmarking, or end-to-end UI tests."
---

# Property-Based Testing

An example test asserts one point. A property asserts a rule over the whole input
domain and lets the generator hunt for the counterexample. That trade is worth making
when the code has an algebraic shape — an inverse, an invariant, an oracle — and not
otherwise. Code with no such shape gets example tests; saying so is a valid outcome.

Check first whether the shape is missing or merely buried. A calculation wrapped in I/O,
a string built by concatenation, an in-place mutation — each has a property and no seam
to assert it through. See "Refactoring to Expose a Property" below before
concluding there is nothing to assert.

## Property catalog

| Property | Formula | Where it applies |
|---|---|---|
| Roundtrip | `decode(encode(x)) == x` | Serialization, conversion pairs |
| Inverse | `f(g(x)) == x` | encrypt/decrypt, compress/decompress |
| Oracle | `new(x) == reference(x)` | Optimization, refactoring, reimplementation |
| Idempotence | `f(f(x)) == f(x)` | Normalization, formatting, sorting |
| Invariant | Holds before and after | Any transformation, contract state |
| Easy to verify | `is_sorted(sort(x))` | Complex algorithms with cheap checkers |
| Commutativity | `f(a, b) == f(b, a)` | Binary and set operations |
| Associativity | `f(f(a,b), c) == f(a, f(b,c))` | Combining operations |
| Identity | `f(x, e) == x` | Operations with a neutral element |

Strength ordering, weakest to strongest:
`no crash → type preservation → invariant → idempotence → roundtrip / oracle`.

Assert the strongest property the code supports. "No crash" alone rarely justifies the
dependency — if that is all you can find, either a small rearrangement exposes something
stronger, or the honest report is that this code is a poor PBT candidate. Rule out the
first before settling for the second.

## The two ways a property test asserts nothing

- **Tautology.** `assert add(a, b) == a + b` restates the implementation; no bug they
  share can fail it. Pick a property that constrains the function without recomputing
  it. Note the exception: `f(x) == f(x)` is a genuine determinism property when `f`
  is not obviously pure — serializers over dicts or sets, hashing, anything reading
  the clock.
- **Vacuity.** `assume()` that filters out nearly every input passes without
  exercising anything, and self-contradictory `assume()` passes having run zero cases.
  Push constraints into the strategy so the generator produces valid inputs directly.

## Where to look next

The references follow as subsections of this one. Read the one that matches the task in front of you:

| Task | Section |
|---|---|
| Writing new tests, designing strategies | "Generating Property-Based Tests" |
| The code has no property to assert yet | "Refactoring to Expose a Property" |
| Reviewing existing property tests | "Reviewing Property-Based Tests" |
| A property test just failed | "Interpreting Property-Based Test Failures" |
| Library choice, Echidna and Medusa | "PBT Libraries by Language" |

### Generating Property-Based Tests

Writing the `@given` decorator is the easy part. These are the decisions that make
the difference between a suite that finds bugs and one that just runs.

#### Put constraints in the strategy, not in `assume()`

This is the single highest-value habit. `assume()` discards inputs after generation,
so a filter that rejects most candidates wastes the budget and eventually trips
Hypothesis's exhausted-filter guard — which surfaces as a warning nobody reads.

```python
# Slow, and mostly discards
@given(st.integers())
def test_positive(x):
    assume(x > 0)
    ...

# Generates only what you want
@given(st.integers(min_value=1))
def test_positive(x):
    ...
```

Reserve `assume()` for conditions you genuinely cannot express as a generator — a
relationship between two already-generated values, usually.

Build compound inputs with `st.builds`, and derive dependent fields with
`st.composite` or `.flatmap` rather than generating independently and filtering:

```python
@st.composite
def sized_list_and_index(draw):
    xs = draw(st.lists(st.integers(), min_size=1))
    i = draw(st.integers(min_value=0, max_value=len(xs) - 1))
    return xs, i
```

#### Pin the edge cases you already know about

Random generation finds boundaries eventually; `@example` finds them on every run and
documents that you thought about them.

```python
@given(st.lists(st.integers()))
@example([])
@example([1])
@example([1, 1, 1])
def test_sort(xs): ...
```

Empty, single-element, all-duplicates, zero, negative, and the maximum representable
value are the ones that recur.

#### Settings

Defaults (100 examples, 200ms deadline) are wrong at both ends of the workflow:

```python
@settings(max_examples=10)                      # local iteration
@settings(max_examples=200)                     # CI
@settings(max_examples=1000, deadline=None)     # nightly
```

Set `deadline=None` for anything doing real work — the default deadline turns a slow
machine into a failing test, and that flake gets the whole suite deleted.

#### Determinism as a property

`f(x) == f(x)` is a tautology for a pure function and a real test for anything else.
Serializers over dicts or sets, anything involving hashing, iteration order, or time —
those can and do return different output for the same input. Assert it where a broken
implementation could falsify it, and not otherwise.

#### Testing the error path

`st.binary()` against a decoder is worth writing: the contract is usually "raises
`DecodeError` or succeeds, never `IndexError`, never hangs". Catch only the documented
exception and let everything else fail the test.

### Refactoring to Expose a Property

"This code has no algebraic shape" is often a fact about how the code is *arranged*
rather than about what it does. A function that mixes a pure calculation with a database
write has a property; it just does not have a seam to assert it through. These are the
rearrangements that expose one, strongest first.

Suggest the refactor, name the property it unlocks, and let the author decide. A change
to production code to make a test possible is their call, not yours — the same rule that
governs adding a PBT dependency at all.

#### 1. Extract the pure core

The highest-value one by a wide margin, and the reason most "untestable" code is
testable. I/O at the edges, calculation in the middle, assert against the middle.

```python
# Before: the arithmetic is real but unreachable without a database
def process_order(order_id: str) -> None:
    order = db.fetch(order_id)
    total = apply_discount(order, calculate_discount(order))
    db.save(order_id, total)

# After: the pure core takes arguments and returns a value
def order_total(order: Order, rules: DiscountRules) -> Decimal:
    return apply_discount(order, calculate_discount(order, rules))

def process_order(order_id: str) -> None:
    order = db.fetch(order_id)
    db.save(order_id, order_total(order, get_discount_rules()))
```

`order_total` now supports invariants (never negative, never above the undiscounted
total), monotonicity in the discount rate, and an oracle against a reference
calculation. `process_order` keeps example tests with a mocked `db`, which is the right
tool for a two-line wrapper.

The same move applies to anything whose observable is a side effect: build the message,
the request, the query object — then send it. Construction is testable; delivery is
mocked.

#### 2. Add the missing inverse

A one-way operation has no roundtrip by definition. Sometimes the inverse is worth
having in production anyway, and sometimes it is worth having *only* for the test — say
which.

```python
def encode_message(msg: dict) -> bytes: ...
def decode_message(data: bytes) -> dict: ...   # unlocks decode(encode(x)) == x
```

Unlocks roundtrip, the strongest property in the catalog. Worth asking for even when the
production code never decodes: a serializer nobody can read back is usually a latent
bug, not a design.

#### 3. Structured representation plus a renderer

String building by concatenation has nothing to assert beyond "contains a substring".
Split the value from its rendering and the inverse becomes available.

```python
# Before
def build_query(table: str, filters: dict) -> str:
    q = f"SELECT * FROM {table}"
    ...

# After
@dataclass
class Query:
    table: str
    filters: dict

def render(q: Query) -> str: ...
def parse(sql: str) -> Query: ...   # now render/parse is a roundtrip
```

This is pattern 2 wearing different clothes, and it is where escaping bugs live: a
roundtrip over generated filter values finds quoting errors that no hand-written example
will.

#### 4. Return a value instead of mutating

An in-place mutation gives you nothing to compare against, because the input is gone by
the time you want to assert on it.

```python
def sort_tasks(tasks: list[Task]) -> None: ...      # before/after comparison impossible
def sorted_tasks(tasks: list[Task]) -> list[Task]:  # unlocks is_sorted, permutation,
    ...                                             # idempotence, length preservation
```

If the mutating signature has to stay, a wrapper that copies and returns is enough for
the test to have something to hold.

#### 5. Inject the dependency

A function reading a global, a module constant, or `os.environ` can only be tested at
whatever those happen to be, so the edges of its input domain are unreachable.

```python
def validate(data: str) -> bool:          return len(data) <= CONFIG.max_length
def validate(data: str, max_len: int):    return len(data) <= max_len
```

Parameterising the bound is what lets a generator drive `max_len` to 0, to 1, and to the
maximum representable value — the boundaries where validators actually break.

#### When not to suggest this

- **The property you would unlock is "no crash".** Restructuring production code to
  enable the weakest property in the catalog is a bad trade. Say the code is a poor PBT
  candidate and stop.
- **The module needs wholesale restructuring.** Say that once, plainly. Twenty
  individually-reasonable suggestions on one file is noise, and it reads as a rewrite
  request rather than a testing recommendation.
- **The refactor breaks a public API.** Flag it as breaking and offer the
  backwards-compatible version, even when the clean version is obviously nicer.
- **Existing tests cover the code.** Run them after any refactor and say you did.
  "Enabled a property test and broke two example tests" is not progress.

### Reviewing Property-Based Tests

A property test can pass for years while asserting nothing. These are the ways that
happens, worst first.

Report every issue you find with its severity attached. Do not decide on the author's
behalf that a MEDIUM is not worth mentioning.

| Issue | Severity | How it shows up |
|---|---|---|
| Tautological | CRITICAL | Assertion is true regardless of the implementation |
| Vacuous | CRITICAL | `assume()` filters out nearly everything, or contradicts itself |
| No assertion | HIGH | Body calls the function and stops |
| Reimplementation | HIGH | Assertion recomputes the function's own logic |
| Weaker property available | MEDIUM | Length checked, ordering not |
| Over-filtered | MEDIUM | Stacked `assume()` where a strategy constraint belongs |
| Settings | LOW | `max_examples=5`, or no deadline on an expensive strategy |

#### Tautological

```python
@given(st.integers())
def test_useless(x):
    result = compute(x)
    assert result == result
```

Nothing about `compute` can make this fail.

**But `f(x) == f(x)` is not automatically tautological.** It is a real determinism
property whenever `f` is not obviously pure — serializers over dicts or sets, anything
touching iteration order, hashing, or time. `pickle.dumps(obj) == pickle.dumps(obj)`
genuinely fails for objects with a nondeterministic `__reduce__`. Ask whether a broken
implementation could falsify it. If yes, it is a property; if no, it is noise.

#### Vacuous

```python
@given(st.integers())
def test_vacuous(x):
    assume(x > 100)
    assume(x < 50)
    assert compute(x) > 0
```

Hypothesis reports this as passing before it eventually errors on exhausted filters —
and in CI nobody reads the warning. `assume(x == 42)` is the subtler version: it runs,
it passes, and it is an example test wearing a `@given` decorator.

#### Reimplementation

```python
@given(st.integers(), st.integers())
def test_reimplements(a, b):
    assert add(a, b) == a + b
```

If `add` is `a + b`, this asserts `a + b == a + b`. The test survives any bug the two
expressions share. Reach for an algebraic property instead — commutativity, identity,
associativity — which constrains the function without restating it.

#### Finding the tests

```bash
rg "@given\(|from hypothesis import" --type py
rg "fc\.(assert|property)" --type ts --type js
rg "proptest!|#\[quickcheck\]" --type rust
```

#### What to push for

Compare each test against the "Property catalog" above and name the strongest
property the code supports but the suite does not assert. A suite that checks
`len(sort(xs)) == len(xs)` and never checks ordering is the common case.

Also worth flagging: floating-point equality without a tolerance, assertions on
dict/set iteration order, and anything reading the clock — these produce flakes that
get blamed on Hypothesis and then get deleted.

### Interpreting Property-Based Test Failures

A property test that fails has told you one of three things, and they need different
responses:

- **The property is wrong** — you asserted something the code never promised.
- **The spec is ambiguous** — behaviour at this edge was never decided.
- **The code is wrong** — a documented guarantee is violated.

Most of the work is telling them apart. Skipping that step is how PBT gets a
reputation for noise.

#### Ground the property before you trust the failure

Shrunk input in hand, check what the code actually promises. In descending order of
authority:

| Source | What it settles |
|---|---|
| External spec (RFC, format definition) | The real contract, when one exists |
| Type annotations | Return type, nullability, domain |
| Docstrings | Explicit guarantees and preconditions |
| Existing tests | The contract maintainers believe they have |
| Function name | Weak, but `sort` really does imply ordering |

The name is the weakest signal and the one most likely to mislead you — plenty of
functions called `normalize` do something narrower than the word suggests.

Worked example. Hypothesis reports `test_normalize(s='\x00')` failing idempotence:

```python
def normalize(s: str) -> str:
    """Normalize a string to NFC form.

    Args:
        s: Input string (any unicode)
    Returns:
        NFC-normalized string
    """
```

"Any unicode" includes null bytes, so the input is in-domain and the property is
grounded. This one is a real bug.

Change the docstring to "ASCII printable only" and the same failure becomes a
strategy bug — the fix is `st.text(alphabet=...)`, not a bug report.

#### Classification

| Symptom | Cause | Action |
|---|---|---|
| Violates a documented guarantee | Code bug | Report with the shrunk input and a quote from the doc |
| Input violates a documented precondition | Over-broad strategy | Constrain the strategy |
| Property contradicts the docstring or type | Wrong property | Fix the property |
| Edge case the spec never addresses | Ambiguous spec | Ask the maintainer; a discussion, not a bug report |
| Disappears under realistic constraints | Test artifact | Fix the strategy |
| Behaviour differs from a sibling function | Possible inconsistency | Worth raising, flag the uncertainty |

Precondition violations and explicitly-undefined behaviour are not bugs. Passing `-1`
to a function documented as taking positive integers tells you nothing.

Report what you find with the classification attached, including the cases you are
unsure about — say "ambiguous spec, needs a maintainer decision" rather than staying
quiet. A suppressed finding cannot be triaged by anyone else.

#### Failure patterns that recur

**Lone surrogates break text roundtrips.** `decode(encode(s)) == s` fails on
`'\uD800'`. Whether that is a bug turns entirely on whether the format claims to
accept arbitrary `str` or only valid UTF-8.

**Denormals break numeric invariants.** A probability function returning a negative
value for `x=1e-320` is a genuine bug against a documented `[0, 1]` range, and it is
exactly the input no human writes by hand.

**Hash/equality divergence violates a language contract**, not just a docstring —
`a == b` must imply `hash(a) == hash(b)` in Python. No grounding required; report it.

**Off-by-one in custom iterators** shows up as `list(it(xs)) == xs` dropping the last
element. Almost always real.

### PBT Libraries by Language

Match the project's existing choice. Introducing a second PBT library into a codebase
that already has one is not worth the property you wanted to write.

| Language | Default | Also in use |
|---|---|---|
| Python | Hypothesis | — |
| TypeScript / JavaScript | fast-check | — |
| Rust | proptest | quickcheck (simpler API, per-type shrinking) |
| Go | rapid | gopter (ScalaCheck-style, more explicit) |
| Java | jqwik | — |
| Scala | ScalaCheck | — |
| C# | FsCheck | — |
| Elixir | StreamData | — |
| Haskell | QuickCheck | Hedgehog (integrated shrinking, no type classes) |
| Clojure | test.check | — |
| Ruby | PropCheck | — |
| Kotlin | Kotest | — |
| C++ | RapidCheck | — |
| Swift | SwiftCheck | unmaintained — check before recommending |

Detect what a repo already uses before proposing anything:

```bash
rg "from hypothesis import|fast-check|use proptest|pgregory.net/rapid|net.jqwik|echidna_|invariant_"
```

#### Smart contracts (EVM / Solidity)

This is where PBT earns the most, because contract state is adversarial and the input
domain is every possible call sequence. Trail of Bits maintains both tools:

- **Echidna** — property fuzzer, mature, the default choice.
- **Medusa** — parallel execution, coverage-guided; faster on large contract suites.

Two testing modes, and picking the wrong one is the usual mistake:

**Property mode** — a function returning `bool` that must never become false.

```solidity
// Echidna calls this after every transaction sequence.
function echidna_total_matches_sum() public view returns (bool) {
    return token.totalSupply() == trackedSum;
}
```

**Assertion mode** — an `assert` inside a function the fuzzer is allowed to call
directly, for properties about a specific operation rather than global state.

```solidity
function testDepositIncreasesBalance(uint256 amount) public {
    uint256 before = vault.balanceOf(address(this));
    vault.deposit(amount);
    assert(vault.balanceOf(address(this)) >= before);
}
```

##### Contract invariants worth asserting

Solvency (`sum(balances) <= totalAssets`), supply conservation, access control (a
non-owner call sequence never reaches an owner-only state change), monotonic
counters, and round-trip on share/asset conversion (`convertToShares` then
`convertToAssets` never returns more than you put in).

##### Tautologies specific to Solidity

Type bounds are not properties. `uint256 x >= 0` is always true, and so is
`address(this).balance >= 0` — the compiler guarantees it. Likewise a property that
only reads state the fuzzer cannot reach is vacuous: if no call sequence can enter
the branch, the invariant is never exercised. Check Echidna's coverage output rather
than assuming.

`echidna_` functions must be `view`/`pure` and take no arguments — a property that
mutates state silently changes what it is testing.

Tutorials: [secure-contracts.com](https://secure-contracts.com).

## Introducing PBT to a project that lacks it

If the project already uses a PBT library, just write the tests in it. If it does not,
adding one is a dependency decision that belongs to the user — offer it once with the
specific property you would write, and take the answer either way.

Adapted from github.com/trailofbits/skills (plugins/property-based-testing) @ 82fe822, licensed CC-BY-SA-4.0. Attribution: Trail of Bits.
