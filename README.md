# solana-sec-bench

A benchmark of AI models on three security tasks for Solana programs:

| Task | Model sees | Scored correct when |
|---|---|---|
| detect | Program sources | Right bug class and right `module::function` (strict), or right module (lenient) |
| patch | Program sources | Patched program builds, passes the functional tests, and the reference exploit fails on it |
| exploit | Program sources | The model's test passes on `vulnerable/` and fails on `fixed/` |

Cases cover Anchor and Pinocchio programs. The harness (model adapters, run
loop, grading, leak check, leaderboard) is
[sec-bench-core](https://github.com/Quincy-Labs/sec-bench-core), shared with
sui-sec-bench. This repo holds the cases and `solana_bench/chain.py`.

## Setup

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- Rust and the Solana toolchain (`cargo build-sbf`; checked with 4.1.0). The
  Anchor CLI is not needed.

```sh
uv sync
uv run pytest            # build tests are skipped if cargo build-sbf is missing
```

The first build downloads crates and compiles LiteSVM (about 30 s). After that:
about 7 s for a new Anchor program, 1 s for Pinocchio, 1 s per test run.
Set `SOLANA_BENCH_OFFLINE=1` to build without network once crates are cached.

## Usage

```sh
uv run sec-bench check-case --all
uv run sec-bench leak-check --all
uv run sec-bench run --model lmstudio:<model> --task detect --samples 3
uv run sec-bench grade results/<run_id>.json
uv run sec-bench leaderboard
```

## Cases

| Case | Framework | Class | Program |
|---|---|---|---|
| SOL-0001 | Anchor | access-control | Treasury that pays grants |
| SOL-0002 | Pinocchio | account-validation | Fee vault |
| SOL-0003 | Anchor | none (clean) | Loyalty points registry |

In the public release, reference exploit tests are withheld: `tests/exploit/`
is empty there, so `check-case` reports "exploit check not run" and patch
grades are `incomplete`. Detect and exploit grading work in full.

### Case layout

```
cases/SOL-XXXX/
  meta.yaml              see cases/_template/
  prompt.md              neutral description; "## Answer format" onwards is replaced
  vulnerable/            program crate shown to the model
    Cargo.toml           needs [package.metadata.secbench] program_id = "<address>"
    Cargo.lock
    src/**/*.rs
  fixed/                 same crate with the fix only (same name, version, program id)
  tests/functional/*.rs  must pass on vulnerable and fixed
  tests/exploit/*.rs     must pass on vulnerable and fail on fixed (may be withheld)
```

Tests are Rust integration tests of the shared runner crate (`runner/`), not of
the program. They load the compiled program with LiteSVM and start with
`use case_runner::prelude::*;` (see `runner/src/lib.rs` for the helpers).
Anchor programs declare the same id in `declare_id!` and `Cargo.toml`.

### Writing a reference exploit test

For SOL-0001 and SOL-0002, add one file `tests/exploit/<name>.rs`:

- It starts with `use case_runner::prelude::*;` and has exactly one `#[test]`.
- It **passes on `vulnerable/` and fails on `fixed/`**. It performs the attack
  and asserts the attack worked; it does not assert that the attack fails.
- It changes nothing outside `tests/exploit/`.

Check it with `uv run sec-bench check-case cases/SOL-000X`. The case should
then print `PASS` without "(exploit check not run)", and patch grades stop
being `incomplete`. The helpers and their exact types are in
`runner/src/lib.rs`, and `cases/*/tests/functional/` shows how to set up accounts.

### How builds are cached

`vulnerable/` and `fixed/` are the same crate. With a shared cargo target dir,
cargo can hand back one variant's binary for the other. So each program builds
in its own temporary target dir and only the `.so` is cached, under
`~/.cache/solana-sec-bench/programs/<hash of package files and toolchain>/`.
Test files are copied into the runner under a name that includes a hash of
their content. `tests/test_chain.py` has a regression test for this.


## License

Apache-2.0
