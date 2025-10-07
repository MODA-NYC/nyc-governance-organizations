"""
Test suite for the populate_officer_name_parts function.

This module tests the name parsing functionality that populates detailed
officer name fields from the PrincipalOfficerName field.
"""

import sys
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
