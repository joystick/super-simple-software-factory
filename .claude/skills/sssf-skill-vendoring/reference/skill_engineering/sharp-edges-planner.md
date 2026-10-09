<!-- sssf:vendored
source: ~/Projects/training/super-simple-software-factory/downloads/trailofbits-skills/plugins/sharp-edges/skills/sharp-edges/SKILL.md
date: 2026-10-09
sha256: 3b69a709c2f8f0cfcf57d40a3186e166f307865cc8ed924be4098e549a121e9c
-->
<!-- sssf:flattened
kept: references/config-patterns.md sha256:1d99f2716f7bef18efe71015ce0c56e0f4961c042faa503d796d6d4d1626fdc6
kept: references/lang-rust.md sha256:3d14993ea70b2b2df3fc0f388cbd1631470895c27ccbd9d764296d1da8f5b6ee
dropped: references/crypto-apis.md, references/auth-patterns.md, references/case-studies.md -- weather-report is a Rust/Axum routing service, not an auth or crypto library; plan-time prevention needs the config and language footguns (the reviewer's sharp-edges.md carries the full set)
dropped: references/lang-c.md, references/lang-csharp.md, references/lang-go.md, references/lang-java.md, references/lang-javascript.md, references/lang-kotlin.md, references/lang-php.md, references/lang-python.md, references/lang-ruby.md, references/lang-swift.md -- other stacks; weather-report is Rust
dropped: references/language-specific.md -- combined multi-language quick reference; the Rust guide is merged instead
dropped: agents/openai.yaml -- harness display metadata, no prompt content
dropped: assets/trail-of-bits-mark.svg -- image, no prompt content
dropped: SKILL.md "## Agent" section -- dispatches a sharp-edges-analyzer agent that is not vendored; the planner cannot call it
dropped: SKILL.md Phase 4 steps "Reproduce the misuse: Write minimal code demonstrating the footgun" and "Test mitigations" -- the planner writes only specs/ and implements nothing; replaced with recording each sharp edge as a builder test at a named seam in plan.md's Seams list, judging exploitability on paper, and running any probe from a scratch dir outside the repo ("Verify exploitability" and "Check documentation" kept)
dropped: SKILL.md "## References" links and language table -- content merged into that section; rewritten as an intro naming the merged subsections, rows for dropped references and other languages removed
dropped: SKILL.md two [config-patterns.md](references/config-patterns.md#unvalidated-constructor-parameters) links -- rewritten to point at "Unvalidated Constructor Parameters" under "Configuration Security Patterns" (below from Configuration Cliffs, above from the Quality Checklist)
dropped: references/*.md H1s -- demoted to ### subsections of "## References" (kept as headings so each reference stays delimited); their ## and ### headings demoted to #### and #####
-->

---
name: sharp-edges
description: "Identifies error-prone APIs, dangerous configurations, and footgun designs that enable security mistakes. Use when reviewing API designs, configuration schemas, cryptographic library ergonomics, or evaluating whether code follows 'secure by default' and 'pit of success' principles. Triggers: footgun, misuse-resistant, secure defaults, API usability, dangerous configuration."
allowed-tools: Read Grep Glob
---

# Sharp Edges Analysis

Evaluates whether APIs, configurations, and interfaces are resistant to developer misuse. Identifies designs where the "easy path" leads to insecurity.

## When to Use

- Reviewing API or library design decisions
- Auditing configuration schemas for dangerous options
- Evaluating cryptographic API ergonomics
- Assessing authentication/authorization interfaces
- Reviewing any code that exposes security-relevant choices to developers

## When NOT to Use

- Implementation bugs (use standard code review)
- Business logic flaws (use domain-specific analysis)
- Performance optimization (different concern)

## Core Principle

**The pit of success**: Secure usage should be the path of least resistance. If developers must understand cryptography, read documentation carefully, or remember special rules to avoid vulnerabilities, the API has failed.

## Rationalizations to Reject

| Rationalization | Why It's Wrong | Required Action |
|-----------------|----------------|-----------------|
| "It's documented" | Developers don't read docs under deadline pressure | Make the secure choice the default or only option |
| "Advanced users need flexibility" | Flexibility creates footguns; most "advanced" usage is copy-paste | Provide safe high-level APIs; hide primitives |
| "It's the developer's responsibility" | Blame-shifting; you designed the footgun | Remove the footgun or make it impossible to misuse |
| "Nobody would actually do that" | Developers do everything imaginable under pressure | Assume maximum developer confusion |
| "It's just a configuration option" | Config is code; wrong configs ship to production | Validate configs; reject dangerous combinations |
| "We need backwards compatibility" | Insecure defaults can't be grandfather-claused | Deprecate loudly; force migration |

## Sharp Edge Categories

### 1. Algorithm/Mode Selection Footguns

APIs that let developers choose algorithms invite choosing wrong ones.

**The JWT Pattern** (canonical example):
- Header specifies algorithm: attacker can set `"alg": "none"` to bypass signatures
- Algorithm confusion: RSA public key used as HMAC secret when switching RS256→HS256
- Root cause: Letting untrusted input control security-critical decisions

**Detection patterns:**
- Function parameters like `algorithm`, `mode`, `cipher`, `hash_type`
- Enums/strings selecting cryptographic primitives
- Configuration options for security mechanisms

**Example - PHP password_hash allowing weak algorithms:**
```php
// DANGEROUS: allows crc32, md5, sha1
password_hash($password, PASSWORD_DEFAULT); // Good - no choice
hash($algorithm, $password); // BAD: accepts "crc32"
```

### 2. Dangerous Defaults

Defaults that are insecure, or zero/empty values that disable security.

**The OTP Lifetime Pattern:**
```python
# What happens when lifetime=0?
def verify_otp(code, lifetime=300):  # 300 seconds default
    if lifetime == 0:
        return True  # OOPS: 0 means "accept all"?
        # Or does it mean "expired immediately"?
```

**Detection patterns:**
- Timeouts/lifetimes that accept 0 (infinite? immediate expiry?)
- Empty strings that bypass checks
- Null values that skip validation
- Boolean defaults that disable security features
- Negative values with undefined semantics

**Questions to ask:**
- What happens with `timeout=0`? `max_attempts=0`? `key=""`?
- Is the default the most secure option?
- Can any default value disable security entirely?

### 3. Primitive vs. Semantic APIs

APIs that expose raw bytes instead of meaningful types invite type confusion.

**The Libsodium vs. Halite Pattern:**

```php
// Libsodium (primitives): bytes are bytes
sodium_crypto_box($message, $nonce, $keypair);
// Easy to: swap nonce/keypair, reuse nonces, use wrong key type

// Halite (semantic): types enforce correct usage
Crypto::seal($message, new EncryptionPublicKey($key));
// Wrong key type = type error, not silent failure
```

**Detection patterns:**
- Functions taking `bytes`, `string`, `[]byte` for distinct security concepts
- Parameters that could be swapped without type errors
- Same type used for keys, nonces, ciphertexts, signatures

**The comparison footgun:**
```go
// Timing-safe comparison looks identical to unsafe
if hmac == expected { }           // BAD: timing attack
if hmac.Equal(mac, expected) { }  // Good: constant-time
// Same types, different security properties
```

### 4. Configuration Cliffs

One wrong setting creates catastrophic failure, with no warning.

**Detection patterns:**
- Boolean flags that disable security entirely
- String configs that aren't validated
- Combinations of settings that interact dangerously
- Environment variables that override security settings
- Constructor parameters with sensible defaults but no validation (callers can override with insecure values)

**Examples:**
```yaml
# One typo = disaster
verify_ssl: fasle  # Typo silently accepted as truthy?

# Magic values
session_timeout: -1  # Does this mean "never expire"?

# Dangerous combinations accepted silently
auth_required: true
bypass_auth_for_health_checks: true
health_check_path: "/"  # Oops
```

```php
// Sensible default doesn't protect against bad callers
public function __construct(
    public string $hashAlgo = 'sha256',  // Good default...
    public int $otpLifetime = 120,       // ...but accepts md5, 0, etc.
) {}
```

See "Unvalidated Constructor Parameters" under "Configuration Security Patterns" below for detailed patterns.

### 5. Silent Failures

Errors that don't surface, or success that masks failure.

**Detection patterns:**
- Functions returning booleans instead of throwing on security failures
- Empty catch blocks around security operations
- Default values substituted on parse errors
- Verification functions that "succeed" on malformed input

**Examples:**
```python
# Silent bypass
def verify_signature(sig, data, key):
    if not key:
        return True  # No key = skip verification?!

# Return value ignored
signature.verify(data, sig)  # Throws on failure
crypto.verify(data, sig)     # Returns False on failure
# Developer forgets to check return value
```

### 6. Stringly-Typed Security

Security-critical values as plain strings enable injection and confusion.

**Detection patterns:**
- SQL/commands built from string concatenation
- Permissions as comma-separated strings
- Roles/scopes as arbitrary strings instead of enums
- URLs constructed by joining strings

**The permission accumulation footgun:**
```python
permissions = "read,write"
permissions += ",admin"  # Too easy to escalate

# vs. type-safe
permissions = {Permission.READ, Permission.WRITE}
permissions.add(Permission.ADMIN)  # At least it's explicit
```

## Analysis Workflow

### Phase 1: Surface Identification

1. **Map security-relevant APIs**: authentication, authorization, cryptography, session management, input validation
2. **Identify developer choice points**: Where can developers select algorithms, configure timeouts, choose modes?
3. **Find configuration schemas**: Environment variables, config files, constructor parameters

### Phase 2: Edge Case Probing

For each choice point, ask:
- **Zero/empty/null**: What happens with `0`, `""`, `null`, `[]`?
- **Negative values**: What does `-1` mean? Infinite? Error?
- **Type confusion**: Can different security concepts be swapped?
- **Default values**: Is the default secure? Is it documented?
- **Error paths**: What happens on invalid input? Silent acceptance?

### Phase 3: Threat Modeling

Consider three adversaries:

1. **The Scoundrel**: Actively malicious developer or attacker controlling config
   - Can they disable security via configuration?
   - Can they downgrade algorithms?
   - Can they inject malicious values?

2. **The Lazy Developer**: Copy-pastes examples, skips documentation
   - Will the first example they find be secure?
   - Is the path of least resistance secure?
   - Do error messages guide toward secure usage?

3. **The Confused Developer**: Misunderstands the API
   - Can they swap parameters without type errors?
   - Can they use the wrong key/algorithm/mode by accident?
   - Are failure modes obvious or silent?

### Phase 4: Validate Findings

Validate on paper and in the plan, not in code. For each identified sharp edge:

1. **Record it as a test**: In `plan.md`'s Seams list, name the seam the builder tests it at and the test the builder must write there: the misuse, and the behavior that shows it is rejected or harmless
2. **Verify exploitability**: Does the misuse create a real vulnerability, or is it a style preference? Judge it from the code and its inputs; only a real vulnerability goes into the plan
3. **Check documentation**: Is the danger documented? (Documentation doesn't excuse bad design, but affects severity)
4. **Probe outside the repo**: If you run anything to confirm a finding, run it from a scratch directory outside the repository, never as a file in the working tree

If a finding seems questionable, return to Phase 2 and probe more edge cases.

## Severity Classification

| Severity | Criteria | Examples |
|----------|----------|----------|
| Critical | Default or obvious usage is insecure | `verify: false` default; empty password allowed |
| High | Easy misconfiguration breaks security | Algorithm parameter accepts "none" |
| Medium | Unusual but possible misconfiguration | Negative timeout has unexpected meaning |
| Low | Requires deliberate misuse | Obscure parameter combination |

## References

The reference material follows, one subsection per topic.

**By category:**

- **Configuration Patterns**: "Configuration Security Patterns" below

**By language** (general footguns, not crypto-specific): "Rust Sharp Edges" below.

### Configuration Security Patterns

Dangerous configuration patterns that enable security failures.

#### Zero/Empty/Null Semantics

##### The Lifetime Zero Problem

```yaml
# What does 0 mean?
session_timeout: 0    # Infinite timeout? Immediate expiry? Disabled?
token_lifetime: 0     # Never expires? Already expired? Use default?
max_attempts: 0       # No attempts allowed? Unlimited attempts?
```

**Real-world failures:**
- OTP libraries where `lifetime=0` means "accept any OTP regardless of age"
- Rate limiters where `max_attempts=0` disables rate limiting
- Session managers where `timeout=0` means "session never expires"

**Detection**: Any numeric security parameter that accepts 0.

**Fix**: Explicit constants, validation, or separate enable/disable flag.

```python
# BAD
def verify_otp(code: str, lifetime: int = 300):
    if lifetime <= 0:
        return True  # What??

# GOOD
def verify_otp(code: str, lifetime: int = 300):
    if lifetime <= 0:
        raise ValueError("lifetime must be positive")
```

##### Empty String Bypass

```python
# Passwords
if user_password == stored_hash:  # What if stored_hash is ""?

# API keys
if api_key == config.api_key:  # What if config is empty?
    grant_access()

# The empty string equals the empty string
"" == ""  # True - authentication bypassed
```

**Detection**: String comparisons for authentication without empty checks.

##### Null as "Skip"

```javascript
// DANGEROUS: null means "skip verification"
function verifySignature(data, signature, publicKey) {
    if (!publicKey) return true;  // No key = trust everything?
    return crypto.verify(data, signature, publicKey);
}

// DANGEROUS: null means "any value"
function checkRole(user, requiredRole) {
    if (!requiredRole) return true;  // No requirement = allow all?
    return user.roles.includes(requiredRole);
}
```

#### Boolean Traps

##### Security-Disabling Flags

```yaml
# Every one of these has caused real vulnerabilities
verify_ssl: false
validate_certificate: false
check_signature: false
require_auth: false
enable_csrf_protection: false
sanitize_input: false
```

**Pattern**: Any boolean that disables a security control.

**The typo problem:**
```yaml
verify_ssl: fasle   # Typo - what does the parser do?
verify_ssl: "false" # String "false" - truthy in many languages!
verify_ssl: 0       # Integer 0 - falsy, but is it valid?
```

##### Double Negatives

```yaml
# Confusing
disable_auth: false      # Auth enabled? Let me re-read...
skip_validation: false   # Validation runs? Think carefully...

# Clear
auth_enabled: true
validate_input: true
```

#### Magic Values

##### Sentinel Values in Security Parameters

```yaml
# What do these mean?
max_retries: -1      # Infinite? Error? Use default?
cache_ttl: -1        # Never expire? Disabled?
timeout_seconds: -1  # Wait forever? Use system default?

# Real vulnerability: connection pool with max_connections: -1
# meant "unlimited" - enabled DoS via connection exhaustion
```

##### Special String Values

```yaml
# Dangerous patterns
allowed_origins: "*"       # CORS wildcard
allowed_hosts: "any"       # Bypass host validation
log_level: "none"          # Disable security logging
password_policy: "disabled" # No password requirements
```

**Detection**: String configs that accept wildcards or "disable" keywords.

#### Combination Hazards

##### Conflicting Settings

```yaml
# Both true - which wins?
require_authentication: true
allow_anonymous_access: true

# Both specified - conflict
session_cookie_secure: true
force_http: true  # HTTP can't use Secure cookies

# Mutually exclusive
encryption_key: "..."
encryption_disabled: true
```

##### Precedence Confusion

```yaml
# In config file
verify_ssl: true

# But overrideable by environment?
VERIFY_SSL=false  # Which wins?

# And command line?
--no-verify-ssl   # Now there are three sources
```

**Fix**: Document precedence clearly; warn on conflicts; fail on contradictions.

#### Environment Variable Hazards

##### Sensitive Values in Environment

```bash
# Common but problematic
export DATABASE_PASSWORD="secret"
export API_KEY="sk_live_xxx"

# Risks:
# - Visible in process listings (ps aux)
# - Inherited by child processes
# - Logged in error dumps
# - Visible in container inspection
```

##### Override Attacks

```python
# Application trusts environment
debug = os.environ.get("DEBUG", "false") == "true"

# Attacker with environment access:
export DEBUG=true  # Enables verbose logging of secrets
```

**Detection**: Security settings controllable via environment without validation.

#### Path Traversal via Config

##### Unrestricted Path Configuration

```yaml
# User-controlled paths
log_file: "../../../etc/passwd"
upload_dir: "/etc/nginx/conf.d/"
template_dir: "../../../etc/shadow"

# Even "read-only" paths can leak secrets
config_include: "/etc/shadow"
certificate_file: "/proc/self/environ"
```

**Fix**: Validate paths; restrict to allowed directories; resolve and check.

#### Unvalidated Constructor Parameters

Configuration/parameter classes that accept security-relevant values without validation create "time bombs" - the insecure value is accepted silently at construction, then explodes later during use.

##### Algorithm Selection Without Allowlist

```php
// DANGEROUS: Accepts any string including weak algorithms
readonly class ServerConfig {
    public function __construct(
        public string $hashAlgo = 'sha256',  // Accepts 'md5', 'crc32', 'adler32'
        public string $cipher = 'aes-256-gcm', // Accepts 'des', 'rc4'
    ) {}
}

// Caller can pass insecure values:
new ServerConfig(hashAlgo: 'md5');  // Silently accepted!
```

**Detection**: Constructor parameters named `algo`, `algorithm`, `hash*`, `cipher`, `mode`, `*_type` that accept strings without validation.

**Fix**: Validate against an explicit allowlist at construction:

```php
public function __construct(public string $hashAlgo = 'sha256') {
    if (!in_array($hashAlgo, ['sha256', 'sha384', 'sha512'], true)) {
        throw new InvalidArgumentException("Disallowed hash algorithm: $hashAlgo");
    }
}
```

##### Timing Parameters Without Bounds

```php
// DANGEROUS: No minimum or maximum bounds
readonly class AuthConfig {
    public function __construct(
        public int $otpLifetime = 120,     // Accepts 0 (immediate expiry? infinite?)
        public int $sessionTimeout = 3600, // Accepts -1 (what does this mean?)
        public int $maxRetries = 5,        // Accepts 0 (no retries? unlimited?)
    ) {}
}

// All of these are silently accepted:
new AuthConfig(otpLifetime: 0);      // OTP always expired or never expires?
new AuthConfig(otpLifetime: 999999); // ~11 days - replay attacks!
new AuthConfig(maxRetries: -1);      // Unlimited retries = brute force
```

**Detection**: Numeric constructor parameters for `*lifetime`, `*timeout`, `*ttl`, `*duration`, `max_*`, `min_*`, `*_seconds`, `*_attempts` without range validation.

**Fix**: Enforce both minimum AND maximum bounds:

```php
public function __construct(public int $otpLifetime = 120) {
    if ($otpLifetime < 2) {
        throw new InvalidArgumentException("OTP lifetime too short (min: 2 seconds)");
    }
    if ($otpLifetime > 300) {
        throw new InvalidArgumentException("OTP lifetime too long (max: 300 seconds)");
    }
}
```

##### Hostname/URL Parameters Without Validation

```php
// DANGEROUS: No format validation
readonly class NetworkConfig {
    public function __construct(
        public string $hostname = 'localhost',  // Accepts anything
        public string $callbackUrl = '',        // Accepts malformed URLs
    ) {}
}

// Silently accepted:
new NetworkConfig(hostname: '../../../etc/passwd');
new NetworkConfig(hostname: 'localhost; rm -rf /');
new NetworkConfig(callbackUrl: 'javascript:alert(1)');
```

**Detection**: String constructor parameters named `host`, `hostname`, `domain`, `*_url`, `*_uri`, `endpoint`, `callback*` without validation.

**Fix**: Validate format at construction:

```php
public function __construct(public string $hostname = 'localhost') {
    if (!filter_var($hostname, FILTER_VALIDATE_DOMAIN, FILTER_FLAG_HOSTNAME)) {
        throw new InvalidArgumentException("Invalid hostname: $hostname");
    }
}
```

##### The "Sensible Default" Trap

Having a secure default does NOT protect you - callers can override it:

```php
// Default is secure...
public function __construct(
    public string $hashAlgo = 'sha256'  // Good default!
) {}

// ...but callers can still shoot themselves
$config = new Config(hashAlgo: 'md5');  // Oops
```

**The rule**: If a parameter affects security, validate it. Defaults only help developers who don't specify a value; validation protects everyone.

#### Configuration Validation Checklist

For configuration schemas, verify:

- [ ] **Zero/empty rejected**: Numeric security params require positive values
- [ ] **No empty passwords/keys**: Empty string authentication forbidden
- [ ] **No security-disabling booleans**: Or require confirmation/separate config
- [ ] **No magic values**: -1 and wildcards have defined, safe meanings
- [ ] **Conflict detection**: Contradictory settings produce errors
- [ ] **Precedence documented**: Clear order when multiple sources exist
- [ ] **Path validation**: User-provided paths restricted to safe directories
- [ ] **Type strictness**: "false" string not silently converted to boolean
- [ ] **Deprecation warnings**: Insecure legacy options warn loudly
- [ ] **Algorithm allowlist**: Crypto algorithm params validated against safe options
- [ ] **Timing bounds**: Lifetime/timeout params have both min AND max limits
- [ ] **Hostname/URL validation**: Network addresses validated at construction
- [ ] **Constructor validation**: All security params validated, not just defaulted

### Rust Sharp Edges

#### Integer Overflow Behavior Differs by Build

```rust
// In debug builds: panics
// In release builds: wraps silently!
let x: u8 = 255;
let y = x + 1;  // Debug: panic! Release: y = 0

fn calculate_size(count: usize, element_size: usize) -> usize {
    count * element_size  // Panics in debug, wraps in release
}
```

**The Problem**: Behavior differs between debug and release. Bugs may only manifest in production.

**Fix**: Use explicit methods:
```rust
// Wrapping (explicitly allows overflow)
let y = x.wrapping_add(1);

// Checked (returns Option)
let y = x.checked_add(1);  // None if overflow

// Saturating (clamps to max/min)
let y = x.saturating_add(1);  // 255 if would overflow

// Overflowing (returns value + overflow flag)
let (y, overflowed) = x.overflowing_add(1);
```

#### Unsafe Blocks

```rust
// DANGEROUS: Unsafe disables Rust's safety guarantees
unsafe {
    // Can dereference raw pointers
    let ptr: *const i32 = &42;
    let val = *ptr;

    // Can call unsafe functions
    libc::free(ptr as *mut libc::c_void);

    // Can access mutable statics
    GLOBAL_COUNTER += 1;

    // Can implement unsafe traits
}

// Real vulnerabilities from unsafe:
// - CVE-2019-15548: memory safety bug in slice::from_raw_parts
// - Many FFI-related vulnerabilities
```

**Audit Focus**: Every `unsafe` block should have a SAFETY comment explaining invariants.

```rust
// GOOD: Documented safety invariants
// SAFETY: ptr is valid for reads of `len` bytes,
// properly aligned, and the memory won't be mutated
// for the lifetime 'a
unsafe { std::slice::from_raw_parts(ptr, len) }
```

#### Mem::forget Skips Destructors

```rust
// DANGEROUS: Resources never cleaned up
let guard = mutex.lock().unwrap();
std::mem::forget(guard);  // Lock never released = deadlock

let file = File::open("data.txt")?;
std::mem::forget(file);  // File descriptor leaked

// Can be used to create memory unsafety with certain types
let mut vec = vec![1, 2, 3];
let ptr = vec.as_mut_ptr();
std::mem::forget(vec);  // Vec's memory leaked, but ptr still valid... maybe
```

**Note**: `mem::forget` is safe (not `unsafe`), but can cause resource leaks and logical bugs.

#### Panics and Unwinding

```rust
// DANGEROUS: Panic in FFI boundary is UB
#[no_mangle]
pub extern "C" fn called_from_c() {
    panic!("oops");  // Undefined behavior!
}

// SAFE: Catch panic at FFI boundary
#[no_mangle]
pub extern "C" fn called_from_c() -> i32 {
    match std::panic::catch_unwind(|| {
        might_panic();
    }) {
        Ok(_) => 0,
        Err(_) => -1,
    }
}

// DANGEROUS: Panic in Drop can abort
impl Drop for MyType {
    fn drop(&mut self) {
        if something_wrong() {
            panic!("in drop");  // If already unwinding, aborts!
        }
    }
}
```

#### Unwrap and Expect

```rust
// DANGEROUS: Panics on None/Err
let value = some_option.unwrap();  // Panics if None
let result = fallible_fn().unwrap();  // Panics if Err

// In libraries: propagate errors with ?
fn library_fn() -> Result<T, E> {
    let value = fallible_fn()?;  // Propagates error
    Ok(value)
}

// In binaries: use expect() with context
let config = load_config()
    .expect("failed to load config from config.toml");
```

#### Interior Mutability Pitfalls

```rust
// DANGEROUS: RefCell panics at runtime on borrow violations
use std::cell::RefCell;

let cell = RefCell::new(42);
let borrow1 = cell.borrow_mut();
let borrow2 = cell.borrow_mut();  // PANIC: already borrowed

// Can happen across function calls - hard to track
fn takes_ref(cell: &RefCell<i32>) {
    let _b = cell.borrow_mut();
    other_fn(cell);  // If this also borrows_mut: panic!
}

// SAFER: Use try_borrow_mut
if let Ok(mut borrow) = cell.try_borrow_mut() {
    *borrow += 1;
}
```

#### Send and Sync Misuse

```rust
// DANGEROUS: Incorrect Send/Sync implementations
struct MyWrapper(*mut SomeType);

// This is WRONG if SomeType isn't thread-safe:
unsafe impl Send for MyWrapper {}
unsafe impl Sync for MyWrapper {}

// Real vulnerability: Rc<T> is not Send/Sync for good reason
// Incorrectly marking a type as Send/Sync enables data races
```

#### Lifetime Elision Surprises

```rust
// The compiler infers lifetimes, but sometimes wrong
impl MyStruct {
    // Elided: fn get(&self) -> &str
    // Means:  fn get<'a>(&'a self) -> &'a str
    fn get(&self) -> &str {
        &self.data
    }
}

// But what if you return something else?
impl MyStruct {
    // WRONG: Elision assumes output lifetime = self lifetime
    fn get_static(&self) -> &str {
        "static string"  // Actually 'static, not 'self
    }

    // RIGHT: Be explicit
    fn get_static(&self) -> &'static str {
        "static string"
    }
}
```

#### Deref Coercion Confusion

```rust
// Can be confusing when method resolution happens
use std::ops::Deref;

struct Wrapper(String);
impl Deref for Wrapper {
    type Target = String;
    fn deref(&self) -> &String { &self.0 }
}

let w = Wrapper(String::from("hello"));
w.len();  // Calls String::len via Deref
w.capacity();  // Also String::capacity

// What if Wrapper has its own len()?
impl Wrapper {
    fn len(&self) -> usize { 42 }
}
w.len();  // Now calls Wrapper::len, not String::len
(*w).len();  // Explicitly calls String::len
```

#### Drop Order

```rust
// Fields dropped in declaration order
struct S {
    first: A,   // Dropped last
    second: B,  // Dropped first
}

// Can cause issues if B depends on A
struct Connection {
    pool: Arc<Pool>,      // Dropped second
    conn: PooledConn,     // Dropped first - needs pool!
}

// Fix: reorder fields, or use ManuallyDrop
```

#### Macro Hygiene Gaps

```rust
// macro_rules! has hygiene gaps
macro_rules! make_var {
    ($name:ident) => {
        let $name = 42;
    }
}

make_var!(x);
println!("{}", x);  // Works - x is in scope

// But: macros can capture identifiers unexpectedly
macro_rules! double {
    ($e:expr) => {
        { let x = $e; x + x }  // Shadows any x in $e!
    }
}

let x = 10;
double!(x + 1)  // Doesn't do what you expect
```

#### Detection Patterns

| Pattern | Risk |
|---------|------|
| `+`, `-`, `*` on integers | Overflow (release wraps) |
| `unsafe { }` | All bets off - audit carefully |
| `mem::forget()` | Resource leak, deadlock |
| `.unwrap()`, `.expect()` | Panic on None/Err |
| `RefCell::borrow_mut()` | Runtime panic on double borrow |
| `unsafe impl Send/Sync` | Potential data races |
| `extern "C" fn` without catch_unwind | UB on panic |
| Drop impl with panic | Double panic = abort |
| Complex deref chains | Method resolution confusion |

## Quality Checklist

Before concluding analysis:

- [ ] Probed all zero/empty/null edge cases
- [ ] Verified defaults are secure
- [ ] Checked for algorithm/mode selection footguns
- [ ] Tested type confusion between security concepts
- [ ] Considered all three adversary types
- [ ] Verified error paths don't bypass security
- [ ] Checked configuration validation
- [ ] Constructor params validated (not just defaulted) - see "Unvalidated Constructor Parameters" under "Configuration Security Patterns" above

Adapted from github.com/trailofbits/skills (plugins/sharp-edges) @ 82fe822, licensed CC-BY-SA-4.0. Attribution: Trail of Bits.
