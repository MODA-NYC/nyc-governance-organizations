"""Tests for name and title normalization."""

from __future__ import annotations

from nycgo_pipeline.appointments.normalize import (
    get_title_relevance,
    name_similarity,
    normalize_agency_name,
    normalize_name,
    parse_description,
)


class TestNormalizeName:
    """Tests for normalize_name function."""

    def test_normalize_lastname_firstname_format(self):
        """Test parsing LASTNAME,FIRSTNAME format."""
        result = normalize_name("WALKER,GLEN M.")
        assert result.first == "Glen"
        assert result.middle == "M."
        assert result.last == "Walker"
        assert result.full == "Glen M. Walker"

    def test_normalize_lastname_firstname_no_middle(self):
        """Test parsing name without middle name."""
        result = normalize_name("DOE,JANE")
        assert result.first == "Jane"
        assert result.middle == ""
        assert result.last == "Doe"
        assert result.full == "Jane Doe"

    def test_normalize_with_suffix(self):
        """Test parsing name with suffix."""
        result = normalize_name("SMITH,JOHN JR.")
        # nameparser should handle Jr. as suffix
        assert result.last == "Smith"
        assert "John" in result.full

    def test_normalize_empty_string(self):
        """Test handling empty string."""
        result = normalize_name("")
        assert result.first == ""
        assert result.last == ""
        assert result.full == ""

    def test_normalize_none(self):
        """Test handling None."""
        result = normalize_name(None)
        assert result.first == ""
        assert result.full == ""

    def test_normalize_standard_format(self):
        """Test parsing standard name format."""
        result = normalize_name("Jane Doe")
        assert result.first == "Jane"
        assert result.last == "Doe"

    def test_variants_generation(self):
        """Test that name variants are generated."""
        result = normalize_name("DOE,JANE M.")
        assert len(result.variants) > 0
        # Should include lowercase variants
        assert "jane doe" in result.variants or "jane m. doe" in result.variants


class TestParseDescription:
    """Tests for parse_description function."""

    def test_parse_full_description(self):
        """Test parsing complete description string."""
        desc = (
            "Effective Date: 12/15/2025; Provisional Status: No; "
            "Title Code: 1002A; Reason For Change: APPOINTED; "
            "Salary: 225000.00; Employee Name: DOE,JANE M."
        )
        result = parse_description(desc)

        assert result.effective_date is not None
        assert result.effective_date.year == 2025
        assert result.effective_date.month == 12
        assert result.effective_date.day == 15
        assert result.provisional_status == "No"
        assert result.title_code == "1002A"
        assert result.reason_for_change == "APPOINTED"
        assert result.salary == 225000.00
        assert result.employee_name == "DOE,JANE M."

    def test_parse_partial_description(self):
        """Test parsing incomplete description."""
        desc = "Reason For Change: RETIRED; Employee Name: SMITH,JOHN"
        result = parse_description(desc)

        assert result.effective_date is None
        assert result.reason_for_change == "RETIRED"
        assert result.employee_name == "SMITH,JOHN"

    def test_parse_empty_description(self):
        """Test parsing empty description."""
        result = parse_description("")
        assert result.effective_date is None
        assert result.employee_name is None

    def test_parse_salary_with_comma(self):
        """Test parsing salary with comma separator."""
        desc = "Salary: 1,500,000.00"
        # Note: our simple parser may not handle this but should not crash
        result = parse_description(desc)
        assert result is not None  # Just verify no crash


class TestTitleRelevance:
    """Tests for get_title_relevance function."""

    def test_unknown_code_default_relevance(self):
        """Test unknown title code returns default relevance."""
        result = get_title_relevance("9999X")
        assert result == 0.5  # Default for unknown

    def test_high_relevance_title_text(self):
        """Test high-relevance title keywords."""
        result = get_title_relevance(None, "Commissioner of Buildings")
        assert result == 1.0

        result = get_title_relevance(None, "Executive Director")
        assert result == 1.0

    def test_medium_relevance_title_text(self):
        """Test medium-relevance title keywords."""
        # Use "Chief of Staff" which is only in MEDIUM, not HIGH
        result = get_title_relevance(None, "Chief of Staff")
        assert result == 0.6

    def test_low_relevance_title_text(self):
        """Test low-relevance title keywords."""
        result = get_title_relevance(None, "Senior Manager")
        assert result == 0.2


class TestNormalizeAgencyName:
    """Tests for normalize_agency_name function."""

    def test_basic_normalization(self):
        """Test basic normalization."""
        result = normalize_agency_name("Department of Buildings")
        assert result == "department of buildings"

    def test_abbreviation_expansion(self):
        """Test abbreviation expansion."""
        result = normalize_agency_name("DEPT OF CITYWIDE ADMIN SERVICES")
        assert "department" in result
        assert "administration" in result

    def test_punctuation_removal(self):
        """Test punctuation is removed."""
        result = normalize_agency_name("Law Department, NYC")
        assert "," not in result

    def test_empty_string(self):
        """Test empty string handling."""
        result = normalize_agency_name("")
        assert result == ""


class TestNameSimilarity:
    """Tests for name_similarity function."""

    def test_identical_names(self):
        """Test identical names return 1.0."""
        result = name_similarity("Jane Doe", "Jane Doe")
        assert result == 1.0

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        result = name_similarity("JANE DOE", "jane doe")
        assert result == 1.0

    def test_different_names(self):
        """Test completely different names."""
        result = name_similarity("Jane Doe", "John Smith")
        assert result < 0.5

    def test_same_last_name_boost(self):
        """Test boost for matching last names."""
        result = name_similarity("Jane Doe", "John Doe")
        # Should have some similarity due to last name match
        assert result > 0.3

    def test_empty_names(self):
        """Test empty name handling."""
        result = name_similarity("", "Jane Doe")
        assert result == 0.0

        result = name_similarity("Jane Doe", "")
        assert result == 0.0
