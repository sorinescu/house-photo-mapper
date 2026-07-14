---
phase: 04
slug: annotation-tools
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-14
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/ -x` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-03-01 | 03 | 1 | ED-04 | — | N/A | unit | `pytest tests/unit/test_undo_commands.py -x` | ⬜ W0 | ⬜ pending |
| 04-03-02 | 03 | 1 | ED-01 | — | N/A | unit | `pytest tests/unit/test_move_marker.py -x` | ⬜ W0 | ⬜ pending |
| 04-03-03 | 03 | 1 | ED-02 | — | N/A | unit | `pytest tests/unit/test_rotate_arrow.py -x` | ⬜ W0 | ⬜ pending |
| 04-03-04 | 03 | 1 | ED-03 | — | N/A | unit | `pytest tests/unit/test_delete_annotation.py -x` | ⬜ W0 | ⬜ pending |
| 04-04-01 | 04 | 1 | NA-01 | — | N/A | unit | `pytest tests/unit/test_shortcuts.py -x` | ⬜ W0 | ⬜ pending |
| 04-04-02 | 04 | 1 | NA-02 | — | N/A | unit | `pytest tests/unit/test_shortcuts.py -x` | ⬜ W0 | ⬜ pending |
| 04-04-03 | 04 | 1 | NA-04 | — | N/A | unit | `pytest tests/unit/test_shortcuts.py -x` | ⬜ W0 | ⬜ pending |
| 04-04-04 | 04 | 1 | NA-05 | — | N/A | unit | `pytest tests/unit/test_shortcuts.py -x` | ⬜ W0 | ⬜ pending |
| 04-04-05 | 04 | 1 | NA-06 | — | N/A | unit | `pytest tests/unit/test_shortcuts.py -x` | ⬜ W0 | ⬜ pending |
| 04-05-01 | 05 | 1 | NA-01 | — | N/A | integration | `pytest tests/integration/test_photo_annotation_binding.py -x` | ⬜ W0 | ⬜ pending |
| 04-05-02 | 05 | 1 | NA-02 | — | N/A | integration | `pytest tests/integration/test_photo_annotation_binding.py -x` | ⬜ W0 | ⬜ pending |
| 04-05-03 | 05 | 1 | US-01 | — | N/A | integration | `pytest tests/integration/test_annotation_flow.py -x` | ⬜ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_undo_commands.py` — stubs for ED-04
- [ ] `tests/unit/test_move_marker.py` — stubs for ED-01
- [ ] `tests/unit/test_rotate_arrow.py` — stubs for ED-02
- [ ] `tests/unit/test_delete_annotation.py` — stubs for ED-03
- [ ] `tests/unit/test_shortcuts.py` — stubs for NA-01, NA-02, NA-04, NA-05, NA-06
- [ ] `tests/integration/test_photo_annotation_binding.py` — stubs for NA-01, NA-02
- [ ] `tests/integration/test_annotation_flow.py` — stubs for US-01

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual polygon vertex handles | AN-04 | Requires visual inspection of grip items | Draw polygon, verify small circles at vertices appear and move with polygon |
| Cone angle adjustment via drag | AN-03 | Requires mouse drag interaction | Drag cone edge handle, verify angle changes smoothly |
| Professional keyboard shortcuts | US-02 | Requires human assessment of shortcut ergonomics | Test all shortcuts in various contexts (metadata field focus, plan view, etc.) |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending