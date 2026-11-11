"""Bug classes and the one-line definitions shown to models in the detect prompt.

Keep docs/TAXONOMY.md in sync (tests/test_chain.py checks it). Keys shared with
sui-sec-bench mean the same thing, so results compare across chains. Tie-breaks
are written into the definitions, following sec_bench_core.classes.LABEL_PRINCIPLE.
"""

DEFINITIONS = {
    "access-control": (
        "the check of who may call is missing, wrong, or applied only in some conditions: a required "
        "signature, or the signer being the stored authority or admin."
    ),
    "account-validation": (
        "an account is accepted without the checks that prove it is the right one: owner program, "
        "type (discriminator), PDA seeds, or expected address. Use this even if the result is that "
        "someone acts as an authority."
    ),
    "arithmetic": (
        "a calculation is wrong: overflow or underflow, precision loss, rounding in the wrong "
        "direction, wrong units or decimals."
    ),
    "input-validation": (
        "an instruction argument's value is not checked: range, length, duplicates, thresholds, "
        "empty input. Use this even if the result is that someone gains control."
    ),
    "cpi": (
        "a cross-program invocation calls a program id the caller supplied without checking it, or "
        "signs with the wrong seeds."
    ),
    "account-lifecycle": (
        "an account can be initialized twice, closed unsafely (revived, lamports or data left "
        "behind), or used after it was closed."
    ),
    "business-logic": (
        "every needed check is present, but the protocol's rule itself is wrong: accounting, "
        "rewards, fees, liquidation, order of steps."
    ),
    "oracle-price": "price data is stale, can be manipulated, or is read without its status checks.",
    "upgrade-versioning": "upgrade authority, program version or data migration is handled wrongly.",
    "none": "no real vulnerability (answer with found: false).",
}

CLASSES = list(DEFINITIONS)

FRAMEWORKS = ["anchor", "pinocchio", "native"]
