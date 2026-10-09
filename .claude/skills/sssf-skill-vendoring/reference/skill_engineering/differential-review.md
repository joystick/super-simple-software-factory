<!-- sssf:vendored
source: ~/Projects/training/super-simple-software-factory/downloads/trailofbits-skills/plugins/differential-review/skills/differential-review/SKILL.md
date: 2026-10-09
sha256: f9af6a8193fc1a9f8ca3c54bb8d19095a5f20c9472ca6d014488bbde50b67da0
-->
<!-- sssf:flattened
kept: methodology.md sha256:16b335d24cf2145e3dc4a37f50056550d29db2efa20e6df78fec95ec1e6fb0b4
kept: adversarial.md sha256:3cb823f38c6e551cbcf5f72325d2bb219dacdad774072519c31d50d92db19800
kept: reporting.md sha256:0016876dc6f158e926448bff1b6f634796757c7afe09dff177cfe30250724fc4
kept: patterns.md sha256:52abb18abbc73502a3d3b2f36a7a035adc1db40fd812d1d5424cf065036a06e9
dropped: agents/openai.yaml -- harness display metadata, no prompt content
dropped: assets/trail-of-bits-mark.svg -- image, no prompt content
dropped: SKILL.md "## Agents" section and the Decision Tree's "Or delegate to: differential-review:adversarial-modeler agent" branch -- the agent is not vendored and the reviewer has no subagent/Task tool; the tree's HIGH RISK branch now says to read "Adversarial Vulnerability Analysis (Phase 5)" below and do the modeling yourself
dropped: SKILL.md Decision Tree "Read: methodology.md/adversarial.md/reporting.md/patterns.md" and Example Usage "(see methodology.md)" -- file names of merged siblings, rewritten to the merged section names (edited inside those code fences)
dropped: SKILL.md "## Supporting Documentation" links and "For first-time users" link -- content merged into that section; rewritten as an intro naming the merged subsections
dropped: methodology.md, adversarial.md, patterns.md sibling links (incl. methodology.md#pre-analysis-baseline-context-building) -- rewritten to named-section pointers above/below
dropped: reporting.md "File Naming and Location" cwd -> Desktop -> ~/.claude/skills/differential-review/output/ chain and <PROJECT>_DIFFERENTIAL_REVIEW_<DATE>.md naming -- replaced with the single location <context_handoff_dir>/review.md (reviewer system.md/user.md); writes: [] would roll back a report in cwd
dropped: reporting.md "Error Handling" Desktop/temp-dir/chat fallback steps 1-4 -- replaced with one line: one place to write, report the failure; closing bold line kept
dropped: reporting.md "## Integration with issue-writer" section and the User Notification Template line "Consider chaining with issue-writer for stakeholder report"; SKILL.md "## Integration" issue-writer bullets -- issue-writer is not vendored or reachable
dropped: methodology.md Pre-Analysis "# Checkout baseline commit / git checkout <baseline_commit>" -- would move the working tree on a writes: [] role (rolled back, phase killed) and scramble the diff under review; replaced with read-only git show <baseline_commit>:<path> and git diff <baseline_commit>..HEAD -- <path>
dropped: sibling H1s -- demoted to ### subsections of "## Supporting Documentation"; their ##-#### headings demoted by two levels; fenced code untouched
-->

---
name: differential-review
description: "Performs security-focused differential review of code changes. Adapts analysis depth to codebase size, uses git blame for context, calculates blast radius by counting callers, checks test coverage of modified code, and generates a markdown report. Use when reviewing a PR, commit, or diff for security vulnerabilities, checking whether a change re-introduces a previously fixed bug, asking what else a change could break, or finding which modified code has no test covering it."
allowed-tools: Read Write Grep Glob Bash
---

# Differential Security Review

Security-focused code review for PRs, commits, and diffs.

## Core Principles

1. **Risk-First**: Focus on auth, crypto, value transfer, external calls
2. **Evidence-Based**: Every finding backed by git history, line numbers, attack scenarios
3. **Adaptive**: Scale to codebase size (SMALL/MEDIUM/LARGE)
4. **Honest**: Explicitly state coverage limits and confidence level
5. **Output-Driven**: Always generate comprehensive markdown report file

---

## Rationalizations (Do Not Skip)

| Rationalization | Why It's Wrong | Required Action |
|-----------------|----------------|-----------------|
| "Small PR, quick review" | Heartbleed was 2 lines | Classify by RISK, not size |
| "I know this codebase" | Familiarity breeds blind spots | Build explicit baseline context |
| "Git history takes too long" | History reveals regressions | Never skip Phase 1 |
| "Blast radius is obvious" | You'll miss transitive callers | Calculate quantitatively |
| "No tests = not my problem" | Missing tests = elevated risk rating | Flag in report, elevate severity |
| "Just a refactor, no security impact" | Refactors break invariants | Analyze as HIGH until proven LOW |
| "I'll explain verbally" | No artifact = findings lost | Always write report |

---

## Quick Reference

### Codebase Size Strategy

| Codebase Size | Strategy | Approach |
|---------------|----------|----------|
| SMALL (<20 files) | DEEP | Read all deps, full git blame |
| MEDIUM (20-200) | FOCUSED | 1-hop deps, priority files |
| LARGE (200+) | SURGICAL | Critical paths only |

### Risk Level Triggers

| Risk Level | Triggers |
|------------|----------|
| HIGH | Auth, crypto, external calls, value transfer, validation removal |
| MEDIUM | Business logic, state changes, new public APIs |
| LOW | Comments, tests, UI, logging |

---

## Workflow Overview

```
Pre-Analysis → Phase 0: Triage → Phase 1: Code Analysis → Phase 2: Test Coverage
    ↓              ↓                    ↓                        ↓
Phase 3: Blast Radius → Phase 4: Deep Context → Phase 5: Adversarial → Phase 6: Report
```

---

## Decision Tree

**Starting a review?**

```
├─ Need detailed phase-by-phase methodology?
│  └─ Read: "Differential Review Methodology" below
│     (Pre-Analysis + Phases 0-4: triage, code analysis, test coverage, blast radius)
│
├─ Analyzing HIGH RISK change?
│  └─ Read: "Adversarial Vulnerability Analysis (Phase 5)" below, and do the modeling yourself
│     (Phase 5: Attacker modeling, exploit scenarios, exploitability rating)
│
├─ Writing the final report?
│  └─ Read: "Report Generation (Phase 6)" below
│     (Phase 6: Report structure, templates, formatting guidelines)
│
├─ Looking for specific vulnerability patterns?
│  └─ Read: "Common Vulnerability Patterns" below
│     (Regressions, reentrancy, access control, overflow, etc.)
│
└─ Quick triage only?
   └─ Use Quick Reference above, skip detailed docs
```

---

## Quality Checklist

Before delivering:

- [ ] All changed files analyzed
- [ ] Git blame on removed security code
- [ ] Blast radius calculated for HIGH risk
- [ ] Attack scenarios are concrete (not generic)
- [ ] Findings reference specific line numbers + commits
- [ ] Report file generated
- [ ] User notified with summary

---

## Integration

**audit-context-building skill:**
- Pre-Analysis: Build baseline context
- Phase 4: Deep context on HIGH RISK changes

---

## Example Usage

### Quick Triage (Small PR)
```
Input: 5 file PR, 2 HIGH RISK files
Strategy: Use Quick Reference
1. Classify risk level per file (2 HIGH, 3 LOW)
2. Focus on 2 HIGH files only
3. Git blame removed code
4. Generate minimal report
Time: ~30 minutes
```

### Standard Review (Medium Codebase)
```
Input: 80 files, 12 HIGH RISK changes
Strategy: FOCUSED (see "Differential Review Methodology" below)
1. Full workflow on HIGH RISK files
2. Surface scan on MEDIUM
3. Skip LOW risk files
4. Complete report with all sections
Time: ~3-4 hours
```

### Deep Audit (Large, Critical Change)
```
Input: 450 files, auth system rewrite
Strategy: SURGICAL + audit-context-building
1. Baseline context with audit-context-building
2. Deep analysis on auth changes only
3. Blast radius analysis
4. Adversarial modeling
5. Comprehensive report
Time: ~6-8 hours
```

---

## When NOT to Use This Skill

- **Greenfield code** (no baseline to compare)
- **Documentation-only changes** (no security impact)
- **Formatting/linting** (cosmetic changes)
- **User explicitly requests quick summary only** (they accept risk)

For these cases, use standard code review instead.

---

## Red Flags (Stop and Investigate)

**Immediate escalation triggers:**
- Removed code from "security", "CVE", or "fix" commits
- Access control modifiers removed (onlyOwner, internal → external)
- Validation removed without replacement
- External calls added without checks
- High blast radius (50+ callers) + HIGH risk change

These patterns require adversarial analysis even in quick triage.

---

## Tips for Best Results

**Do:**
- Start with git blame for removed code
- Calculate blast radius early to prioritize
- Generate concrete attack scenarios
- Reference specific line numbers and commits
- Be honest about coverage limitations
- Always generate the output file

**Don't:**
- Skip git history analysis
- Make generic findings without evidence
- Claim full analysis when time-limited
- Forget to check test coverage
- Miss high blast radius changes
- Output report only to chat (file required)

---

## Supporting Documentation

The supporting documentation follows, one subsection per topic:

- **"Differential Review Methodology"** - Detailed phase-by-phase workflow (Phases 0-4)
- **"Adversarial Vulnerability Analysis (Phase 5)"** - Attacker modeling and exploit scenarios (Phase 5)
- **"Report Generation (Phase 6)"** - Report structure and formatting (Phase 6)
- **"Common Vulnerability Patterns"** - Common vulnerability patterns reference

---

**For first-time users:** Start with "Differential Review Methodology" below to understand the complete workflow.

**For experienced users:** Use this page's Quick Reference and Decision Tree to navigate directly to needed content.

### Differential Review Methodology

Detailed phase-by-phase workflow for security-focused code review.

#### Pre-Analysis: Baseline Context Building

**FIRST ACTION - Build complete baseline understanding:**

If `audit-context-building` skill is available:

```bash
# Inspect the baseline commit read-only (never check it out: the working tree must not change)
git show <baseline_commit>:<path>
git diff <baseline_commit>..HEAD -- <path>

# Invoke audit-context-building skill on baseline codebase
# Scope = entire relevant project (e.g., packages/contracts/contracts/ for Solidity, src/ for Rust, etc.)
audit-context-building --scope [entire project or main contract directory] --focus invariants,trust-boundaries,validation-patterns,call-graphs,state-flows

# Examples:
# For Solidity: audit-context-building --scope packages/contracts/contracts
# For Rust: audit-context-building --scope src
# For full repo: audit-context-building --scope .
```

**Capture from baseline analysis:**
- System-wide invariants (what must ALWAYS be true across all code)
- Trust boundaries and privilege levels (who can do what)
- Validation patterns (what gets checked where - defense-in-depth)
- Complete call graphs for critical functions (who calls what)
- State flow diagrams (how state changes)
- External dependencies and trust assumptions

**Why this matters:**
- Understand what the code was SUPPOSED to do before changes
- Identify implicit security assumptions in baseline
- Detect when changes violate baseline invariants
- Know which patterns are system-wide vs local
- Catch when changes break defense-in-depth

**Store baseline context for reference during differential analysis.**

After baseline analysis, checkout back to head commit to analyze changes.

---

#### Phase 0: Intake & Triage

**Extract changes:**
```bash
# For commit range
git diff <base>..<head> --stat
git log <base>..<head> --oneline

# For PR
gh pr view <number> --json files,additions,deletions

# Get all changed files
git diff <base>..<head> --name-only
```

**Assess codebase size:**
```bash
find . -name "*.sol" -o -name "*.rs" -o -name "*.go" -o -name "*.ts" | wc -l
```

**Classify complexity:**
- **SMALL**: <20 files → Deep analysis (read all deps)
- **MEDIUM**: 20-200 files → Focused analysis (1-hop deps)
- **LARGE**: 200+ files → Surgical (critical paths only)

**Risk score each file:**
- **HIGH**: Auth, crypto, external calls, value transfer, validation removal
- **MEDIUM**: Business logic, state changes, new public APIs
- **LOW**: Comments, tests, UI, logging

---

#### Phase 1: Changed Code Analysis

For each changed file:

1. **Read both versions** (baseline and changed)

2. **Analyze each diff region:**
   ```
   BEFORE: [exact code]
   AFTER: [exact code]
   CHANGE: [behavioral impact]
   SECURITY: [implications]
   ```

3. **Git blame removed code:**
   ```bash
   # When was it added? Why?
   git log -S "removed_code" --all --oneline
   git blame <baseline> -- file.sol | grep "pattern"
   ```

   **Red flags:**
   - Removed code from "fix", "security", "CVE" commits → CRITICAL
   - Recently added (<1 month) then removed → HIGH

4. **Check for regressions (re-added code):**
   ```bash
   git log -S "added_code" --all -p
   ```

   Pattern: Code added → removed for security → re-added now = REGRESSION

5. **Micro-adversarial analysis** for each change:
   - What attack did removed code prevent?
   - What new surface does new code expose?
   - Can modified logic be bypassed?
   - Are checks weaker? Edge cases covered?

6. **Generate concrete attack scenarios:**
   ```
   SCENARIO: [attack goal]
   PRECONDITIONS: [required state]
   STEPS:
     1. [specific action]
     2. [expected outcome]
     3. [exploitation]
   WHY IT WORKS: [reference code change]
   IMPACT: [severity + scope]
   ```

---

#### Phase 2: Test Coverage Analysis

**Identify coverage gaps:**
```bash
# Production code changes (exclude tests)
git diff <range> --name-only | grep -v "test"

# Test changes
git diff <range> --name-only | grep "test"

# For each changed function, search for tests
grep -r "test.*functionName" test/ --include="*.sol" --include="*.js"
```

**Risk elevation rules:**
- NEW function + NO tests → Elevate risk MEDIUM→HIGH
- MODIFIED validation + UNCHANGED tests → HIGH RISK
- Complex logic (>20 lines) + NO tests → HIGH RISK

---

#### Phase 3: Blast Radius Analysis

**Calculate impact:**
```bash
# Count callers for each modified function
grep -r "functionName(" --include="*.sol" . | wc -l
```

**Classify blast radius:**
- 1-5 calls: LOW
- 6-20 calls: MEDIUM
- 21-50 calls: HIGH
- 50+ calls: CRITICAL

**Priority matrix:**

| Change Risk | Blast Radius | Priority | Analysis Depth |
|-------------|--------------|----------|----------------|
| HIGH | CRITICAL | P0 | Deep + all deps |
| HIGH | HIGH/MEDIUM | P1 | Deep |
| HIGH | LOW | P2 | Standard |
| MEDIUM | CRITICAL/HIGH | P1 | Standard + callers |

---

#### Phase 4: Deep Context Analysis

**If `audit-context-building` skill is available**, invoke it to help answer all the questions below for each HIGH RISK changed function:

```bash
# Run audit-context-building on the changed function and its dependencies
audit-context-building --scope [file containing changed function] --focus flow-analysis,call-graphs,invariants,root-cause
```

**The audit-context-building skill will help you answer:**

1. **Map complete function flow:**
   - Entry conditions (preconditions, requires, modifiers)
   - State reads (which variables accessed)
   - State writes (which variables modified)
   - External calls (to contracts, APIs, system)
   - Return values and side effects

2. **Trace internal calls:**
   - List all functions called
   - Recursively map their flows
   - Build complete call graph

3. **Trace external calls:**
   - Identify trust boundaries crossed
   - List assumptions about external behavior
   - Check for reentrancy risks

4. **Identify invariants:**
   - What must ALWAYS be true?
   - What must NEVER happen?
   - Are invariants maintained after changes?

5. **Five Whys root cause:**
   - WHY was this code changed?
   - WHY did the original code exist?
   - WHY might this break?
   - WHY is this approach chosen?
   - WHY could this fail in production?

**If `audit-context-building` skill is NOT available**, manually perform the line-by-line analysis above using Read, Grep, and code tracing.

**Cross-cutting pattern detection:**
```bash
# Find repeated validation patterns
grep -r "require.*amount > 0" --include="*.sol" .
grep -r "onlyOwner" --include="*.sol" .

# Check if any removed in diff
git diff <range> | grep "^-.*require.*amount > 0"
```

**Flag if removal breaks defense-in-depth.**

---

**Next steps:**
- For HIGH RISK changes, proceed to "Adversarial Vulnerability Analysis (Phase 5)" below
- For report generation, see "Report Generation (Phase 6)" below

### Adversarial Vulnerability Analysis (Phase 5)

Structured methodology for finding vulnerabilities through attacker modeling.

**When to use:** After completing deep context analysis (Phase 4), apply this to all HIGH RISK changes.

---

#### 1. Define Specific Attacker Model

**WHO is the attacker?**
- Unauthenticated external user
- Authenticated regular user
- Malicious administrator
- Compromised contract/service
- Front-runner/MEV bot

**WHAT access/privileges do they have?**
- Public API access only
- Authenticated user role
- Specific permissions/tokens
- Contract call capabilities

**WHERE do they interact with the system?**
- Specific HTTP endpoints
- Smart contract functions
- RPC interfaces
- External APIs

---

#### 2. Identify Concrete Attack Vectors

```
ENTRY POINT: [Exact function/endpoint attacker can access]

ATTACK SEQUENCE:
1. [Specific API call/transaction with parameters]
2. [How this reaches the vulnerable code]
3. [What happens in the vulnerable code]
4. [Impact achieved]

PROOF OF ACCESSIBILITY:
- Show the function is public/external
- Demonstrate attacker has required permissions
- Prove attack path exists through actual interfaces
```

---

#### 3. Rate Realistic Exploitability

**EASY:** Exploitable via public APIs with no special privileges
- Single transaction/call
- Common user access level
- No complex conditions required

**MEDIUM:** Requires specific conditions or elevated privileges
- Multiple steps or timing requirements
- Elevated but obtainable privileges
- Specific system state needed

**HARD:** Requires privileged access or rare conditions
- Admin/owner privileges needed
- Rare edge case conditions
- Significant resources required

---

#### 4. Build Complete Exploit Scenario

```
ATTACKER STARTING POSITION:
[What the attacker has at the beginning]

STEP-BY-STEP EXPLOITATION:
Step 1: [Concrete action through accessible interface]
  - Command: [Exact call/request]
  - Parameters: [Specific values]
  - Expected result: [What happens]

Step 2: [Next action]
  - Command: [Exact call/request]
  - Why this works: [Reference to code change]
  - System state change: [What changed]

Step 3: [Final impact]
  - Result: [Concrete harm achieved]
  - Evidence: [How to verify impact]

CONCRETE IMPACT:
[Specific, measurable impact - not "could cause issues"]
- Exact amount of funds drained
- Specific privileges escalated
- Particular data exposed
```

---

#### 5. Cross-Reference with Baseline Context

From baseline analysis (see "Pre-Analysis: Baseline Context Building" under "Differential Review Methodology" above), check:
- Does this violate a system-wide invariant?
- Does this break a trust boundary?
- Does this bypass a validation pattern?
- Is this a regression of a previous fix?

---

#### Vulnerability Report Template

Generate this for each finding:

```markdown
## [SEVERITY] Vulnerability Title

**Attacker Model:**
- WHO: [Specific attacker type]
- ACCESS: [Exact privileges]
- INTERFACE: [Specific entry point]

**Attack Vector:**
[Step-by-step exploit through accessible interfaces]

**Exploitability:** EASY/MEDIUM/HARD
**Justification:** [Why this rating]

**Concrete Impact:**
[Specific, measurable harm - not theoretical]

**Proof of Concept:**
```code
// Exact code to reproduce
```

**Root Cause:**
[Reference specific code change at file.sol:L123]

**Blast Radius:** [N callers affected]
**Baseline Violation:** [Which invariant/pattern broken]
```

---

#### Example: Complete Adversarial Analysis

**Change:** Removed `require(amount > 0)` check from `withdraw()` function

##### 1. Attacker Model
- **WHO:** Unauthenticated external user
- **ACCESS:** Can call public contract functions
- **INTERFACE:** `withdraw(uint256 amount)` at 0x1234...

##### 2. Attack Vector
**ENTRY POINT:** `withdraw(0)`

**ATTACK SEQUENCE:**
1. Call `withdraw(0)` from attacker address
2. Code bypasses amount check (removed)
3. Withdraw event emitted with 0 amount
4. Accounting updated incorrectly

**PROOF:** Function is `external`, no auth required

##### 3. Exploitability
**RATING:** EASY
- Single transaction
- Public function
- No special state required

##### 4. Exploit Scenario
**ATTACKER POSITION:** Has user account with 0 balance

**EXPLOITATION:**
```solidity
Step 1: attacker.withdraw(0)
  - Passes removed validation
  - Emits Withdraw(user, 0)
  - Updates withdrawnAmount[user] += 0

Step 2: Off-chain indexer sees Withdraw event
  - Credits attacker for 0 withdrawal
  - But accounting thinks withdrawal happened

Step 3: Accounting mismatch exploited
  - Total supply decremented
  - User balance not changed
  - System invariants broken
```

**IMPACT:**
- Protocol accounting corrupted
- Can be used to manipulate LP calculations
- Estimated $50K impact on pool prices

##### 5. Baseline Violation
- Violates invariant: "All withdrawals must transfer non-zero value"
- Breaks validation pattern: Amount checks present in all other value transfers
- Regression: Check added in commit abc123 "Fix zero-amount exploit"

---

**Next:** Document all findings in final report (see "Report Generation (Phase 6)" below)

### Report Generation (Phase 6)

Comprehensive markdown report structure and formatting guidelines.

---

#### Report Structure

Generate markdown report with these mandatory sections:

##### 1. Executive Summary

- Severity distribution table
- Risk assessment (CRITICAL/HIGH/MEDIUM/LOW)
- Final recommendation (APPROVE/REJECT/CONDITIONAL)
- Key metrics (test gaps, blast radius, red flags)

**Template:**
```markdown
# Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | X |
| 🟠 HIGH | Y |
| 🟡 MEDIUM | Z |
| 🟢 LOW | W |

**Overall Risk:** CRITICAL/HIGH/MEDIUM/LOW
**Recommendation:** APPROVE/REJECT/CONDITIONAL

**Key Metrics:**
- Files analyzed: X/Y (Z%)
- Test coverage gaps: N functions
- High blast radius changes: M functions
- Security regressions detected: P
```

---

##### 2. What Changed

- Commit timeline with visual
- File summary table
- Lines changed stats

**Template:**
```markdown
## What Changed

**Commit Range:** `base..head`
**Commits:** X
**Timeline:** YYYY-MM-DD to YYYY-MM-DD

| File | +Lines | -Lines | Risk | Blast Radius |
|------|--------|--------|------|--------------|
| file1.sol | +50 | -20 | HIGH | CRITICAL |
| file2.sol | +10 | -5 | MEDIUM | LOW |

**Total:** +N, -M lines across K files
```

---

##### 3. Critical Findings

For each HIGH/CRITICAL issue:

```markdown
### [SEVERITY] Title

**File**: path/to/file.ext:lineNumber
**Commit**: hash
**Blast Radius**: N callers (HIGH/MEDIUM/LOW)
**Test Coverage**: YES/NO/PARTIAL

**Description**: [clear explanation]

**Historical Context**:
- Git blame: Added in commit X (date)
- Message: "[original commit message]"
- [Why this code existed]

**Attack Scenario**:
[Concrete exploitation steps from adversarial.md]

**Proof of Concept**:
```code demonstrating issue```

**Recommendation**:
[Specific fix with code]
```

**Example:**
```markdown
### 🔴 CRITICAL: Authorization Bypass in Withdraw

**File**: TokenVault.sol:156
**Commit**: abc123def
**Blast Radius**: 23 callers (HIGH)
**Test Coverage**: NO

**Description**:
Removed `require(msg.sender == owner)` check allows any user to withdraw funds.

**Historical Context**:
- Git blame: Added 2024-06-15 (commit def456)
- Message: "Add owner check per audit finding #45"
- Code existed to prevent unauthorized withdrawals

**Attack Scenario**:
1. Attacker calls `withdraw(1000 ether)`
2. No authorization check (removed)
3. 1000 ETH transferred to attacker
4. Protocol funds drained

**Proof of Concept**:
```solidity
// As any address
vault.withdraw(vault.balance());
// Success - funds stolen
```

**Recommendation**:
```solidity
function withdraw(uint256 amount) external {
+   require(msg.sender == owner, "Unauthorized");
    // ... rest of function
}
```
```

---

##### 4. Test Coverage Analysis

- Coverage statistics
- Untested changes list
- Risk assessment

**Template:**
```markdown
## Test Coverage Analysis

**Coverage:** X% of changed code

**Untested Changes:**
| Function | Risk | Impact |
|----------|------|--------|
| functionA() | HIGH | No validation tests |
| functionB() | MEDIUM | Logic untested |

**Risk Assessment:**
N HIGH-risk functions without tests → Recommend blocking merge
```

---

##### 5. Blast Radius Analysis

- High-impact functions table
- Dependency graph
- Impact quantification

**Template:**
```markdown
## Blast Radius Analysis

**High-Impact Changes:**
| Function | Callers | Risk | Priority |
|----------|---------|------|----------|
| transfer() | 89 | HIGH | P0 |
| validate() | 45 | MEDIUM | P1 |
```

---

##### 6. Historical Context

- Security-related removals
- Regression risks
- Commit message red flags

**Template:**
```markdown
## Historical Context

**Security-Related Removals:**
- Line 45: `require` removed (added 2024-03 for CVE-2024-1234)
- Line 78: Validation removed (added 2023-12 "security hardening")

**Regression Risks:**
- Code pattern removed in commit X, re-added in commit Y
```

---

##### 7. Recommendations

- Immediate actions (blocking)
- Before production (tracking)
- Technical debt (future)

**Template:**
```markdown
## Recommendations

### Immediate (Blocking)
- [ ] Fix CRITICAL issue in TokenVault.sol:156
- [ ] Add tests for withdraw() function

### Before Production
- [ ] Security audit of auth changes
- [ ] Load test blast radius functions

### Technical Debt
- [ ] Refactor validation pattern consistency
```

---

##### 8. Analysis Methodology

- Strategy used (DEEP/FOCUSED/SURGICAL)
- Files analyzed
- Coverage estimate
- Techniques applied
- Limitations
- Confidence level

**Template:**
```markdown
## Analysis Methodology

**Strategy:** FOCUSED (80 files, medium codebase)

**Analysis Scope:**
- Files reviewed: 45/80 (56%)
- HIGH RISK: 100% coverage
- MEDIUM RISK: 60% coverage
- LOW RISK: Excluded

**Techniques:**
- Git blame on all removals
- Blast radius calculation
- Test coverage analysis
- Adversarial modeling for HIGH RISK

**Limitations:**
- Did not analyze external dependencies
- Limited to 1-hop caller analysis

**Confidence:** HIGH for analyzed scope, MEDIUM overall
```

---

##### 9. Appendices

- Commit reference table
- Key definitions
- Contact info

---

#### Formatting Guidelines

**Tables:** Use markdown tables for structured data

**Code blocks:** Always include syntax highlighting
```solidity
// Solidity code
```
```rust
// Rust code
```

**Status indicators:**
- ✅ Complete
- ⚠️ Warning
- ❌ Failed/Blocked

**Severity:**
- 🔴 CRITICAL
- 🟠 HIGH
- 🟡 MEDIUM
- 🟢 LOW

**Before/After comparisons:**
```markdown
**BEFORE:**
```code
old code
```

**AFTER:**
```code
new code
```
```

**Line number references:** Always include
- Format: `file.sol:L123`
- Link to commit: `file.sol:L123 (commit abc123)`

---

#### File Naming and Location

**Output location:** `<context_handoff_dir>/review.md`, the one review file you already write. Put the full report (every section above) in that file; do not create a second, separately named report file anywhere else.

---

#### User Notification Template

After generating report:

```markdown
Report generated successfully!

📄 File: [filename]
📁 Location: [path]
📏 Size: XX KB
⏱️ Review Time: ~X hours

Summary:
- X findings (Y critical, Z high)
- Final recommendation: APPROVE/REJECT/CONDITIONAL
- Confidence: HIGH/MEDIUM/LOW

Next steps:
- Review findings in detail
- Address CRITICAL/HIGH issues before merge
```

---

#### Error Handling

There is exactly one place to write the report. If writing `<context_handoff_dir>/review.md` fails, do not fall back to another location or to chat output; report the failure.

**Always prioritize persistent artifact generation over ephemeral chat output.**

### Common Vulnerability Patterns

Quick reference for detecting common security issues in code changes.

**Specialized Pattern Resources:**
For specific contexts, reference these additional pattern databases:

**Domain-Specific:**
- `domain-specific-audits/defi-bridges/resources/` - 127 bridge-specific findings
- `domain-specific-audits/tick-math/resources/` - 81 tick math findings
- `domain-specific-audits/merkle-trees/resources/` - 67 merkle tree findings
- [Check `domain-specific-audits/skills/` for additional domains]

**Solidity-Specific:**
- `not-so-smart-contracts` - Automated Solidity vulnerability detectors
- `token-integration-analyzer` - Token integration safety patterns
- `building-secure-contracts/development-guidelines` - Solidity best practices

These complement the generic patterns below.

---

#### Security Regressions

**Pattern:** Previously removed code is re-added

**Detection:**
```bash
# Code previously removed for security
git log -S "pattern" --all --grep="security\|fix\|CVE"
```

**Red flags:**
- Commit message contains "security", "fix", "CVE", "vulnerability"
- Code removed <6 months ago
- No explanation in current PR for re-addition

**Example:**
```solidity
// Removed in commit abc123 "Fix reentrancy CVE-2024-1234"
// Re-added in current PR
function emergencyWithdraw() {
    // REGRESSION: Reentrancy vulnerability re-introduced
}
```

---

#### Double Decrease/Increase Bugs

**Pattern:** Same accounting operation twice for same event

**Detection:** Look for two state updates in related functions for same logical action

**Example:**
```solidity
// Request exit
function requestExit() {
    balance[user] -= amount;  // First decrease
}

// Process exit
function processExit() {
    balance[user] -= amount;  // Second decrease - BUG!
}
```

**Impact:** User balance decremented twice, protocol loses funds

---

#### Missing Validation

**Pattern:** Removed `require`/`assert`/`check` without replacement

**Detection:**
```bash
git diff <range> | grep "^-.*require"
git diff <range> | grep "^-.*assert"
git diff <range> | grep "^-.*revert"
```

**Questions to ask:**
- Was validation moved elsewhere?
- Is it redundant (defensive programming)?
- Does removal expose vulnerability?

**Example:**
```diff
function withdraw(uint256 amount) {
-   require(amount > 0, "Zero amount");
-   require(amount <= balance[msg.sender], "Insufficient");
    balance[msg.sender] -= amount;
}
```

**Risk:** Zero-amount withdrawals, underflow attacks now possible

---

#### Underflow/Overflow

**Pattern:** Arithmetic without SafeMath or checks

**Detection:**
- Look for `+`, `-`, `*`, `/` in Solidity <0.8.0
- Check if SafeMath removed
- Look for unchecked blocks in Solidity >=0.8.0

**Example:**
```solidity
// Solidity 0.7 without SafeMath
balance[user] -= amount;  // Can underflow if amount > balance

// Solidity 0.8+ with unchecked
unchecked {
    balance[user] -= amount;  // Deliberately bypasses overflow check
}
```

**Risk:** Integer wrap-around leads to incorrect balances

---

#### Reentrancy

**Pattern:** External call before state update

**Detection:** Look for CEI (Checks-Effects-Interactions) pattern violations

**Example:**
```solidity
// VULNERABLE: External call before state update
function withdraw() {
    uint amount = balances[msg.sender];
    (bool success,) = msg.sender.call{value: amount}("");  // External call FIRST
    require(success);
    balances[msg.sender] = 0;  // State update AFTER
}

// SAFE: State update before external call
function withdraw() {
    uint amount = balances[msg.sender];
    balances[msg.sender] = 0;  // State update FIRST
    (bool success,) = msg.sender.call{value: amount}("");  // External call AFTER
    require(success);
}
```

**Impact:** Attacker can recursively call withdraw() before balance is zeroed

---

#### Access Control Bypass

**Pattern:** Removed or relaxed permission checks

**Detection:**
```bash
git diff <range> | grep "^-.*onlyOwner"
git diff <range> | grep "^-.*onlyAdmin"
git diff <range> | grep "^-.*require.*msg.sender"
```

**Questions:**
- Who can now call this function?
- What's the new trust model?
- Was check moved to caller?

**Example:**
```diff
- function setConfig(uint value) external onlyOwner {
+ function setConfig(uint value) external {
      config = value;
  }
```

**Risk:** Any user can now modify critical configuration

---

#### Race Conditions / Front-Running

**Pattern:** State-dependent logic without protection

**Detection:** Look for two-step processes without commit-reveal or timelocks

**Example:**
```solidity
// Step 1: Approve
function approve(address spender, uint amount) {
    allowance[msg.sender][spender] = amount;
}

// Step 2: User can front-run between approval changes
// Attacker sees tx changing approval from 100 to 50
// Front-runs to spend 100, then spends 50 after = 150 total
```

**Risk:** MEV/front-running exploits state transitions

---

#### Timestamp Manipulation

**Pattern:** Security logic depending on `block.timestamp`

**Detection:**
```bash
grep -r "block.timestamp" --include="*.sol"
grep -r "now\b" --include="*.sol"  # Solidity <0.7
```

**Example:**
```solidity
// VULNERABLE
require(block.timestamp > deadline, "Too early");
// Miner can manipulate timestamp by ~15 seconds

// SAFER
require(block.number > deadlineBlock, "Too early");
// Block numbers are harder to manipulate
```

**Risk:** Miners can manipulate timestamps within tolerance

---

#### Unchecked Return Values

**Pattern:** External call without checking success

**Detection:**
```bash
git diff <range> | grep "\.call\|\.send\|\.transfer"
```

**Example:**
```solidity
// VULNERABLE
token.transfer(user, amount);  // Ignores return value

// SAFE
require(token.transfer(user, amount), "Transfer failed");
// Or use SafeERC20 wrapper
```

**Risk:** Silent failures lead to inconsistent state

---

#### Denial of Service

**Pattern:** Unbounded loops, external call reverts blocking execution

**Detection:**
- Arrays that grow without limit
- Loops over user-controlled array
- Critical function depends on external call success

**Example:**
```solidity
// DOS: Attacker adds many users, making loop too expensive
function distributeRewards() {
    for (uint i = 0; i < users.length; i++) {
        users[i].transfer(reward);  // Runs out of gas
    }
}
```

**Risk:** Function becomes unusable due to gas limits

---

#### Quick Detection Commands

**Find removed security checks:**
```bash
git diff <range> | grep "^-" | grep -E "require|assert|revert"
```

**Find new external calls:**
```bash
git diff <range> | grep "^+" | grep -E "\.call|\.delegatecall|\.staticcall"
```

**Find changed access modifiers:**
```bash
git diff <range> | grep -E "onlyOwner|onlyAdmin|internal|private|public|external"
```

**Find arithmetic changes:**
```bash
git diff <range> | grep -E "\+|\-|\*|/"
```

---

**For detailed analysis workflow, see "Differential Review Methodology" above**
**For building exploit scenarios, see "Adversarial Vulnerability Analysis (Phase 5)" above**

Adapted from github.com/trailofbits/skills (plugins/differential-review) @ 82fe822, licensed CC-BY-SA-4.0. Attribution: Trail of Bits.
