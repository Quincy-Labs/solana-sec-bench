# Bug classes

One key per case in `meta.yaml` (`bug_class`). The definitions are the ones
models see in the detect prompt; their source is `solana_bench/taxonomy.py`
(`tests/test_chain.py` checks this file matches). Keys shared with
sui-sec-bench mean the same thing, so results can be compared across chains.

Labeling principle (shared by every chain, from `sec_bench_core.classes`):
label the cause, not the consequence. Tie-breaks are written into the
definitions ("use this even if ...").

| Key | Definition | Shared with Sui |
|---|---|---|
| `access-control` | The check of who may call is missing, wrong, or applied only in some conditions: a required signature, or the signer being the stored authority or admin. | yes |
| `account-validation` | An account is accepted without the checks that prove it is the right one: owner program, type (discriminator), PDA seeds, or expected address. Use this even if the result is that someone acts as an authority. | Solana form of Sui's `object-validation` |
| `arithmetic` | A calculation is wrong: overflow or underflow, precision loss, rounding in the wrong direction, wrong units or decimals. | yes |
| `input-validation` | An instruction argument's value is not checked: range, length, duplicates, thresholds, empty input. Use this even if the result is that someone gains control. | yes |
| `cpi` | A cross-program invocation calls a program id the caller supplied without checking it, or signs with the wrong seeds. | no |
| `account-lifecycle` | An account can be initialized twice, closed unsafely (revived, lamports or data left behind), or used after it was closed. | no |
| `business-logic` | Every needed check is present, but the protocol's rule itself is wrong: accounting, rewards, fees, liquidation, order of steps. | yes |
| `oracle-price` | Price data is stale, can be manipulated, or is read without its status checks. | yes |
| `upgrade-versioning` | Upgrade authority, program version or data migration is handled wrongly. | yes |
| `none` | No real vulnerability (answer with found: false). | yes |

`bug_class_also` in `meta.yaml` lists other classes accepted for a case, only
where a reviewer agrees the second label is defensible (SOL-0002 accepts
`access-control`). `framework` is one of `anchor`, `pinocchio`, `native`.
