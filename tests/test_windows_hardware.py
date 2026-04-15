"""
Tests for Windows hardware interface implementation.

These tests verify that the WindowsHardwareInterface class works correctly
on any platform by mocking Windows-specific calls (subprocess, ctypes, winreg).
"""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from src.hardware_interface import (
    WindowsHardwareInterface,
    HardwareCapabilities,
    SafetyState,
    HardwareManager,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def win_iface(tmp_path):
    """Create a WindowsHardwareInterface with backup path in a temp dir."""
    iface = WindowsHardwareInterface.__new__(WindowsHardwareInterface)
    iface.capabilities = HardwareCapabilities()
    iface._backup_dir = str(tmp_path)
    iface.backup_path = str(tmp_path / "ddr5_backup.json")
    return iface


# ---------------------------------------------------------------------------
# detect_capabilities
# ---------------------------------------------------------------------------

class TestDetectCapabilities:
    def test_platform_is_windows(self, win_iface):
        with patch("src.hardware_interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            caps = win_iface.detect_capabilities()
        assert caps.platform == "Windows"
        assert caps.backup_restore is True

    def test_admin_detection_non_admin(self, win_iface):
        """When ctypes says not admin, admin_required should be True."""
        mock_ctypes = MagicMock()
        mock_ctypes.windll.shell32.IsUserAnAdmin.return_value = 0

        with patch.dict("sys.modules", {"ctypes": mock_ctypes}), \
             patch("src.hardware_interface.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            caps = win_iface.detect_capabilities()
        assert caps.admin_required is True


# ---------------------------------------------------------------------------
# create_backup / restore_backup
# ---------------------------------------------------------------------------

class TestBackupRestore:
    def test_create_backup_writes_json(self, win_iface):
        """create_backup should write a valid JSON file."""
        wmi_json = json.dumps([{
            "Manufacturer": "Corsair",
            "Capacity": str(16 * 1024**3),
            "Speed": "5600",
            "DeviceLocator": "DIMM_A1",
        }])

        mock_result = MagicMock(returncode=0, stdout=wmi_json)
        with patch("src.hardware_interface.subprocess.run", return_value=mock_result):
            assert win_iface.create_backup() is True

        assert os.path.exists(win_iface.backup_path)
        with open(win_iface.backup_path, "r") as f:
            data = json.load(f)
        assert "timestamp" in data
        assert data["platform"] == "Windows"
        assert "memory_settings" in data

    def test_restore_backup_no_file(self, win_iface):
        """restore_backup should return False when no backup exists."""
        assert win_iface.restore_backup() is False

    def test_restore_backup_reads_saved_data(self, win_iface):
        """restore_backup should read and log the saved configuration."""
        backup = {
            "timestamp": 1700000000,
            "platform": "Windows",
            "memory_settings": {
                "wmi_physical_memory": [{
                    "DeviceLocator": "DIMM_A1",
                    "Manufacturer": "Corsair",
                    "Capacity": str(16 * 1024**3),
                    "Speed": "5600",
                }]
            },
            "bios_version": "1.2.3",
        }
        with open(win_iface.backup_path, "w") as f:
            json.dump(backup, f)

        assert win_iface.restore_backup() is True


# ---------------------------------------------------------------------------
# monitor_stability
# ---------------------------------------------------------------------------

class TestMonitorStability:
    def test_returns_safety_state(self, win_iface):
        with patch("src.hardware_interface.subprocess.run") as mock_run:
            # CPU temp returns nothing useful → temperature_safe defaults to True
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            state = win_iface.monitor_stability()

        assert isinstance(state, SafetyState)
        assert state.last_check > 0
        assert state.temperature_safe is True
        assert state.memory_stable is True

    def test_cpu_temperature_high_is_unsafe(self, win_iface, tmp_path):
        """When WMI reports high temperature, temperature_safe should be False."""
        # 90°C in tenths-of-kelvin = (90 + 273.15) * 10 = 3631.5
        wmi_temp = str((90 + 273.15) * 10)

        calls = []

        def side_effect(*args, **kwargs):
            cmd_str = " ".join(args[0]) if args else ""
            calls.append(cmd_str)
            if "MSAcpi_ThermalZoneTemperature" in cmd_str:
                return MagicMock(returncode=0, stdout=wmi_temp)
            return MagicMock(returncode=1, stdout="")

        # Pre-create a backup so backup_created is True
        with open(win_iface.backup_path, "w") as f:
            json.dump({"timestamp": 0}, f)

        with patch("src.hardware_interface.subprocess.run", side_effect=side_effect):
            state = win_iface.monitor_stability()

        assert state.temperature_safe is False
        assert state.backup_created is True


# ---------------------------------------------------------------------------
# apply_settings
# ---------------------------------------------------------------------------

class TestApplySettings:
    def test_apply_returns_false(self, win_iface):
        """apply_settings always returns False (manual action required)."""
        win_iface.capabilities = HardwareCapabilities(vendor_tools=False)
        result = win_iface.apply_settings({"frequency": 5600, "cl": 32})
        assert result is False


# ---------------------------------------------------------------------------
# _check_memory_stability
# ---------------------------------------------------------------------------

class TestMemoryStability:
    def test_no_errors_is_stable(self, win_iface):
        mock = MagicMock(returncode=0, stdout="0")
        with patch("src.hardware_interface.subprocess.run", return_value=mock):
            assert win_iface._check_memory_stability() is True

    def test_errors_is_unstable(self, win_iface):
        mock = MagicMock(returncode=0, stdout="3")
        with patch("src.hardware_interface.subprocess.run", return_value=mock):
            assert win_iface._check_memory_stability() is False

    def test_failure_assumes_stable(self, win_iface):
        with patch("src.hardware_interface.subprocess.run", side_effect=Exception("fail")):
            assert win_iface._check_memory_stability() is True


# ---------------------------------------------------------------------------
# HardwareManager platform dispatch
# ---------------------------------------------------------------------------

class TestHardwareManagerDispatch:
    def test_windows_dispatch(self):
        with patch("src.hardware_interface.platform.system", return_value="Windows"):
            mgr = HardwareManager()
        assert isinstance(mgr.interface, WindowsHardwareInterface)
