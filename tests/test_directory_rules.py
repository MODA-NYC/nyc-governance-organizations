"""
Regression tests for NYC.gov Agency Directory eligibility rules.

These tests ensure the directory eligibility logic produces consistent
and expected results across all organization types and edge cases.
"""

import pytest

from nycgo_pipeline.directory_rules import (
    ADVISORY_EXEMPTIONS,
    NONPROFIT_EXEMPTIONS,
    evaluate_eligibility,
    has_main_nyc_gov_url,
    is_state_nygov_url,
)

# =============================================================================
# Helper function tests
# =============================================================================


class TestHelperFunctions:
    """Test helper functions used by rules."""

    def test_is_state_nygov_url_detects_state_urls(self):
        """State .ny.gov URLs should be detected."""
        assert is_state_nygov_url("https://www.ny.gov/agency") is True
        assert is_state_nygov_url("https://tax.ny.gov") is True
        assert is_state_nygov_url("http://health.ny.gov/services") is True

    def test_is_state_nygov_url_allows_city_urls(self):
        """City .nyc.gov URLs should not be flagged as state."""
        assert is_state_nygov_url("https://www.nyc.gov") is False
        assert is_state_nygov_url("https://a856-cityrecord.nyc.gov") is False
        assert is_state_nygov_url("http://council.nyc.gov") is False

    def test_is_state_nygov_url_handles_empty(self):
        """Empty/None URLs should return False."""
        assert is_state_nygov_url("") is False
        assert is_state_nygov_url(None) is False

    def test_has_main_nyc_gov_url_detects_index_pages(self):
        """URLs with nyc.gov and index.page should be detected."""
        assert (
            has_main_nyc_gov_url("https://www.nyc.gov/site/agency/index.page") is True
        )
        assert has_main_nyc_gov_url("https://www.nyc.gov/office/index.page") is True

    def test_has_main_nyc_gov_url_rejects_non_index(self):
        """URLs without index.page should not match."""
        assert has_main_nyc_gov_url("https://www.nyc.gov/site/agency") is False
        assert has_main_nyc_gov_url("https://www.nyc.gov") is False

    def test_has_main_nyc_gov_url_handles_empty(self):
        """Empty/None URLs should return False."""
        assert has_main_nyc_gov_url("") is False
        assert has_main_nyc_gov_url(None) is False


# =============================================================================
# Gatekeeper rule tests
# =============================================================================


class TestGatekeeperRules:
    """Test gatekeeper rules that must all pass."""

    def test_inactive_status_fails(self):
        """Inactive organizations should be ineligible."""
        record = {
            "record_id": "100001",
            "name": "Test Agency",
            "operational_status": "Inactive",
            "organization_type": "Mayoral Agency",
            "url": "https://www.nyc.gov/test",
        }
        result = evaluate_eligibility(record)
        assert result.eligible is False
        assert "Active" in result.reasoning or "active" in result.reasoning.lower()

    def test_dissolved_status_fails(self):
        """Dissolved organizations should be ineligible."""
        record = {
            "record_id": "100002",
            "name": "Old Agency",
            "operational_status": "Dissolved",
            "organization_type": "Mayoral Agency",
            "url": "https://www.nyc.gov/old",
        }
        result = evaluate_eligibility(record)
        assert result.eligible is False

    def test_state_nygov_url_fails(self):
        """Organizations with state .ny.gov URLs should be ineligible."""
        record = {
            "record_id": "100003",
            "name": "State Affiliated Org",
            "operational_status": "Active",
            "organization_type": "Mayoral Agency",
            "url": "https://www.ny.gov/state-agency",
        }
        result = evaluate_eligibility(record)
        assert result.eligible is False

    def test_no_contact_info_fails(self):
        """Organizations with no contact info should be ineligible."""
        record = {
            "record_id": "100004",
            "name": "No Contact Agency",
            "operational_status": "Active",
            "organization_type": "Mayoral Agency",
            "url": "",
            "principal_officer_full_name": "",
            "principal_officer_contact_url": "",
        }
        result = evaluate_eligibility(record)
        assert result.eligible is False

    def test_url_satisfies_contact_requirement(self):
        """URL alone satisfies contact info requirement."""
        record = {
            "record_id": "100005",
            "name": "URL Only Agency",
            "operational_status": "Active",
            "organization_type": "Mayoral Agency",
            "url": "https://www.nyc.gov/agency",
            "principal_officer_full_name": "",
            "principal_officer_contact_url": "",
        }
        result = evaluate_eligibility(record)
        assert result.eligible is True

    def test_officer_name_satisfies_contact_requirement(self):
        """Principal officer name alone satisfies contact info requirement."""
        record = {
            "record_id": "100006",
            "name": "Officer Name Agency",
            "operational_status": "Active",
            "organization_type": "Mayoral Agency",
            "url": "",
            "principal_officer_full_name": "John Doe",
            "principal_officer_contact_url": "",
        }
        result = evaluate_eligibility(record)
        assert result.eligible is True

    def test_officer_contact_url_satisfies_contact_requirement(self):
        """Principal officer contact URL alone satisfies contact info requirement."""
        record = {
            "record_id": "100007",
            "name": "Contact URL Agency",
            "operational_status": "Active",
            "organization_type": "Mayoral Agency",
            "url": "",
            "principal_officer_full_name": "",
            "principal_officer_contact_url": "https://www.nyc.gov/contact",
        }
        result = evaluate_eligibility(record)
        assert result.eligible is True


