"""
🔥 Pytest Deprecation Hunter Plugin - The Divine Test Guardian! ⚡

This pytest plugin catches deprecation warnings during test runs,
ensuring that no deprecated patterns slip through the sacred testing process.
"""

import warnings
import pytest
from typing import List, Dict, Any


class DeprecationHunter:
    """Divine hunter that captures deprecation warnings during tests."""
    
    def __init__(self):
        self.captured_warnings: List[Dict[str, Any]] = []
        self.original_showwarning = warnings.showwarning
        
    def setup(self):
        """Setup the hunter to capture warnings."""
        # Configure warnings to be captured
        warnings.filterwarnings('default', category=DeprecationWarning)
        warnings.filterwarnings('default', category=PendingDeprecationWarning)
        
        # Install our custom warning handler
        warnings.showwarning = self.capture_warning
        
    def capture_warning(self, message, category, filename, lineno, file=None, line=None):
        """Capture deprecation warnings for analysis."""
        if issubclass(category, (DeprecationWarning, PendingDeprecationWarning)):
            # Check if this is a Pydantic deprecation
            is_pydantic_warning = any(keyword in str(message).lower() for keyword in [
                'pydantic', 'config', 'basemodel', 'basesettings', 'configdict'
            ])
            
            warning_info = {
                'message': str(message),
                'category': category.__name__,
                'filename': filename,
                'lineno': lineno,
                'is_pydantic': is_pydantic_warning,
                'severity': 'critical' if is_pydantic_warning else 'warning'
            }
            
            self.captured_warnings.append(warning_info)
            
            # Still show the warning using original handler
            if self.original_showwarning:
                self.original_showwarning(message, category, filename, lineno, file, line)
        else:
            # Non-deprecation warnings use original handler
            if self.original_showwarning:
                self.original_showwarning(message, category, filename, lineno, file, line)
    
    def teardown(self):
        """Restore original warning handler."""
        warnings.showwarning = self.original_showwarning
    
    def get_pydantic_warnings(self) -> List[Dict[str, Any]]:
        """Get captured Pydantic-related warnings."""
        return [w for w in self.captured_warnings if w['is_pydantic']]
    
    def get_all_warnings(self) -> List[Dict[str, Any]]:
        """Get all captured deprecation warnings."""
        return self.captured_warnings.copy()


# Global hunter instance
deprecation_hunter = DeprecationHunter()


@pytest.fixture(autouse=True, scope='session')
def setup_deprecation_hunting():
    """Setup deprecation hunting for the entire test session."""
    deprecation_hunter.setup()
    yield
    deprecation_hunter.teardown()


@pytest.fixture
def deprecation_warnings():
    """Provide access to captured deprecation warnings in tests."""
    # Clear previous warnings for this test
    deprecation_hunter.captured_warnings.clear()
    yield deprecation_hunter
    # Warnings are automatically captured during test execution


def pytest_runtest_teardown(item, nextitem):
    """Check for deprecation warnings after each test."""
    pydantic_warnings = deprecation_hunter.get_pydantic_warnings()
    
    if pydantic_warnings:
        # Format warning messages
        warning_messages = []
        for warning in pydantic_warnings:
            msg = (f"🔥 PYDANTIC DEPRECATION in {item.nodeid}: "
                  f"{warning['message']} "
                  f"({warning['filename']}:{warning['lineno']}) ⚡")
            warning_messages.append(msg)
        
        # Print warnings
        for msg in warning_messages:
            print(f"\n{msg}")
        
        # Optionally fail the test (uncomment to make deprecations fail tests)
        # pytest.fail(f"Pydantic deprecation warnings detected:\n" + "\n".join(warning_messages))


def pytest_sessionfinish(session, exitstatus):
    """Report summary of deprecation warnings at end of test session."""
    all_warnings = deprecation_hunter.get_all_warnings()
    pydantic_warnings = deprecation_hunter.get_pydantic_warnings()
    
    if all_warnings:
        print(f"\n🔥 DEPRECATION HUNT SUMMARY ⚡")
        print("=" * 60)
        print(f"Total deprecation warnings: {len(all_warnings)}")
        print(f"Pydantic-related warnings: {len(pydantic_warnings)}")
        
        if pydantic_warnings:
            print(f"\n🚨 CRITICAL PYDANTIC WARNINGS:")
            print("-" * 40)
            for warning in pydantic_warnings:
                print(f"  {warning['filename']}:{warning['lineno']} - {warning['message']}")
            print(f"\n⚡ Fix these Pydantic warnings immediately! ⚡")
        
        other_warnings = [w for w in all_warnings if not w['is_pydantic']]
        if other_warnings:
            print(f"\n⚠️  OTHER DEPRECATION WARNINGS:")
            print("-" * 40)
            for warning in other_warnings:
                print(f"  {warning['filename']}:{warning['lineno']} - {warning['message']}")
    else:
        print(f"\n✅ NO DEPRECATION WARNINGS FOUND! Divine compliance achieved! ⚡")


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest with deprecation hunting."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "deprecation_sensitive: mark test as sensitive to deprecation warnings"
    )
    
    # Configure warnings to be more strict during testing
    warnings.simplefilter('default', DeprecationWarning)
    warnings.simplefilter('default', PendingDeprecationWarning)