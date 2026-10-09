<!-- sssf:vendored
source: ~/Projects/training/super-simple-software-factory/downloads/trailofbits-skills/plugins/sharp-edges/skills/sharp-edges/SKILL.md
date: 2026-10-09
sha256: 3b69a709c2f8f0cfcf57d40a3186e166f307865cc8ed924be4098e549a121e9c
-->
<!-- sssf:flattened
kept: references/crypto-apis.md sha256:8baddc83a1f964d6d8b15678d60a37c93029c18dc162bd7c00895e585ff1a825
kept: references/config-patterns.md sha256:1d99f2716f7bef18efe71015ce0c56e0f4961c042faa503d796d6d4d1626fdc6
kept: references/auth-patterns.md sha256:1fbf526ca1db7204f9ebb1bf4eb3c48c544676623d23e5d28e01f6f63c355be2
kept: references/case-studies.md sha256:2e81a320728b4597bf84c490176d5bf212f1e6ba6f87aafba61ad1734de35332
kept: references/lang-rust.md sha256:3d14993ea70b2b2df3fc0f388cbd1631470895c27ccbd9d764296d1da8f5b6ee
dropped: references/lang-c.md, references/lang-csharp.md, references/lang-go.md, references/lang-java.md, references/lang-javascript.md, references/lang-kotlin.md, references/lang-php.md, references/lang-python.md, references/lang-ruby.md, references/lang-swift.md -- other stacks; weather-report is Rust
dropped: references/language-specific.md -- combined multi-language quick reference; the Rust guide is merged instead
dropped: agents/openai.yaml -- harness display metadata, no prompt content
dropped: assets/trail-of-bits-mark.svg -- image, no prompt content
dropped: SKILL.md "## Agent" section -- dispatches a sharp-edges-analyzer agent that is not vendored; the reviewer cannot call it
dropped: SKILL.md "## References" links and language table -- content merged into that section; rewritten as an intro naming the merged subsections, rows for other languages removed
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

For each identified sharp edge:

1. **Reproduce the misuse**: Write minimal code demonstrating the footgun
2. **Verify exploitability**: Does the misuse create a real vulnerability?
3. **Check documentation**: Is the danger documented? (Documentation doesn't excuse bad design, but affects severity)
4. **Test mitigations**: Can the API be used safely with reasonable effort?

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

- **Cryptographic APIs**: "Cryptographic API Footguns" below
- **Configuration Patterns**: "Configuration Security Patterns" below
- **Authentication/Session**: "Authentication & Session Footguns" below
- **Real-World Case Studies**: "Real-World Case Studies" below (OpenSSL, GMP, etc.)

**By language** (general footguns, not crypto-specific): "Rust Sharp Edges" below.

### Cryptographic API Footguns

Detailed patterns for identifying misuse-prone cryptographic interfaces.

#### Algorithm Selection Anti-Patterns

##### The "alg" Header Attack (JWT)

The JSON Web Token standard allows the token itself to specify which algorithm to use for verification. This is catastrophically wrong.

**Attack 1: "none" algorithm**
```json
{"alg": "none", "typ": "JWT"}
```
Many libraries accept this and skip signature verification entirely.

**Attack 2: Algorithm confusion (RS256 → HS256)**
- Server expects RSA signature, uses public key for verification
- Attacker changes algorithm to HMAC, uses *public key* as HMAC secret
- Public key is public, so attacker can forge valid signatures

**Root cause**: Trusting untrusted input to select security mechanisms.

**Fix**: Never let data dictate algorithm. Use one algorithm, hardcoded.

##### Cipher Mode Parameters

```python
# DANGEROUS: mode is selectable
def encrypt(plaintext, key, mode="ECB"):  # ECB is never correct
    ...

# BAD: accepts any OpenSSL cipher string
cipher = OpenSSL::Cipher.new(user_selected_cipher)

# GOOD: no parameters
def encrypt(plaintext, key):  # internally uses AES-256-GCM
    ...
```

**Detection**: Parameters named `mode`, `cipher`, `algorithm`, `hash_type`

##### Hash Algorithm Downgrade

```php
// PHP's hash() accepts ANY algorithm
hash("crc32", $password);  // Valid call, terrible security
hash("md5", $password);    // Valid call, broken security
hash("sha256", $password); // Valid call, still wrong for passwords

// Password functions limit choices
password_hash($password, PASSWORD_ARGON2ID);  // Better
```

**Pattern**: APIs that accept algorithm as string instead of restricting to safe subset.

#### Key/Nonce/IV Confusion

##### Indistinguishable Byte Arrays

```go
// All three are just []byte - easy to swap
func Encrypt(plaintext, key, nonce []byte) []byte

// Easy mistakes:
Encrypt(plaintext, nonce, key)  // Swapped - compiles fine
Encrypt(plaintext, key, key)    // Reused key as nonce - compiles fine
```

**Fix**: Distinct types

```go
type EncryptionKey [32]byte
type Nonce [24]byte

func Encrypt(plaintext []byte, key EncryptionKey, nonce Nonce) []byte
// Now type system catches swaps
```

##### Nonce Reuse

```python
# DANGEROUS: nonce parameter with no guidance
def encrypt(plaintext, key, nonce):
    ...

# Developer "simplifies" by reusing:
nonce = b'\x00' * 12
encrypt(msg1, key, nonce)
encrypt(msg2, key, nonce)  # Catastrophic with GCM/ChaCha
```

**Fix**: Generate nonces internally, return them with ciphertext.

#### Comparison Footguns

##### Timing-Safe vs. Regular Comparison

```python
# These look identical but have different security properties
if computed_mac == expected_mac:  # VULNERABLE: timing attack
if hmac.compare_digest(computed_mac, expected_mac):  # Safe
```

**The problem**: Developers don't know to use special comparison. Default string equality is vulnerable.

**Detection**: Direct equality checks on MACs, signatures, hashes, tokens.

##### Boolean Confusion

```python
# Signature verification APIs
result = verify(signature, message, key)

# Some return True/False
if verify(...):  # Must check return value

# Some raise exceptions
verify(...)  # Failure = exception, no return to check

# Developers mixing these up = vulnerabilities
```

#### Padding Oracle Enablers

##### Raw Decryption APIs

```python
# DANGEROUS: returns plaintext even if padding invalid
def decrypt(ciphertext, key):
    # ... decrypt ...
    return unpad(plaintext)  # Throws on bad padding

# Attacker can distinguish:
# - Valid padding → success
# - Invalid padding → exception

# This distinction enables padding oracle attacks
```

**Fix**: Decrypt-then-MAC (or authenticated encryption). Never expose padding validity.

##### Error Message Differentiation

```
# DANGEROUS error messages
"Invalid padding"           # Padding oracle signal
"MAC verification failed"   # Different error = oracle
"Decryption failed"         # Good: single error for all failures
```

#### Key Derivation Footguns

##### Using Hashes Instead of KDFs

```python
# DANGEROUS: hash is not a KDF
key = hashlib.sha256(password.encode()).digest()

# Developer reasoning: "SHA-256 is secure"
# Reality: Fast hash enables brute force

# CORRECT: use actual KDF
key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
```

##### Password Storage Misuse

```python
# DANGEROUS: encryption is not password storage
encrypted_password = encrypt(password, master_key)
# Compromise of master_key = all passwords exposed

# CORRECT: one-way hash with salt
hashed_password = argon2.hash(password)
# No key to steal; each password salted differently
```

#### Safe API Design Checklist

For cryptographic APIs, verify:

- [ ] **No algorithm selection**: One safe algorithm, hardcoded
- [ ] **No mode selection**: GCM/ChaCha20-Poly1305 only, no ECB/CBC
- [ ] **Distinct types**: Keys, nonces, ciphertexts are different types
- [ ] **Internal nonce generation**: Don't require developer to provide
- [ ] **Authenticated encryption**: Encrypt-then-MAC or AEAD built in
- [ ] **Constant-time comparison**: Default or only comparison method
- [ ] **Uniform errors**: Same error for all decryption failures
- [ ] **KDF for passwords**: Argon2/scrypt/bcrypt, not raw hashes

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

### Authentication & Session Footguns

Patterns that make authentication and session management error-prone.

#### Password Handling

##### Comparison Vulnerabilities

```python
# DANGEROUS: Short-circuit evaluation
def check_password(user_input, stored):
    return user_input == stored  # Timing attack

# DANGEROUS: Empty password bypass
def check_password(user_input, stored):
    if not stored:
        return True  # No password set = access granted?
    return constant_time_compare(user_input, stored)

# DANGEROUS: Null bypass
def authenticate(username, password):
    user = get_user(username)
    if user is None:
        return None  # No user = return None
    if password == user.password:  # None == None if both None
        return user
```

##### Length Limits That Truncate

```python
# DANGEROUS: Password truncated before hashing
def hash_password(password: str) -> str:
    password = password[:72]  # bcrypt limit
    return bcrypt.hash(password)

# User sets: "password123" + 64 more characters + "IMPORTANT_ENTROPY"
# Stored: hash of just "password123" + first 61 characters
# Attacker only needs to brute force truncated version
```

**Fix**: Reject passwords over limit; don't silently truncate.

##### Validation Ordering

```python
# DANGEROUS: Username enumeration
def login(username, password):
    user = db.get_user(username)
    if not user:
        return "User not found"  # Reveals user doesn't exist
    if not verify_password(password, user.password_hash):
        return "Wrong password"  # Reveals user DOES exist
    return create_session(user)

# SECURE: Uniform error
def login(username, password):
    user = db.get_user(username)
    if not user or not verify_password(password, user.password_hash):
        return "Invalid credentials"
    return create_session(user)
```

#### Session Management

##### Session Fixation Enablers

```python
# DANGEROUS: Session ID accepted from request
def login(request):
    session_id = request.cookies.get("session") or generate_session_id()
    # Attacker gives victim a known session ID before login
    # After login, attacker knows victim's session
    sessions[session_id] = user
```

**Fix**: Always generate new session ID on authentication state change.

##### Token Generation Weakness

```python
# DANGEROUS: Predictable tokens
import time
session_id = hashlib.md5(str(time.time()).encode()).hexdigest()
# Attacker knows approximate login time = can guess session

# DANGEROUS: Insufficient entropy
session_id = ''.join(random.choice('abcdef') for _ in range(8))
# Only 6^8 = 1.6M possibilities

# SECURE: Cryptographic randomness
session_id = secrets.token_urlsafe(32)
```

##### Session Timeout Footguns

```python
# DANGEROUS: Timeout of 0 means "never"?
class SessionConfig:
    timeout_seconds: int = 3600  # 1 hour
    # What if someone sets 0? Infinite session?

# DANGEROUS: Negative timeout
if current_time - session_created > timeout:
    # If timeout is negative, this is always False
    # Session never expires
```

#### Token/OTP Handling

##### OTP Lifetime Issues

```python
# DANGEROUS: lifetime=0 accepts all
def verify_otp(code, user, lifetime=300):
    if lifetime == 0:
        return True  # Skip expiry check entirely

# DANGEROUS: Negative lifetime
    if otp.created_at + lifetime > current_time:
        return True
    # If lifetime is negative, always expired? Or underflow?

# DANGEROUS: No rate limiting
def verify_otp(code, user):
    return code == user.current_otp
    # Attacker can try all 1,000,000 6-digit codes
```

##### Token Reuse

```python
# DANGEROUS: OTP valid until next OTP generated
def verify_otp(code, user):
    return code == user.otp

# DANGEROUS: Reset token valid forever
def verify_reset_token(token):
    return token in valid_tokens
    # Never expires, never invalidated on use

# SECURE: Single-use, time-limited
def verify_reset_token(token):
    record = db.get_token(token)
    if not record:
        return False
    if record.used or record.expired:
        return False
    record.mark_used()  # Invalidate immediately
    return True
```

#### Authorization Footguns

##### Role/Permission Accumulation

```python
# DANGEROUS: String-based permissions
user.permissions = "read,write"
user.permissions += ",admin"  # Too easy

# DANGEROUS: Any-match logic
def has_permission(user, required):
    return any(p in user.permissions for p in required.split(","))
# has_permission(user, "admin,readonly") - matches if ANY is present

# DANGEROUS: Substring matching
if "admin" in user.role:
    grant_admin_access()
# "readonly_admin_viewer" contains "admin"
```

##### Missing Authorization Checks

```python
# DANGEROUS: Auth check in one place, not others
@require_login
def list_documents(request):
    return Document.objects.all()

def get_document(request, doc_id):
    # Developer forgot @require_login
    return Document.objects.get(id=doc_id)

def delete_document(request, doc_id):
    # Developer also forgot authorization check
    Document.objects.get(id=doc_id).delete()
```

**Fix**: Centralized authorization; deny-by-default.

##### IDOR Enablers

```python
# DANGEROUS: User ID from request
def get_profile(request):
    user_id = request.GET["user_id"]  # Attacker changes this
    return User.objects.get(id=user_id)

# DANGEROUS: Sequential IDs
user = User.objects.create(...)  # Gets ID 12345
# Attacker tries 12344, 12346, etc.
```

#### Multi-Factor Authentication

##### Bypassable MFA

```python
# DANGEROUS: MFA check in frontend only
# API directly accessible without MFA

# DANGEROUS: "Remember this device" with weak token
device_token = hashlib.md5(user_agent.encode()).hexdigest()
# Attacker spoofs User-Agent to bypass MFA

# DANGEROUS: MFA disabled by user preference
if user.preferences.get("mfa_enabled", True):
    require_mfa()
# Preference stored in same session = attacker disables it
```

##### Recovery Code Issues

```python
# DANGEROUS: Predictable recovery codes
recovery_code = str(user.id).zfill(8)  # Just the user ID

# DANGEROUS: Unlimited recovery attempts
for _ in range(1000000):
    try_recovery_code(guess)

# DANGEROUS: Recovery codes don't invalidate
if code in user.recovery_codes:
    login(user)
    # Code still valid for reuse
```

#### Auth API Design Checklist

For authentication APIs, verify:

- [ ] **Constant-time comparison**: Password/token checks use constant-time compare
- [ ] **Empty value rejection**: Empty passwords/tokens explicitly rejected
- [ ] **Uniform errors**: No user enumeration via different error messages
- [ ] **Session regeneration**: New session ID on auth state changes
- [ ] **Cryptographic tokens**: secrets module, not random or time-based
- [ ] **Positive timeouts**: Zero/negative values rejected or have safe meaning
- [ ] **Single-use tokens**: OTPs/reset tokens invalidated on use
- [ ] **Rate limiting**: Brute force protection on all auth endpoints
- [ ] **Authorization centralized**: Not scattered across endpoints
- [ ] **MFA in backend**: Not bypassable by skipping frontend

### Real-World Case Studies

Analysis of sharp edges in widely-used libraries. These aren't implementation bugs—they're design decisions that make secure usage difficult.

#### GNU Multiple Precision Arithmetic Library (GMP)

GMP is used extensively for cryptographic implementations (RSA, Paillier, ElGamal, etc.) despite being fundamentally unsuitable for cryptography.

##### Sharp Edge: Variable-Time Operations

**The Problem**: GMP operations are not constant-time. Timing varies based on input values.

```c
// DANGEROUS: Timing leaks secret exponent bits
mpz_powm(result, base, secret_exponent, modulus);

// Each bit of secret_exponent affects timing differently
// Attacker can recover secret_exponent via timing analysis
```

**Why This Matters**:
- Paillier encryption uses `mpz_powm` with secret keys
- RSA implementations using GMP leak private key bits
- Even "blinded" implementations often have residual timing leaks

**Detection Pattern**: Any use of GMP (`mpz_*` functions) with secret values:
- `mpz_powm`, `mpz_powm_sec` (the "sec" version is still not fully constant-time)
- `mpz_mul`, `mpz_mod` with secret operands
- `mpz_cmp` for secret comparison

**Real Vulnerabilities**:
- CVE-2018-16152: Timing attack on strongSwan IKEv2
- Numerous academic papers demonstrating key recovery from GMP-based crypto

##### Sharp Edge: Memory Not Securely Cleared

```c
mpz_t secret_key;
mpz_init(secret_key);
// ... use secret_key ...
mpz_clear(secret_key);  // Memory NOT securely wiped
// Secret data may persist in freed memory
```

**The Problem**: `mpz_clear` doesn't zero memory before freeing. Secrets persist.

##### Sharp Edge: Confusing Import/Export API

```c
// What does this do?
mpz_export(buf, &count, order, size, endian, nails, op);

// Parameters:
// - order: 1 = most significant word first, -1 = least significant
// - endian: 1 = big, -1 = little, 0 = native
// - nails: bits to skip at top of each word (?!)
```

**The Problem**: Seven parameters, three of which control byte ordering in different ways. Easy to get wrong, hard to verify correctness.

##### Mitigation

For cryptographic use, prefer:
- **libsodium** for common operations
- **OpenSSL BIGNUM** (has constant-time variants)
- **libgmp with mpz_powm_sec** (partial mitigation, not complete)

---

#### OpenSSL

The canonical example of a powerful but footgun-laden cryptographic library.

##### Sharp Edge: SSL_CTX_set_verify Callback

```c
// DANGEROUS: Easy to write callback that always returns 1
SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, verify_callback);

int verify_callback(int preverify_ok, X509_STORE_CTX *ctx) {
    // Developer thinks: "I'll add logging here"
    log_certificate(ctx);
    return 1;  // OOPS: Always accepts, ignoring preverify_ok!
}
```

**The Problem**: The callback's return value determines whether verification succeeds. Developers often:
- Return 1 (success) unconditionally while "just adding logging"
- Forget that returning non-zero bypasses all verification
- Copy-paste examples that return 1 for "debugging"

**Correct Pattern**:
```c
int verify_callback(int preverify_ok, X509_STORE_CTX *ctx) {
    if (!preverify_ok) {
        // Log failure details
        log_verification_failure(ctx);
    }
    return preverify_ok;  // Preserve original decision
}
```

##### Sharp Edge: Error Handling via ERR_get_error

```c
// DANGEROUS: Error easily ignored
EVP_EncryptFinal_ex(ctx, outbuf, &outlen);
// Did it succeed? Who knows!

// Correct but verbose:
if (EVP_EncryptFinal_ex(ctx, outbuf, &outlen) != 1) {
    unsigned long err = ERR_get_error();
    char buf[256];
    ERR_error_string_n(err, buf, sizeof(buf));
    // Handle error...
}
```

**The Problem**:
- Functions return 1 for success (not 0!)
- Errors accumulate in a thread-local queue
- Easy to forget to check, easy to check wrong way
- Error queue must be cleared or errors persist

##### Sharp Edge: RAND_bytes vs RAND_pseudo_bytes

```c
// These look almost identical:
RAND_bytes(buf, len);        // Cryptographically secure
RAND_pseudo_bytes(buf, len); // NOT guaranteed secure!

// Worse: RAND_pseudo_bytes returns 1 even when insecure
int rc = RAND_pseudo_bytes(buf, len);
// rc == 1 means "success", not "cryptographically random"
// rc == 0 means "success but not crypto-strength" (!!)
// rc == -1 means "not supported"
```

**The Problem**: Function names differ by one word; return values are confusing; the insecure function is not clearly marked dangerous.

##### Sharp Edge: Memory Ownership Confusion

```c
// Who frees this?
X509 *cert = SSL_get_peer_certificate(ssl);
// Answer: YOU do (it's a copy)

// Who frees this?
X509 *cert = SSL_get0_peer_certificate(ssl);  // OpenSSL 3.0+
// Answer: NOBODY (it's a reference)

// The difference: "get" vs "get0"
// This convention is NOT obvious or consistently applied
```

**The Problem**: Memory ownership indicated by subtle naming conventions that aren't documented together and aren't consistent across the API.

##### Sharp Edge: EVP_CIPHER_CTX Reuse

```c
EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, key, iv);
EVP_EncryptUpdate(ctx, out, &outlen, in, inlen);
EVP_EncryptFinal_ex(ctx, out + outlen, &tmplen);

// DANGEROUS: Reusing ctx without reset
EVP_EncryptInit_ex(ctx, NULL, NULL, NULL, iv2);  // New IV only
// Some state from previous encryption may persist!
```

**The Problem**: Context reuse rules are complex and vary by cipher mode.

---

#### Python's `pickle`

##### Sharp Edge: Arbitrary Code Execution by Design

```python
import pickle

# DANGEROUS: Deserializes arbitrary Python objects
data = pickle.loads(untrusted_input)

# Attacker sends:
# b"cos\nsystem\n(S'rm -rf /'\ntR."
# Result: Executes shell command
```

**The Problem**: `pickle` is not a data format—it's a code execution format. There is no safe way to unpickle untrusted data, but:
- The function looks like a data parser
- The name suggests food preservation, not danger
- Many developers don't realize the risk

**Mitigation**: Use `json` for data. If you need pickle, use `hmac` to authenticate before unpickling (but even then, prefer safer formats).

---

#### YAML Libraries

##### Sharp Edge: Code Execution via Tags

```python
import yaml

# DANGEROUS: yaml.load() executes arbitrary code
data = yaml.load(untrusted_input)

# Attacker sends:
# !!python/object/apply:os.system ['rm -rf /']
```

**The Problem**: YAML's tag system allows arbitrary object instantiation. The "safe" loader is:
```python
data = yaml.safe_load(untrusted_input)  # Safe
data = yaml.load(untrusted_input, Loader=yaml.SafeLoader)  # Also safe
```

But the dangerous version is the obvious one (`yaml.load()`).

---

#### PHP's `strcmp` for Password Comparison

##### Sharp Edge: Type Juggling Bypass

```php
// DANGEROUS: Type juggling attack
if (strcmp($_POST['password'], $stored_password) == 0) {
    authenticate();
}

// Attacker sends: password[]=anything
// strcmp(array, string) returns NULL
// NULL == 0 is TRUE in PHP!
```

**The Problem**:
- `strcmp` returns `NULL` on type error, not `-1` or `1`
- PHP's `==` operator coerces `NULL` to `0`
- `NULL == 0` evaluates to `TRUE`
- Authentication bypassed

**Fix**:
```php
if (hash_equals($stored_hash, hash('sha256', $_POST['password']))) {
    // Use hash_equals for timing-safe comparison
    // AND proper password hashing (not shown)
}
```

---

#### Analysis Template

When examining a library for sharp edges:

##### Input → Expected Output

| Input | Expected | Actual | Vulnerability |
|-------|----------|--------|---------------|
| `verify_ssl=false` | Clear warning | Silent acceptance | Config cliff |
| `password=""` | Rejection | Login success | Empty bypass |
| `algorithm="none"` | Error | Signature skipped | Downgrade |
| `timeout=-1` | Error | Infinite timeout | Magic value |

##### Library Comparison

| Feature | Dangerous Library | Safer Alternative |
|---------|------------------|-------------------|
| Bignum crypto | GMP | libsodium, OpenSSL BIGNUM |
| TLS | Raw OpenSSL | Higher-level wrappers |
| Serialization | pickle, YAML | JSON, protobuf |
| Password compare | strcmp | hash_equals, secrets.compare_digest |

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