# =============================================================================
# Organization type tests
# =============================================================================


class TestOrganizationTypes:
    """Test type-specific eligibility rules."""

    @pytest.fixture
    def base_record(self):
        """Base record with all gatekeepers passing."""
        return {
            "record_id": "100100",
            "name": "Test Organization",
            "operational_status": "Active",
            "url": "https://www.nyc.gov/test",
            "in_org_chart": "",
        }

    def test_mayoral_agency_always_eligible(self, base_record):
        """Mayoral Agency should always be eligible."""
        base_record["organization_type"] = "Mayoral Agency"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True

    def test_mayoral_office_always_eligible(self, base_record):
        """Mayoral Office should always be eligible."""
        base_record["organization_type"] = "Mayoral Office"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True

    def test_elected_office_always_eligible(self, base_record):
        """Elected Office should always be eligible."""
        base_record["organization_type"] = "Elected Office"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True

    def test_pension_fund_allowlist(self, base_record):
        """Pension Fund eligible only if on allowlist (city employee funds)."""
        base_record["organization_type"] = "Pension Fund"

        # Non-allowlisted pension fund should NOT be eligible
        base_record["name"] = "Cultural Institutions Retirement System"
        result = evaluate_eligibility(base_record)
        assert result.eligible is False

        # Allowlisted pension fund should be eligible
        base_record["name"] = "New York City Employee Retirement System"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True

    def test_state_government_agency_always_eligible(self, base_record):
        """State Government Agency should always be eligible."""
        base_record["organization_type"] = "State Government Agency"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True

    def test_division_requires_org_chart(self, base_record):
        """Division requires in_org_chart=True."""
        base_record["organization_type"] = "Division"
        base_record["in_org_chart"] = ""
        result = evaluate_eligibility(base_record)
        assert result.eligible is False

        base_record["in_org_chart"] = "True"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True

    def test_public_benefit_requires_org_chart(self, base_record):
        """Public Benefit or Development Organization requires in_org_chart=True."""
        base_record["organization_type"] = "Public Benefit or Development Organization"
        base_record["in_org_chart"] = ""
        result = evaluate_eligibility(base_record)
        assert result.eligible is False

        base_record["in_org_chart"] = "True"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True

    def test_nonprofit_requires_org_chart_or_exemption(self, base_record):
        """Nonprofit Organization requires in_org_chart or exemption list."""
        base_record["organization_type"] = "Nonprofit Organization"
        base_record["in_org_chart"] = ""
        result = evaluate_eligibility(base_record)
        assert result.eligible is False

        # With org chart
        base_record["in_org_chart"] = "True"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True

        # With exemption (reset org chart)
        base_record["in_org_chart"] = ""
        base_record["name"] = NONPROFIT_EXEMPTIONS[0]
        result = evaluate_eligibility(base_record)
        assert result.eligible is True

    def test_advisory_multiple_paths_to_eligibility(self, base_record):
        """Advisory or Regulatory Organization has multiple paths to eligibility."""
        base_record["organization_type"] = "Advisory or Regulatory Organization"
        base_record["in_org_chart"] = ""
        base_record["url"] = "https://www.nyc.gov/other"

        # No conditions met - ineligible
        result = evaluate_eligibility(base_record)
        assert result.eligible is False

        # With org chart
        base_record["in_org_chart"] = "True"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True
        base_record["in_org_chart"] = ""

        # With main nyc.gov URL
        base_record["url"] = "https://www.nyc.gov/site/advisory/index.page"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True
        base_record["url"] = "https://www.nyc.gov/other"

        # With exemption
        base_record["name"] = ADVISORY_EXEMPTIONS[0]
        result = evaluate_eligibility(base_record)
        assert result.eligible is True

    def test_unknown_organization_type_ineligible(self, base_record):
        """Unknown organization types should be ineligible."""
        base_record["organization_type"] = "Unknown Type"
        result = evaluate_eligibility(base_record)
        assert result.eligible is False


