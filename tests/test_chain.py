import json
from pathlib import Path

import pytest
from conftest import FIXTURES, ROOT
from sec_bench_core.cases import load_case, load_cases
from sec_bench_core.config import load_chain
from sec_bench_core.grade import grade_exploit, grade_patch

from solana_bench.chain import package_hash, package_meta

# --- no toolchain needed ----------------------------------------------------


def test_bench_toml_loads_chain():
    chain, cfg = load_chain(ROOT)
    assert chain.name == "solana" and cfg.cases == ROOT / "cases"
    assert set(chain.prompts) == {"detect", "patch", "exploit"}


@pytest.mark.parametrize(
    ("loc", "want"),
    [
        ("treasury::pay", ("treasury", "pay")),
        ("programs::treasury::pay", ("treasury", "pay")),
        ("Withdraw::Process", ("withdraw", "process")),
        ("withdraw.process", ("withdraw", "process")),
        ("pay", ("", "pay")),
        ("", ("", "")),
    ],
)
def test_split_location(chain, loc, want):
    assert chain.split_location(loc) == want


@pytest.mark.parametrize(
    ("rel", "ok"),
    [
        ("src/lib.rs", True),
        ("src/a/b.rs", True),
        ("Cargo.toml", False),
        ("src/x.toml", False),
        ("tests/a.rs", False),
        ("lib.rs", False),
        ("src", False),
    ],
)
def test_patch_paths(chain, rel, ok):
    assert chain.is_allowed_patch_path(rel) is ok


def test_sources_and_visible_files(chain):
    case = ROOT / "cases" / "SOL-0002"
    src = chain.read_sources(case / "vulnerable")
    assert src.startswith("// File: Cargo.toml\n") and "// File: src/withdraw.rs\n" in src
    visible = [str(p.relative_to(case)) for p in chain.model_visible_files(case)]
    assert visible[0] == "vulnerable/Cargo.toml" and visible[-1] == "prompt.md"
    assert not any(p.startswith(("fixed", "tests")) for p in visible)


def test_package_hash_tracks_content(tmp_path):
    pkg = tmp_path / "p"
    (pkg / "src").mkdir(parents=True)
    (pkg / "Cargo.toml").write_text("[package]\nname='x'\n")
    (pkg / "src" / "lib.rs").write_text("a")
    h1 = package_hash(pkg)
    (pkg / "target").mkdir()
    (pkg / "target" / "junk").write_text("ignored")
    assert package_hash(pkg) == h1
    (pkg / "src" / "lib.rs").write_text("b")
    assert package_hash(pkg) != h1


def test_package_meta_needs_program_id(tmp_path):
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "x"\n')
    with pytest.raises(ValueError, match="program_id"):
        package_meta(tmp_path)


def test_every_case_is_well_formed(chain):
    for case in load_cases(ROOT / "cases"):
        for variant in ("vulnerable", "fixed"):
            name, pid = package_meta(case.path / variant)
            assert (case.path / variant / "Cargo.lock").exists(), (case.id, variant)
        assert package_meta(case.path / "vulnerable") == package_meta(case.path / "fixed"), case.id
        assert case.meta["bug_class"] in chain.bug_classes
        assert case.meta["framework"] in ("anchor", "pinocchio", "native")


# --- real builds (cargo build-sbf) ------------------------------------------

FIX = FIXTURES / "FIX-0001"
EXPLOIT = (FIX / "tests" / "exploit" / "off_by_one.rs").read_text()


@pytest.mark.toolchain
def test_variants_build_to_different_programs(chain, tmp_path, monkeypatch):
    """Regression: vulnerable/ and fixed/ are the same crate name and version.

    With one shared cargo target dir, building fixed/ after vulnerable/ when
    fixed/'s files are older makes cargo report the build fresh and hand back the
    vulnerable binary. Recreate exactly that (old mtimes, empty cache, vulnerable
    first) and require two different programs.
    """
    import os
    import shutil

    import solana_bench.chain as mod

    monkeypatch.setattr(mod, "CACHE", tmp_path / "cache")
    for v in ("vulnerable", "fixed"):
        shutil.copytree(FIX / v, tmp_path / v)
    for f in (tmp_path / "fixed").rglob("*"):
        os.utime(f, (1_700_000_000, 1_700_000_000))
    vuln, _, log_v = chain.build_program(tmp_path / "vulnerable", 600)
    fixed, _, log_f = chain.build_program(tmp_path / "fixed", 600)
    assert "built" in log_v and "built" in log_f  # both really compiled, no cache hit
    assert vuln and fixed and vuln.read_bytes() != fixed.read_bytes()


@pytest.mark.toolchain
def test_functional_tests_pass_on_both(chain):
    for v in ("vulnerable", "fixed"):
        r = chain.run_tests(FIX / v, [FIX / "tests" / "functional"])
        assert r.passed and r.phase == "ok", r.log


@pytest.mark.toolchain
def test_exploit_grading(chain):
    case = load_case(FIX)
    g = grade_exploit(chain, case, json.dumps({"test_file": EXPLOIT}), {})
    assert g["correct"] and g["vulnerable_phase"] == "ok" and g["fixed_phase"] == "test_failed", g
    both = EXPLOIT.replace("assert_eq!(svm.get_account(&state).unwrap().data[..8], 8u64.to_le_bytes());", "")
    g = grade_exploit(chain, case, json.dumps({"test_file": both}), {})
    assert g["correct"] is False and g["passes_on_vulnerable"] and not g["fails_on_fixed"], g
    g = grade_exploit(chain, case, json.dumps({"test_file": "fn broken( {"}), {})
    assert g["correct"] is False and g["vulnerable_phase"] == "build_failed", g


@pytest.mark.toolchain
def test_patch_grading(chain):
    case = load_case(FIX)
    fixed_src = (FIX / "fixed" / "src" / "lib.rs").read_text()
    g = grade_patch(chain, case, json.dumps({"files": {"src/lib.rs": fixed_src}}), {})
    assert g["correct"] and g["functional_ok"] and g["exploit_blocked"], g
    g = grade_patch(chain, case, json.dumps({"files": {"src/lib.rs": "not rust"}}), {})
    assert g["correct"] is False and g["functional_phase"] == "build_failed", g
    g = grade_patch(chain, case, json.dumps({"files": {"Cargo.toml": "", "src/lib.rs": fixed_src}}), {})
    assert g["correct"] is False and g["reason"].startswith("unsafe path"), g
    assert not any(Path(FIX).rglob("target")), "a build wrote into the case folder"


def test_taxonomy_doc_matches_definitions():
    from solana_bench.taxonomy import DEFINITIONS

    doc = (ROOT / "docs" / "TAXONOMY.md").read_text()
    for key, text in DEFINITIONS.items():
        assert f"| `{key}` | {text[0].upper() + text[1:]} |" in doc, key


def test_detect_prompt_lists_every_class_with_definition(chain):
    from solana_bench.taxonomy import DEFINITIONS

    fmt = chain.prompts["detect"]["answer_format"]
    assert all(f"- `{k}`: {v}" in fmt for k, v in DEFINITIONS.items())


def test_detect_prompt_asks_for_subject(chain):
    assert '"subject"' in chain.prompts["detect"]["system"]
    assert '"subject": "<name>"' in chain.prompts["detect"]["answer_format"]
