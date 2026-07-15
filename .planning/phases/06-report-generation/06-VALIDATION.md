---
phase: 06
slug: report-generation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-15
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1+ with pytest-qt 4.5+ |
| **Config file** | pyproject.toml [tool.pyappdist] |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | RG-01 | — | N/A | integration | `pytest tests/test_report_generator.py -x` | ❌ Wave 0 | ⬜ pending |
| 06-02-01 | 02 | 1 | RG-03 | — | N/A | unit | `pytest tests/test_plan_snippet.py -x` | ❌ Wave 0 | ⬜ pending |
| 06-03-01 | 03 | 1 | RG-01, RG-02, RG-05, RG-06, RG-07 | — | N/A | unit | `pytest tests/test_report_generator.py -x` | ❌ Wave 0 | ⬜ pending |
| 06-04-01 | 04 | 2 | RG-01 | — | N/A | integration | `pytest tests/test_report_generator.py -x` | ❌ Wave 0 | ⬜ pending |
| 06-05-01 | 05 | 2 | RG-08 | — | N/A | unit | `pytest tests/test_layout_dialog.py -x` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_report_generator.py` — covers RG-01, RG-02, RG-05, RG-06, RG-07
- [ ] `tests/test_plan_snippet.py` — covers RG-03
- [ ] `tests/test_camera_overlay.py` — covers RG-04
- [ ] `tests/test_layout_dialog.py` — covers RG-08
- [ ] `pip install reportlab` — required before any tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual quality of plan snippet | RG-03 | Requires human judgment | Generate report, inspect plan snippet quality |
| Camera symbol rendering at plan scale | RG-04 | Requires visual verification | Generate report, verify symbol proportions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
