# Future Improvements & Technical Debt

This document tracks planned improvements and technical debt items that are not immediately critical but should be addressed in the future.

## Package Management Migration

### UV Migration
**Status**: Planned  
**Priority**: Low  
**Timeline**: TBD

**Description**:  
Migrate from `venv` + `pip` to [UV](https://github.com/astral-sh/uv) for package management. UV is a modern, fast Python package manager written in Rust that can replace both `venv` and `pip`.

**Rationale**:
- Faster dependency installation and resolution
- Better lockfile support
- Modern tooling (from Astral, makers of ruff)
- Potential standardization across MODA projects

**Current State**:
- Project uses `venv` + `pip` via Makefile
- `pyproject.toml` already configured (compatible with UV)
- Python 3.10+ requirement (UV compatible)

**Migration Tasks** (when ready):
- [ ] Install UV
- [ ] Update Makefile to use UV instead of venv/pip
- [ ] Create `uv.lock` file
- [ ] Update documentation (README, setup instructions)
- [ ] Update CI/CD if applicable
- [ ] Test that all functionality still works
- [ ] Remove `.venv` from gitignore (UV uses different structure)

**Notes**:
- Good timing: Between major phases (e.g., after Phase II.1, before Phase II.2)
- Low risk: Current setup works fine, migration is optional
- Can be done incrementally without blocking other work

