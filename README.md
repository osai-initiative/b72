# Deterministic Neuralese Translator

Downloaded from `AGofficial/NeuraleseTranslator` on Hugging Face.

## Neuralese vocabulary translator

`reverse_model.py` probes each Kalrean source token through the upstream checkpoint once, ranks English vocabulary outputs, and writes `vocabulary.json`. Runtime translation uses only that JSON dictionary—no PyTorch and no neural inference.

## Neuralese Bytecode (B72-o200k)

The primary machine-first language is implemented in `neuralese_bytecode.py`.

Example:

```text
B72{A:J;E{X:M;V:leave;T:+1d;C:O:upset}}
```

Grammar:

```text
B<version>{<entry>;<entry>;...}
<entry> := <one-char-opcode>{<nested entries>} | <one-char-opcode>:<value>
```

Properties:

- typed nested scopes;
- one-character opcodes;
- explicit sequence boundaries;
- deterministic serialization;
- fail-closed parsing;
- escaped delimiter support;
- ASCII-compatible values except where the protocol deliberately uses compact opcodes;
- optimized and measured with `o200k_base`.

The bytecode is intentionally difficult for humans to scan. Payload values remain ordinary text because reasoning quality matters more than compressing semantic content into arbitrary symbols.

```python
from neuralese_bytecode import decode, encode

x = decode("B72{A:J;E{X:M;V:leave;T:+1d;C:O:upset}}")
assert encode(x) == "B72{A:J;E{X:M;V:leave;T:+1d;C:O:upset}}"
```

The canonical form costs **27 `o200k_base` tokens** for supplied example. Token cost must be measured against real prompts; no wire format is universally optimal across tokenizers. For token efficiency, `encode_compact()` emits same AST as whitespace-delimited scopes with shared semantic codebook:

```text
B72 ( A q E ( X aa V zx T zz C yy ) )
```

Codebook maps `q=J`, `aa=M`, `zx=leave`, `zz=+1d`, and `yy=O:upset`. Once loaded in model context, example costs **17 `o200k_base` tokens**, versus **18** for concise English equivalent. Codebook cost must be amortized across messages; sending it each time loses advantage.


## O200K structured fallback

`o200k_machine.py` provides a simpler field format:

```text
∆=goal text|§=context text|¤=hard constraints|※=JSON
```

Use B72-o200k when nested typed structure matters. Use the fallback when fixed named fields are enough.

## Tests

```bash
/home/axel/.hermes/hermes-agent/venv/bin/python -m unittest discover -s tests -v
```

## Install as a skill

Standard skills-compatible agents can install the skill from this repository:

```bash
npx skills add <repository-url> --skill b72-o200k -a codex --yes
```

For local Codex and Hermes installation from a clone:

```bash
./install.sh --only both
```

Restart the agent after installation. Codex loads skills at startup; use `$b72-o200k` for explicit invocation.
