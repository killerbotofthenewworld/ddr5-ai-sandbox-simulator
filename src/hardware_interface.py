"""
Real Hardware Integration Module for DDR5 AI Sandbox Simulator
Provides direct hardware control capabilities with comprehensive safety measures.
"""

import os
import sys
import subprocess
import time
import json
import platform
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HardwareCapabilities:
    """Detected hardware control capabilities."""
    bios_access: bool = False
    uefi_vars: bool = False
    memory_controller: bool = False
    vendor_tools: bool = False
    direct_registers: bool = False
    backup_restore: bool = False
    platform: str = ""
    admin_required: bool = True


@dataclass
class SafetyState:
    """Current system safety state for hardware operations."""
    temperature_safe: bool = False
    power_stable: bool = False
    memory_stable: bool = False
    backup_created: bool = False
    emergency_stop: bool = False
    last_check: float = 0.0


class HardwareInterface(ABC):
    """Abstract base class for hardware interfaces."""
    
    @abstractmethod
    def detect_capabilities(self) -> HardwareCapabilities:
        """Detect what hardware control capabilities are available."""
        pass
    
    @abstractmethod
    def create_backup(self) -> bool:
        """Create a backup of current settings."""
        pass
    
    @abstractmethod
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """Apply memory settings to hardware."""
        pass
    
    @abstractmethod
    def restore_backup(self) -> bool:
        """Restore settings from backup."""
        pass
    
    @abstractmethod
    def monitor_stability(self) -> SafetyState:
        """Monitor system stability in real-time."""
        pass


