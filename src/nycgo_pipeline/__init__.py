"""Core processing package for NYC Governance Organizations."""

import sys
from importlib import import_module
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(_ROOT.parent))


directory_changelog = import_module("nycgo_pipeline.directory_changelog")
export = import_module("nycgo_pipeline.export")
global_rules = import_module("nycgo_pipeline.global_rules")
pipeline = import_module("nycgo_pipeline.pipeline")
publish = import_module("nycgo_pipeline.publish")
qa_edits = import_module("nycgo_pipeline.qa_edits")
review = import_module("nycgo_pipeline.review")
run_ids = import_module("nycgo_pipeline.run_ids")
schema = import_module("nycgo_pipeline.schema")

__all__ = [
    "directory_changelog",
    "export",
    "global_rules",
    "pipeline",
    "publish",
    "qa_edits",
    "review",
    "crosswalk",
    "schema",
    "run_ids",
]