# =============================================================================
# Exemption list tests
# =============================================================================


class TestExemptionLists:
    """Test exemption list handling."""

    @pytest.fixture
    def base_record(self):
        """Base record with all gatekeepers passing."""
        return {
            "record_id": "100200",
            "operational_status": "Active",
            "url": "https://www.nyc.gov/test",
            "in_org_chart": "",
        }

    @pytest.mark.parametrize("name", NONPROFIT_EXEMPTIONS)
    def test_nonprofit_exemptions_are_eligible(self, base_record, name):
        """All nonprofit exemptions should be eligible without org chart."""
        base_record["name"] = name
        base_record["organization_type"] = "Nonprofit Organization"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True
        assert "Exemption" in result.reasoning or name in result.reasoning

    @pytest.mark.parametrize("name", ADVISORY_EXEMPTIONS)
    def test_advisory_exemptions_are_eligible(self, base_record, name):
        """All advisory exemptions should be eligible without org chart."""
        base_record["name"] = name
        base_record["organization_type"] = "Advisory or Regulatory Organization"
        result = evaluate_eligibility(base_record)
        assert result.eligible is True


# =============================================================================
# in_org_chart value handling tests
# =============================================================================


class TestInOrgChartValues:
    """Test various in_org_chart value representations."""

    @pytest.fixture
    def division_record(self):
        """Division record for testing in_org_chart values."""
        return {
            "record_id": "100300",
            "name": "Test Division",
            "operational_status": "Active",
            "organization_type": "Division",
            "url": "https://www.nyc.gov/division",
        }

    @pytest.mark.parametrize("value", ["True", "true", "TRUE", "1", "t", "yes", "YES"])
    def test_truthy_values_accepted(self, division_record, value):
        """Various truthy representations should be accepted."""
        division_record["in_org_chart"] = value
        result = evaluate_eligibility(division_record)
        assert result.eligible is True

    @pytest.mark.parametrize("value", ["False", "false", "0", "f", "no", "", None])
    def test_falsy_values_rejected(self, division_record, value):
        """Falsy values should result in ineligibility for divisions."""
        division_record["in_org_chart"] = value if value is not None else ""
        result = evaluate_eligibility(division_record)
        assert result.eligible is False


# =============================================================================
# Reasoning string tests
# =============================================================================


class TestReasoningStrings:
    """Test that reasoning strings are properly generated."""

    def test_eligible_record_has_reasoning(self):
        """Eligible records should have meaningful reasoning."""
        record = {
            "record_id": "100400",
            "name": "Test Agency",
            "operational_status": "Active",
            "organization_type": "Mayoral Agency",
            "url": "https://www.nyc.gov/test",
        }
        result = evaluate_eligibility(record)
        assert result.reasoning is not None
        assert len(result.reasoning) > 0
        assert result.reasoning_detailed is not None
        assert len(result.reasoning_detailed) > 0

    def test_ineligible_record_has_reasoning(self):
        """Ineligible records should have reasoning explaining why."""
        record = {
            "record_id": "100401",
            "name": "Inactive Agency",
            "operational_status": "Inactive",
            "organization_type": "Mayoral Agency",
            "url": "https://www.nyc.gov/test",
        }
        result = evaluate_eligibility(record)
        assert result.reasoning is not None
        assert len(result.reasoning) > 0

    def test_reasoning_detailed_contains_all_rules(self):
        """Detailed reasoning should mention gatekeeper and type rules."""
        record = {
            "record_id": "100402",
            "name": "Test Agency",
            "operational_status": "Active",
            "organization_type": "Mayoral Agency",
            "url": "https://www.nyc.gov/test",
        }
        result = evaluate_eligibility(record)
        assert "GATEKEEPER" in result.reasoning_detailed
        assert "TYPE-SPECIFIC" in result.reasoning_detailed


