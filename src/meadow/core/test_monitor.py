"""Unit tests for screen monitoring functionality"""

import unittest
from unittest.mock import patch, MagicMock
from Quartz import kCGWindowListOptionOnScreenOnly, kCGNullWindowID, kCGWindowOwnerName, kCGWindowName

from meadow.core.monitor import get_active_window_info

class TestMonitor(unittest.TestCase):
    """Test screen monitoring functionality"""

    def test_get_active_window(self):
        """Test getting active window information"""
        # Mock the Quartz function at the module level where it's imported
        with patch('meadow.core.monitor.CGWindowListCopyWindowInfo') as mock_window_list:
            mock_windows = [
                {
                    kCGWindowOwnerName: 'TestApp',
                    kCGWindowName: 'Test Window',
                    'kCGWindowIsOnscreen': 1,
                    'kCGWindowLayer': 0
                }
            ]
            mock_window_list.return_value = mock_windows

            window_info = get_active_window_info()
            self.assertEqual(window_info['app'], 'TestApp')
            self.assertEqual(window_info['title'], 'Test Window')

if __name__ == '__main__':
    unittest.main()