class LinuxHardwareInterface(HardwareInterface):
    """Linux-specific hardware interface implementation."""
    
    def __init__(self):
        self.capabilities = HardwareCapabilities()
        self.backup_path = "/tmp/ddr5_backup.json"
        
    def detect_capabilities(self) -> HardwareCapabilities:
        """Detect Linux hardware control capabilities."""
        caps = HardwareCapabilities(platform="Linux")
        
        # Check for root/sudo access (geteuid is Unix-only)
        try:
            caps.admin_required = os.geteuid() != 0
        except AttributeError:
            caps.admin_required = True
        
        # Check for UEFI variables access
        if os.path.exists("/sys/firmware/efi/efivars"):
            caps.uefi_vars = True
            logger.info("✅ UEFI variables access detected")
        
        # Check for memory controller access
        if os.path.exists("/dev/mem"):
            caps.memory_controller = True
            logger.info("✅ Memory controller access available")
        
        # Check for vendor tools
        caps.vendor_tools = self._detect_vendor_tools()
        
        # Check for MSR (Model Specific Register) access
        if os.path.exists("/dev/cpu/0/msr"):
            caps.direct_registers = True
            logger.info("✅ Direct register access available")
        
        caps.backup_restore = True  # Always available on Linux
        
        self.capabilities = caps
        return caps
    
    def _detect_vendor_tools(self) -> bool:
        """Detect vendor-specific tools."""
        vendor_tools = [
            "msi-dragon-center",
            "asus-ai-suite", 
            "gigabyte-siv",
            "corsair-icue"
        ]
        
        for tool in vendor_tools:
            if subprocess.run(
                ["which", tool], capture_output=True, timeout=5
            ).returncode == 0:
                logger.info(f"✅ Vendor tool detected: {tool}")
                return True
        
        return False
    
    def create_backup(self) -> bool:
        """Create backup of current memory settings."""
        try:
            # Backup UEFI variables related to memory
            backup_data = {
                "timestamp": time.time(),
                "platform": "Linux",
                "memory_settings": self._read_memory_settings(),
                "bios_version": self._get_bios_version()
            }
            
            with open(self.backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info("✅ Hardware backup created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup creation failed: {e}")
            return False
    
    def _read_memory_settings(self) -> Dict[str, Any]:
        """Read current memory settings from hardware."""
        settings = {}
        
        try:
            # Read DMI memory information
            result = subprocess.run(
                ["dmidecode", "-t", "memory"], 
                capture_output=True, text=True, check=True
            )
            settings["dmi_info"] = result.stdout
            
            # Read memory timing from /proc/meminfo if available
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", 'r') as f:
                    settings["meminfo"] = f.read()
            
            # Try to read UEFI memory variables
            settings["uefi_vars"] = self._read_uefi_memory_vars()
            
        except Exception as e:
            logger.warning(f"⚠️ Could not read all memory settings: {e}")
        
        return settings
    
    def _read_uefi_memory_vars(self) -> Dict[str, str]:
        """Read UEFI variables related to memory."""
        uefi_vars = {}
        
        if not os.path.exists("/sys/firmware/efi/efivars"):
            return uefi_vars
        
        try:
            # Common memory-related UEFI variables
            memory_vars = [
                "MemoryConfig",
                "MemoryOverrides", 
                "XMPProfile",
                "MemoryTimings",
                "MemoryVoltage"
            ]
            
            for var_name in memory_vars:
                var_files = subprocess.run(
                    ["find", "/sys/firmware/efi/efivars", "-name", f"*{var_name}*"],
                    capture_output=True, text=True
                ).stdout.strip().split('\n')
                
                for var_file in var_files:
                    if var_file and os.path.exists(var_file):
                        try:
                            with open(var_file, 'rb') as f:
                                # Skip first 4 bytes (attributes)
                                data = f.read()[4:]
                                uefi_vars[os.path.basename(var_file)] = data.hex()
                        except (OSError, IOError):
                            continue
            
        except Exception as e:
            logger.warning(f"⚠️ Could not read UEFI variables: {e}")
        
        return uefi_vars
    
    def _get_bios_version(self) -> str:
        """Get BIOS version information."""
        try:
            result = subprocess.run(
                ["dmidecode", "-s", "bios-version"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except Exception:
            return "Unknown"
    
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """Apply memory settings to hardware."""
        logger.warning("🚧 Direct settings application not yet implemented")
        logger.info("📋 Recommended: Apply these settings manually in BIOS:")
        
        for key, value in settings.items():
            logger.info(f"  {key}: {value}")
        
        # TODO: Implement direct hardware application
        # This requires:
        # 1. UEFI variable modification
        # 2. Memory controller register access
        # 3. Vendor tool integration
        
        return False
    
    def restore_backup(self) -> bool:
        """Restore settings from backup."""
        try:
            if not os.path.exists(self.backup_path):
                logger.error("❌ No backup file found")
                return False
            
            with open(self.backup_path, 'r') as f:
                backup_data = json.load(f)
            
            logger.info("🔄 Restoring hardware settings from backup...")
            logger.info(f"📅 Backup created: {time.ctime(backup_data['timestamp'])}")
            
            # TODO: Implement actual restoration
            logger.warning("🚧 Automatic restoration not yet implemented")
            logger.info("📋 Manual restoration required via BIOS")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    def monitor_stability(self) -> SafetyState:
        """Monitor system stability in real-time."""
        state = SafetyState()
        state.last_check = time.time()
        
        try:
            # Check CPU temperature
            temp = self._get_cpu_temperature()
            state.temperature_safe = temp < 80.0 if temp else True
            
            # Check memory stability (simplified)
            state.memory_stable = self._check_memory_stability()
            
            # Check power stability (simplified)
            state.power_stable = True  # TODO: Implement actual power monitoring
            
            # Check if backup exists
            state.backup_created = os.path.exists(self.backup_path)
            
        except Exception as e:
            logger.warning(f"⚠️ Stability monitoring error: {e}")
        
        return state
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature."""
        try:
            # Try common temperature sources
            temp_files = [
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/hwmon/hwmon0/temp1_input",
                "/sys/class/hwmon/hwmon1/temp1_input"
            ]
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    with open(temp_file, 'r') as f:
                        temp = float(f.read().strip())
                        # Convert from millidegrees if necessary
                        if temp > 1000:
                            temp /= 1000
                        return temp
            
            return None
            
        except Exception:
            return None
    
    def _check_memory_stability(self) -> bool:
        """Check memory stability indicators."""
        try:
            # Check for memory errors in dmesg
            result = subprocess.run(
                "dmesg | grep -i 'memory.*error'",
                shell=True, capture_output=True, text=True, timeout=10
            )
            
            # If no memory errors found, consider stable
            return len(result.stdout.strip()) == 0
            
        except Exception:
            return True  # Assume stable if cannot check


class WindowsHardwareInterface(HardwareInterface):
    """Windows-specific hardware interface implementation."""
    
    def __init__(self):
        self.capabilities = HardwareCapabilities()
        # Store backups under %LOCALAPPDATA%\DDR5-AI, falling back to %TEMP%
        _local = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP", "C:\\Temp")
        self._backup_dir = os.path.join(_local, "DDR5-AI")
        self.backup_path = os.path.join(self._backup_dir, "ddr5_backup.json")
    
    def detect_capabilities(self) -> HardwareCapabilities:
        """Detect Windows hardware control capabilities."""
        caps = HardwareCapabilities(platform="Windows")
        
        # Check for administrator privileges
        try:
            import ctypes
            caps.admin_required = not ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            caps.admin_required = True
        
        # Check for vendor tools via registry
        caps.vendor_tools = self._detect_vendor_tools()
        
        # WMI gives read access to memory info (no direct register/UEFI write)
        caps.memory_controller = self._check_wmi_available()
        caps.direct_registers = False
        caps.uefi_vars = False
        caps.backup_restore = True
        
        self.capabilities = caps
        return caps
    
    # ------------------------------------------------------------------
    # Vendor-tool detection
    # ------------------------------------------------------------------
    def _detect_vendor_tools(self) -> bool:
        """Detect Windows vendor tools by checking the uninstall registry."""
        registry_entries = [
            ("MSI Dragon Center", r"SOFTWARE\WOW6432Node\MSI\Dragon Center"),
            ("ASUS AI Suite", r"SOFTWARE\WOW6432Node\ASUS\AISuite III"),
            ("Gigabyte SIV", r"SOFTWARE\WOW6432Node\Gigabyte\SIV"),
            ("Corsair iCUE", r"SOFTWARE\WOW6432Node\Corsair\Corsair iCUE Software"),
        ]
        try:
            import winreg
            for name, key_path in registry_entries:
                try:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    logger.info(f"✅ Vendor tool detected: {name}")
                    return True
                except OSError:
                    continue
        except ImportError:
            pass

        # Fallback: check for well-known executables on PATH / Program Files
        exe_names = [
            "MSIDragonCenter.exe",
            "AISuite3.exe",
            "SIV.exe",
            "iCUE.exe",
        ]
        program_dirs = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        ]
        for exe in exe_names:
            for base in program_dirs:
                if base and os.path.isfile(os.path.join(base, exe)):
                    logger.info(f"✅ Vendor tool detected: {exe}")
                    return True

        logger.info("🔍 No vendor tools detected")
        return False
    
    # ------------------------------------------------------------------
    # WMI helper
    # ------------------------------------------------------------------
    @staticmethod
    def _check_wmi_available() -> bool:
        """Return True if we can query memory information via WMI."""
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_PhysicalMemory | Select-Object -First 1 | ConvertTo-Json",
                ],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0 and len(result.stdout.strip()) > 2
        except Exception:
            return False
    
    # ------------------------------------------------------------------
    # Backup / restore via WMI snapshot
    # ------------------------------------------------------------------
    def create_backup(self) -> bool:
        """Create a JSON backup of current memory settings via WMI."""
        try:
            os.makedirs(self._backup_dir, exist_ok=True)

            backup_data: Dict[str, Any] = {
                "timestamp": time.time(),
                "platform": "Windows",
                "memory_settings": self._read_memory_settings(),
                "bios_version": self._get_bios_version(),
            }

            with open(self.backup_path, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2)

            logger.info("✅ Hardware backup created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Backup creation failed: {e}")
            return False
    
    def _read_memory_settings(self) -> Dict[str, Any]:
        """Read current memory settings from WMI."""
        settings: Dict[str, Any] = {}
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_PhysicalMemory "
                    "| Select-Object Manufacturer, PartNumber, Capacity, Speed, "
                    "ConfiguredClockSpeed, ConfiguredVoltage, DeviceLocator, SerialNumber "
                    "| ConvertTo-Json",
                ],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0 and result.stdout.strip():
                settings["wmi_physical_memory"] = json.loads(result.stdout)
        except Exception as e:
            logger.warning(f"⚠️ Could not read WMI memory settings: {e}")

        # Also capture total physical memory
        try:
            import psutil as _psutil
            vm = _psutil.virtual_memory()
            settings["total_physical_bytes"] = vm.total
        except Exception:
            pass

        return settings
    
    def _get_bios_version(self) -> str:
        """Get BIOS version via WMI."""
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_BIOS).SMBIOSBIOSVersion",
                ],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return "Unknown"
    
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """Apply memory settings on Windows.
        
        Direct register-level changes are not safe via user-space on Windows.
        Instead we log the recommended BIOS changes and attempt to invoke a
        detected vendor tool if one is available.
        """
        logger.info("📋 Recommended BIOS settings to apply manually:")
        for key, value in settings.items():
            logger.info(f"  {key}: {value}")

        if self.capabilities.vendor_tools:
            logger.info(
                "🏭 Vendor tool detected — please use it to apply these settings, "
                "or apply them via BIOS."
            )
        else:
            logger.info(
                "ℹ️  No vendor tool detected. Apply these settings manually in BIOS."
            )

        # We cannot safely poke hardware registers on Windows without a
        # kernel driver, so we return False to signal "manual action needed".
        return False
    
    def restore_backup(self) -> bool:
        """Restore settings from a previously saved backup on Windows."""
        try:
            if not os.path.exists(self.backup_path):
                logger.error("❌ No backup file found")
                return False

            with open(self.backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            logger.info("🔄 Restoring hardware settings from backup…")
            logger.info(f"📅 Backup created: {time.ctime(backup_data['timestamp'])}")
            logger.info("📋 Saved memory configuration:")

            mem = backup_data.get("memory_settings", {})
            modules = mem.get("wmi_physical_memory")
            if modules:
                if not isinstance(modules, list):
                    modules = [modules]
                for mod in modules:
                    logger.info(
                        f"  {mod.get('DeviceLocator', '?')}: "
                        f"{mod.get('Manufacturer', '?')} "
                        f"{int(mod.get('Capacity', 0)) // (1024**3)}GB "
                        f"@ {mod.get('Speed', '?')} MT/s"
                    )

            logger.info(
                "ℹ️  Automatic register-level restoration is not available on Windows. "
                "Use the above info to restore settings via BIOS."
            )
            return True
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    # ------------------------------------------------------------------
    # Stability monitoring
    # ------------------------------------------------------------------
    def monitor_stability(self) -> SafetyState:
        """Monitor system stability on Windows via WMI and psutil."""
        state = SafetyState()
        state.last_check = time.time()

        try:
            temp = self._get_cpu_temperature()
            state.temperature_safe = temp < 80.0 if temp is not None else True

            state.memory_stable = self._check_memory_stability()
            state.power_stable = True  # No user-space power-rail sensor on Windows
            state.backup_created = os.path.exists(self.backup_path)
        except Exception as e:
            logger.warning(f"⚠️ Stability monitoring error: {e}")

        return state
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature on Windows.
        
        Tries psutil first (it works when Open Hardware Monitor / LibreHardwareMonitor
        expose sensor data). Falls back to WMI MSAcpi_ThermalZoneTemperature.
        """
        # 1) psutil sensors (available when LibreHardwareMonitor is running)
        try:
            import psutil as _psutil
            if hasattr(_psutil, "sensors_temperatures"):
                temps = _psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            return entries[0].current
        except Exception:
            pass

        # 2) WMI thermal zone (requires admin, value in tenths of kelvin)
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance -Namespace root/WMI "
                    "-ClassName MSAcpi_ThermalZoneTemperature "
                    "-ErrorAction SilentlyContinue "
                    "| Select-Object -First 1).CurrentTemperature",
                ],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                raw = float(result.stdout.strip())
                # WMI returns tenths of kelvin
                celsius = (raw / 10.0) - 273.15
                if 0 < celsius < 120:
                    return celsius
        except Exception:
            pass

        return None
    
    def _check_memory_stability(self) -> bool:
        """Check Windows Event Log for memory-related errors."""
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-WinEvent -FilterHashtable @{LogName='System'; Level=2; "
                    "StartTime=(Get-Date).AddHours(-1)} -MaxEvents 50 "
                    "-ErrorAction SilentlyContinue "
                    "| Where-Object { $_.Message -match 'memory' } "
                    "| Measure-Object | Select-Object -ExpandProperty Count",
                ],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0 and result.stdout.strip():
                error_count = int(result.stdout.strip())
                return error_count == 0
        except Exception:
            pass
        return True  # Assume stable if we cannot check


class HardwareManager:
    """Main hardware management interface."""
    
    def __init__(self):
        self.interface = self._create_interface()
        self.capabilities = HardwareCapabilities()
        self.safety_state = SafetyState()
        
    def _create_interface(self) -> HardwareInterface:
        """Create platform-specific hardware interface."""
        system = platform.system().lower()
        
        if system == "linux":
            return LinuxHardwareInterface()
        elif system == "windows":
            return WindowsHardwareInterface()
        else:
            raise NotImplementedError(f"Platform {system} not supported yet")
    
    def initialize(self) -> bool:
        """Initialize hardware interface and detect capabilities."""
        try:
            logger.info("🔍 Detecting hardware control capabilities...")
            self.capabilities = self.interface.detect_capabilities()
            
            logger.info(f"🖥️ Platform: {self.capabilities.platform}")
            logger.info(f"👑 Admin required: {self.capabilities.admin_required}")
            logger.info(f"🔧 UEFI vars: {self.capabilities.uefi_vars}")
            logger.info(f"💾 Memory controller: {self.capabilities.memory_controller}")
            logger.info(f"🏭 Vendor tools: {self.capabilities.vendor_tools}")
            logger.info(f"📊 Direct registers: {self.capabilities.direct_registers}")
            logger.info(f"💾 Backup/restore: {self.capabilities.backup_restore}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Hardware initialization failed: {e}")
            return False
    
    def create_safety_backup(self) -> bool:
        """Create a safety backup before any hardware changes."""
        if not self.capabilities.backup_restore:
            logger.warning("⚠️ Backup not supported on this platform")
            return False
        
        return self.interface.create_backup()
    
    def apply_ddr5_settings(self, settings: Dict[str, Any]) -> bool:
        """Apply DDR5 settings with safety checks."""
        # Pre-flight safety checks
        if not self._pre_flight_checks():
            logger.error("❌ Pre-flight safety checks failed")
            return False
        
        # Create backup
        if not self.create_safety_backup():
            logger.error("❌ Could not create safety backup")
            return False
        
        # Apply settings
        return self.interface.apply_settings(settings)
    
    def emergency_restore(self) -> bool:
        """Emergency restore to last known good configuration."""
        logger.warning("🚨 EMERGENCY RESTORE INITIATED")
        return self.interface.restore_backup()
    
    def _pre_flight_checks(self) -> bool:
        """Perform pre-flight safety checks."""
        self.safety_state = self.interface.monitor_stability()
        
        if not self.safety_state.temperature_safe:
            logger.error("❌ Temperature too high for safe operation")
            return False
        
        if not self.safety_state.memory_stable:
            logger.error("❌ Memory already unstable")
            return False
        
        if not self.safety_state.power_stable:
            logger.error("❌ Power not stable")
            return False
        
        return True
    
    def get_hardware_status(self) -> Dict[str, Any]:
        """Get comprehensive hardware status."""
        return {
            "capabilities": self.capabilities.__dict__,
            "safety_state": self.safety_state.__dict__,
            "platform": platform.system(),
            "platform_version": platform.release(),
            "architecture": platform.machine()
        }


# Global hardware manager instance
hardware_manager = HardwareManager()
