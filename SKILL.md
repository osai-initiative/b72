---
name: b72-o200k
description: Use B72 compact bytecode with o200k_base models.
version: 0.1.0
author: Axel, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
---

# B72-o200k Skill

Use **B72-o200k** (Neuralese Bytecode Language) internally when machine readability
and token cost matter more than human readability. B72-o200k is a typed notation
for model reasoning and agent-to-agent interchange. It must never replace
natural language in user-facing final output. The reference implementation is
`neuralese_bytecode.py`.

This specification is agent-neutral. It does not require Hermes, a particular
API provider, a hidden chain-of-thought channel, Python, or tool access.

## Hard Output Boundary

Use B72 for internal reasoning state, intermediate tool plans, structured
model-to-model messages, and machine-facing payloads. When emitting an
intermediate progress or tool-planning message, show the raw B72 wire text on
its own line. Do not prepend a label or marker such as `B72-INTERMEDIATE:`.
Before sending a final answer to a human, decode all B72 content and write the
result in the user's normal language. Never emit raw `B72`, compact opcodes, or
codebook atoms in a final answer unless the user explicitly requests the wire
representation.

If an agent has no private reasoning channel, use its ordinary intermittent
progress channel for the raw B72 line. If the host suppresses intermittent
messages, keep B72 in an internal variable, local scratchpad,
system/developer instruction, or agent-to-agent message. If the host cannot
provide either, use ordinary structured text rather than falsely claiming that
B72 was applied.

## Cross-Agent Interoperability

Every compatible agent must implement the same four operations:

1. **Load** the version and codebook from protocol setup.
2. **Encode** structured state into B72-o200k compact wire text.
3. **Decode** wire text into an ordered tree without guessing.
4. **Render** decoded state as ordinary natural language for final output.

Protocol setup may be supplied through a system prompt, developer prompt,
initialization message, configuration file, or side-channel agreed by the
agents. The transport must preserve ASCII spaces, parentheses, and codeword
text exactly. Do not rely on provider-specific prompt syntax.

Agents that cannot guarantee shared codebook state must use canonical B72 with
literal values or ordinary structured text. Agents using another tokenizer must
create a separately measured variant named `B72-<tokenizer>`; do not call it
`B72-o200k` or reuse its atom assignments without benchmarking.

## When to Use

Use B72-o200k when:

- sending repeated structured instructions to an `o200k_base` model;
- representing goals, entities, events, constraints, or outputs;
- nesting related data without verbose JSON keys;
- exchanging messages between model and parser;
- the receiver already has the B72 codebook loaded.

Do not use B72-o200k for final user-facing prose. Also do not use B72-o200k when:

- the receiver has not received the codebook;
- a human must understand the message immediately;
- values contain long prose that dominates token cost;
- exact semantics are uncertain and no explicit code exists.

## Protocol Bootstrap

Load this codebook once per conversation or session. Do not repeat it with every
message. Treat codebook loading as protocol setup, not message content.

```text
B72 protocol:
B<version> <scope>
A action
E event or nested event scope
X entity
M mode
V verb/action value
T time or temporal offset
C cause/context relation
J JSON output marker

compact atoms:
q=J
aa=M
zx=leave
zz=+1d
yy=O:upset
```

The atom table is shared state. Never guess a missing atom. Add a new atom only
with an explicit codebook revision and version bump.

## Wire Grammar

Canonical form:

```text
B72{<entry>;<entry>;...}
```

Entry forms:

```text
<opcode>:<value>
<opcode>{<nested entries>}
```

Compact form:

```text
B72 ( <opcode> <value>|<scope> ... )
```

The compact form uses whitespace as its sequence boundary and parentheses as
scope markers. It replaces known semantic values with shared atoms:

```text
B72 ( A q E ( X aa V zx T zz C yy ) )
```

This decodes to the same AST as:

```text
B72{A:J;E{X:M;V:leave;T:+1d;C:O:upset}}
```

## Encoding Rules

1. Start every message with `B` plus a numeric protocol version.
2. Use one-character opcodes only.
3. Put related facts in a nested scope.
4. Keep entry order deterministic.
5. Use compact atoms only when the receiver has the same codebook.
6. Keep unknown values explicit; never silently drop them.
7. Escape `\\`, `;`, `{`, and `}` in canonical values.
8. Keep compact values whitespace-free. Use canonical form for long or free-form values.
9. Encode constraints separately from context.
10. Encode output requirements explicitly.

Example:

```text
B72 ( A q E ( X aa V zx T zz C yy ) )
```

## Decoding Rules

- Reject missing or malformed `B<version>` headers.
- Reject invalid opcodes and unterminated scopes.
- Reject trailing tokens after the root scope.
- Reject ambiguous or unknown codebook atoms when strict mode is enabled.
- Preserve entry order.
- Preserve value text exactly after unescaping.
- Always translate B72 into normal user-facing prose before final output.
- Preserve exact B72 only when the user explicitly requests the wire format.

A decoder must fail closed. An incorrect decode is worse than an explicit
unknown value.

## Reasoning Behavior

Use B72 to represent **task state**, not hidden chain-of-thought. Encode only
information needed by the receiver:

```text
B72 ( G classify I text R ( must JSON no external ) O q )
```

Keep internal private reasoning out of the wire message unless the user has
explicitly requested that content and policy permits its disclosure. B72 does
not bypass safety, permissions, privacy boundaries, or tool approvals.

## Token Measurement

Measure the actual message with the target tokenizer. For this variant, the
reference tokenizer is `o200k_base`:

```python
import tiktoken

enc = tiktoken.get_encoding("o200k_base")
wire_tokens = len(enc.encode(wire))
```

In another language or agent, use that tokenizer's official API and count the
returned token IDs. Do not infer token savings from character count. Punctuation,
Unicode, spaces, and adjacent codewords can tokenize unexpectedly. Compare
against an equivalent message with identical semantics and identical codebook
assumptions.

The reference example measured as follows in the current implementation:

```text
canonical B72: 27 tokens
compact B72:    17 tokens
concise English:18 tokens
```

The compact result wins by one token only after codebook setup is amortized.
Results vary with payload, tokenizer version, and codebook.

## Reference Implementation (Optional)

The Python implementation is optional. Any language may implement the protocol
using the grammar and rules above:

```python
from neuralese_bytecode import decode, decode_compact, encode, encode_compact

canonical = "B72{A:J;E{X:M;V:leave;T:+1d;C:O:upset}}"
ast = decode(canonical)
compact = encode_compact(ast)
assert decode_compact(compact) == ast
```

## Verification

Before using a new B72 revision:

1. Round-trip canonical form through `decode` and `encode`.
2. Round-trip compact form through `decode_compact` and `encode_compact`.
3. Test nested scopes, empty values, escapes, malformed input, and trailing data.
4. Count tokens with `o200k_base`.
5. Compare against an equivalent human-language message.
6. Confirm receiver has the exact same codebook.

Run the reference tests:

```text
python -m unittest discover -s tests -v
```

If no project virtual environment exists, use the active Python environment
that contains `tiktoken`.

## Pitfalls

- Opaque symbols do not create meaning by themselves; codebook agreement does.
- A codebook sent per message can cost more than natural language.
- Short messages can grow because fixed headers and scope markers have overhead.
- Do not call a model-derived atom human-verified without evidence.
- Do not use B72 to conceal credentials, unsafe actions, or policy-sensitive data.
- Do not change opcode meanings within one session.
- Do not expose compact bytes to users who need an actionable explanation.
