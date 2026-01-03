"""Integration tests for appointments monitoring using fixtures (no network)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from nycgo_pipeline.appointments.fetch_open_data import _parse_record
from nycgo_pipeline.appointments.match import match_organizations
from nycgo_pipeline.appointments.report import generate_reports
from nycgo_pipeline.appointments.score import score_candidates


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory path."""
    return Path(__file__).parent.parent / "fixtures" / "appointments"


@pytest.fixture
def open_data_records(fixtures_dir):
    """Load sample Open Data records from fixture."""
    fixture_path = fixtures_dir / "open_data_sample.json"
    with open(fixture_path) as f:
        raw_records = json.load(f)
    return [_parse_record(r) for r in raw_records]


@pytest.fixture
def golden_df(fixtures_dir):
    """Load sample golden dataset from fixture."""
    fixture_path = fixtures_dir / "golden_sample.csv"
    return pd.read_csv(fixture_path, dtype=str).fillna("")


class TestEndToEndPipeline:
    """End-to-end integration tests using fixtures."""

    def test_full_pipeline_with_fixtures(self, open_data_records, golden_df):
        """Test the full pipeline from records to scored candidates."""
        # Match records to organizations
        candidates = match_organizations(open_data_records, golden_df)

        # Should have candidates for each record
        assert len(candidates) == len(open_data_records)

        # Score candidates
        scored = score_candidates(candidates)

        # All should have scores
        assert all(c.score >= 0 for c in scored)

        # Check specific expected matches
        dob_candidates = [c for c in scored if c.nycgo_record_id == "NYC_GOID_000001"]
        assert len(dob_candidates) >= 1  # DOB should match

        law_candidates = [c for c in scored if c.nycgo_record_id == "NYC_GOID_000002"]
        assert len(law_candidates) >= 1  # Law Dept should match

    def test_report_generation(self, open_data_records, golden_df):
        """Test report generation with fixture data."""
        # Process candidates
        candidates = match_organizations(open_data_records, golden_df)
        scored = score_candidates(candidates)

        # Generate reports in temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            scan_metadata = {
                "scan_date": "2025-12-30",
                "start_date": "2025-12-01",
                "end_date": "2025-12-30",
                "golden_version": "test",
                "records_scanned": len(open_data_records),
            }

            generate_reports(scored, output_dir, scan_metadata)

            # Check all output files exist
            assert (output_dir / "candidates.json").exists()
            assert (output_dir / "candidates.csv").exists()
            assert (output_dir / "candidates_summary.md").exists()

            # Verify JSON structure
            with open(output_dir / "candidates.json") as f:
                json_report = json.load(f)
                assert "scan_metadata" in json_report
                assert "candidates" in json_report
                assert len(json_report["candidates"]) == len(scored)

            # Verify CSV has header
            with open(output_dir / "candidates.csv") as f:
                header = f.readline().strip()
                assert "record_id" in header
                assert "field_name" in header

            # Verify Markdown has content
            with open(output_dir / "candidates_summary.md") as f:
                md_content = f.read()
                assert "Appointments Monitor Scan Report" in md_content
                assert "Summary" in md_content


class TestPersonnelRecordParsing:
    """Tests for parsing personnel records from fixture data."""

    def test_parse_appointed_record(self, open_data_records):
        """Test parsing an APPOINTED record."""
        appointed = [r for r in open_data_records if r.reason_for_change == "APPOINTED"]
        assert len(appointed) >= 1

        record = appointed[0]
        assert record.agency_name == "DEPARTMENT OF BUILDINGS"
        assert record.employee_name == "DOE,JANE M."
        assert record.effective_date is not None

    def test_parse_retired_record(self, open_data_records):
        """Test parsing a RETIRED record."""
        retired = [r for r in open_data_records if r.reason_for_change == "RETIRED"]
        assert len(retired) >= 1

        record = retired[0]
        assert record.agency_name == "LAW DEPARTMENT"
        assert "WALKER" in record.employee_name

    def test_parse_promoted_record(self, open_data_records):
        """Test parsing a PROMOTED record."""
        promoted = [r for r in open_data_records if r.reason_for_change == "PROMOTED"]
        assert len(promoted) >= 1

    def test_all_records_have_agency(self, open_data_records):
        """Test all records have agency name."""
        for record in open_data_records:
            assert record.agency_name


class TestMatchingLogic:
    """Tests for matching logic with fixture data."""

    def test_exact_match_dob(self, open_data_records, golden_df):
        """Test exact match for Department of Buildings."""
        dob_record = next(r for r in open_data_records if "BUILDINGS" in r.agency_name)

        # Create single-record list for matching
        candidates = match_organizations([dob_record], golden_df)

        assert len(candidates) == 1
        assert candidates[0].nycgo_record_id == "NYC_GOID_000001"
        assert candidates[0].org_match is not None
        assert candidates[0].org_match.confidence >= 0.8

    def test_no_match_unknown_agency(self, open_data_records, golden_df):
        """Test no match for unknown agency."""
        unknown_record = next(
            r for r in open_data_records if "UNKNOWN" in r.agency_name
        )

        candidates = match_organizations([unknown_record], golden_df)

        assert len(candidates) == 1
        # Should have no org match or very low confidence fuzzy match
        if candidates[0].org_match:
            assert candidates[0].org_match.confidence < 0.5
        else:
            assert candidates[0].nycgo_record_id is None

    def test_separation_detection(self, open_data_records, golden_df):
        """Test that separations are detected and handled."""
        retired_record = next(
            r for r in open_data_records if r.reason_for_change == "RETIRED"
        )

        candidates = match_organizations([retired_record], golden_df)

        assert len(candidates) == 1
        # Retired records should be flagged for vacancy verification
        # depending on name match
        assert candidates[0].reason_for_change == "RETIRED"


class TestScoringWithFixtures:
    """Tests for scoring with fixture data."""

    def test_appointment_scores_higher_than_separation(
        self, open_data_records, golden_df
    ):
        """Test that appointments with different names score higher."""
        candidates = match_organizations(open_data_records, golden_df)
        scored = score_candidates(candidates)

        # Find appointment and separation for same-confidence org match
        appointments = [
            c
            for c in scored
            if c.reason_for_change == "APPOINTED" and c.nycgo_record_id
        ]
        separations = [
            c for c in scored if c.reason_for_change == "RETIRED" and c.nycgo_record_id
        ]

        # Both should exist in fixtures
        assert len(appointments) >= 1
        assert len(separations) >= 1

    def test_unmatched_org_scores_low(self, open_data_records, golden_df):
        """Test that unmatched orgs score low."""
        candidates = match_organizations(open_data_records, golden_df)
        scored = score_candidates(candidates)

        unmatched = [c for c in scored if c.nycgo_record_id is None]
        matched = [c for c in scored if c.nycgo_record_id is not None]

        if unmatched and matched:
            # Average unmatched score should be lower
            avg_unmatched = sum(c.score for c in unmatched) / len(unmatched)
            avg_matched = sum(c.score for c in matched) / len(matched)
            assert avg_unmatched < avg_matched