# =============================================================================
# Edge case tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_record(self):
        """Empty record should not crash, should be ineligible."""
        record = {}
        result = evaluate_eligibility(record)
        assert result.eligible is False

    def test_missing_fields(self):
        """Records with missing fields should handle gracefully."""
        record = {
            "record_id": "100500",
            "name": "Minimal Record",
        }
        result = evaluate_eligibility(record)
        assert result.eligible is False

    def test_whitespace_in_status(self):
        """Whitespace in operational_status should be trimmed."""
        record = {
            "record_id": "100501",
            "name": "Whitespace Agency",
            "operational_status": "  Active  ",
            "organization_type": "Mayoral Agency",
            "url": "https://www.nyc.gov/test",
        }
        result = evaluate_eligibility(record)
        # Should still be eligible (Active status has whitespace but should be trimmed)
        assert result.eligible is True

    def test_case_insensitive_status(self):
        """Operational status should be case-insensitive."""
        record = {
            "record_id": "100502",
            "name": "Case Test Agency",
            "organization_type": "Mayoral Agency",
            "url": "https://www.nyc.gov/test",
        }

        for status in ["Active", "ACTIVE", "active", "AcTiVe"]:
            record["operational_status"] = status
            result = evaluate_eligibility(record)
            assert result.eligible is True, f"Status '{status}' should be accepted"


# =============================================================================
# Regression snapshot test
# =============================================================================


class TestRegressionSnapshot:
    """
    Snapshot tests to catch unintended changes in eligibility outcomes.

    If these tests fail after a code change, verify the change is intentional
    and update the expected values accordingly.
    """

    EXPECTED_OUTCOMES = [
        # (record_id, name, org_type, status, in_org_chart, expected_eligible)
        ("100600", "NYC Department of Finance", "Mayoral Agency", "Active", "", True),
        (
            "100601",
            "Mayor's Office of Operations",
            "Mayoral Office",
            "Active",
            "",
            True,
        ),
        ("100602", "City Council", "Elected Office", "Active", "", True),
        (
            "100603",
            "New York City Employee Retirement System",
            "Pension Fund",
            "Active",
            "",
            True,
        ),
        # Non-allowlisted pension fund should be excluded
        (
            "100603b",
            "Cultural Institutions Retirement System",
            "Pension Fund",
            "Active",
            "",
            False,
        ),
        ("100604", "MTA", "State Government Agency", "Active", "", True),
        ("100605", "IT Division", "Division", "Active", "True", True),
        ("100606", "IT Division", "Division", "Active", "", False),
        (
            "100607",
            "NYC EDC",
            "Public Benefit or Development Organization",
            "Active",
            "True",
            True,
        ),
        (
            "100608",
            "NYC EDC",
            "Public Benefit or Development Organization",
            "Active",
            "",
            False,
        ),
        (
            "100609",
            "Brooklyn Public Library",
            "Nonprofit Organization",
            "Active",
            "",
            True,
        ),
        ("100610", "Random Nonprofit", "Nonprofit Organization", "Active", "", False),
        (
            "100611",
            "Random Nonprofit",
            "Nonprofit Organization",
            "Active",
            "True",
            True,
        ),
        (
            "100612",
            "Board of Elections",
            "Advisory or Regulatory Organization",
            "Active",
            "",
            True,
        ),
        (
            "100613",
            "Random Board",
            "Advisory or Regulatory Organization",
            "Active",
            "",
            False,
        ),
        (
            "100614",
            "Random Board",
            "Advisory or Regulatory Organization",
            "Active",
            "True",
            True,
        ),
        ("100615", "Dissolved Agency", "Mayoral Agency", "Dissolved", "", False),
        ("100616", "Inactive Office", "Mayoral Office", "Inactive", "", False),
    ]

    @pytest.mark.parametrize(
        "record_id,name,org_type,status,in_org_chart,expected",
        EXPECTED_OUTCOMES,
    )
    def test_expected_outcome(
        self, record_id, name, org_type, status, in_org_chart, expected
    ):
        """Verify expected eligibility outcomes match."""
        record = {
            "record_id": record_id,
            "name": name,
            "organization_type": org_type,
            "operational_status": status,
            "in_org_chart": in_org_chart,
            "url": "https://www.nyc.gov/test",
        }
        result = evaluate_eligibility(record)
        assert result.eligible is expected, (
            f"Record '{name}' ({org_type}): "
            f"expected {expected}, got {result.eligible}\n"
            f"Reasoning: {result.reasoning}"
        )
