"""
Hardware Detection Module for DDR5 AI Sandbox Simulator
Detects system memory and provides hardware information.
"""

import platform
import subprocess
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DetectedRAMModule:
    """Represents a detected RAM module in the system."""
    manufacturer: str
    part_number: str
    capacity_gb: int
    speed_mt_s: int
    slot_location: str
    serial_number: Optional[str] = None
    voltage: Optional[float] = None
    form_factor: str = "DIMM"
    chip_type: Optional[str] = None
    
    def __str__(self) -> str:
        return (f"{self.manufacturer} {self.part_number} "
                f"{self.capacity_gb}GB DDR5-{self.speed_mt_s}")


class HardwareDetector:
    """Detects and identifies system memory hardware."""
    
    def __init__(self):
        """Initialize hardware detector."""
        self.detected_modules: List[DetectedRAMModule] = []
        self.system_info: Dict[str, str] = {}
        self.detection_method: str = ""
        
    def detect_system_memory(self) -> List[DetectedRAMModule]:
        """
        Detect RAM modules in the current system.
        
        Returns:
            List of detected RAM modules
        """
        self.system_info = self._get_system_info()
        
        # Try different detection methods based on OS
        if platform.system() == "Linux":
            modules = self._detect_linux_memory()
        elif platform.system() == "Windows":
            modules = self._detect_windows_memory()
        elif platform.system() == "Darwin":  # macOS
            modules = self._detect_macos_memory()
        else:
            print(f"⚠️  Hardware detection not yet supported on {platform.system()}")
            modules = self._create_demo_modules()
            
        self.detected_modules = modules
        return modules
    
    def _detect_linux_memory(self) -> List[DetectedRAMModule]:
        """Detect memory on Linux systems."""
        modules = []
        self.detection_method = "Linux DMI/dmidecode"
        
        try:
            # Try dmidecode first (requires sudo)
            result = subprocess.run([
                'sudo', 'dmidecode', '--type', 'memory'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                modules = self._parse_dmidecode_output(result.stdout)
                if modules:
                    return modules
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            pass
        
        # Try /proc/meminfo for basic info
        try:
            modules = self._detect_linux_proc_meminfo()
            if modules:
                self.detection_method = "Linux /proc/meminfo"
                return modules
        except Exception:
            pass
        
        # Fallback to lshw if available
        try:
            result = subprocess.run([
                'lshw', '-class', 'memory'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                modules = self._parse_lshw_output(result.stdout)
                if modules:
                    self.detection_method = "Linux lshw"
                    return modules
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # If all else fails, create demo data
        print("📋 Could not detect hardware details, using demo configuration")
        return self._create_demo_modules()
    
    def _detect_windows_memory(self) -> List[DetectedRAMModule]:
        """Detect memory on Windows systems."""
        modules = []
        self.detection_method = "Windows WMI"
        
        try:
            # Use PowerShell to query WMI
            powershell_cmd = """
            Get-WmiObject -Class Win32_PhysicalMemory | Select-Object Manufacturer, PartNumber, Capacity, Speed, DeviceLocator, SerialNumber | ConvertTo-Json
            """
            
            result = subprocess.run([
                'powershell', '-Command', powershell_cmd
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                modules = self._parse_windows_wmi_output(result.stdout)
                if modules:
                    return modules
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print("📋 Could not detect Windows hardware details, using demo configuration")
        return self._create_demo_modules()
    
    def _detect_macos_memory(self) -> List[DetectedRAMModule]:
        """Detect memory on macOS systems."""
        modules = []
        self.detection_method = "macOS system_profiler"
        
        try:
            result = subprocess.run([
                'system_profiler', 'SPMemoryDataType', '-json'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                modules = self._parse_macos_output(result.stdout)
                if modules:
                    return modules
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print("📋 Could not detect macOS hardware details, using demo configuration")
        return self._create_demo_modules()
    
    def _parse_dmidecode_output(self, output: str) -> List[DetectedRAMModule]:
        """Parse dmidecode output to extract memory information."""
        modules = []
        current_module = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if 'Memory Device' in line:
                if current_module and current_module.get('Size', '') != 'No Module Installed':
                    module = self._create_module_from_dmidecode(current_module)
                    if module:
                        modules.append(module)
                current_module = {}
            
            elif ':' in line:
                key, value = line.split(':', 1)
                current_module[key.strip()] = value.strip()
        
        # Don't forget the last module
        if current_module and current_module.get('Size', '') != 'No Module Installed':
            module = self._create_module_from_dmidecode(current_module)
            if module:
                modules.append(module)
        
        return modules
    
    def _create_module_from_dmidecode(self, data: Dict[str, str]) -> Optional[DetectedRAMModule]:
        """Create a DetectedRAMModule from dmidecode data."""
        try:
            # Skip empty slots
            size_str = data.get('Size', '')
            if 'No Module Installed' in size_str or not size_str:
                return None
            
            # Parse capacity
            capacity_match = re.search(r'(\d+)\s*GB', size_str)
            capacity_gb = int(capacity_match.group(1)) if capacity_match else 0
            
            # Parse speed
            speed_str = data.get('Speed', '0')
            speed_match = re.search(r'(\d+)', speed_str)
            speed_mt_s = int(speed_match.group(1)) if speed_match else 0
            
            # Only include DDR5
            type_str = data.get('Type', '')
            if 'DDR5' not in type_str:
                return None
            
            return DetectedRAMModule(
                manufacturer=data.get('Manufacturer', 'Unknown').strip(),
                part_number=data.get('Part Number', 'Unknown').strip(),
                capacity_gb=capacity_gb,
                speed_mt_s=speed_mt_s,
                slot_location=data.get('Locator', 'Unknown'),
                serial_number=data.get('Serial Number', '').strip() or None,
                voltage=float(data.get('Configured Voltage', '1.1').replace('V', '')) if data.get('Configured Voltage') else None
            )
        except (ValueError, AttributeError):
            return None
    
    def _detect_linux_proc_meminfo(self) -> List[DetectedRAMModule]:
        """Basic memory detection from /proc/meminfo."""
        try:
            with open('/proc/meminfo', 'r') as f:
                content = f.read()
            
            total_match = re.search(r'MemTotal:\s*(\d+)\s*kB', content)
            if total_match:
                total_kb = int(total_match.group(1))
                total_gb = round(total_kb / (1024 * 1024))
                
                # Create a generic module
                return [DetectedRAMModule(
                    manufacturer="Generic",
                    part_number="Unknown DDR5",
                    capacity_gb=total_gb,
                    speed_mt_s=4800,  # Default DDR5 speed
                    slot_location="System",
                    chip_type="Unknown"
                )]
        except FileNotFoundError:
            pass
        
        return []
    
    def _parse_windows_wmi_output(self, output: str) -> List[DetectedRAMModule]:
        """Parse Windows WMI JSON output."""
        try:
            data = json.loads(output)
            modules = []
            
            # Handle both single object and array
            if not isinstance(data, list):
                data = [data]
            
            for item in data:
                capacity_bytes = int(item.get('Capacity', 0))
                capacity_gb = capacity_bytes // (1024**3)
                
                speed_mhz = int(item.get('Speed', 2400))
                speed_mt_s = speed_mhz * 2  # Convert MHz to MT/s for DDR
                
                module = DetectedRAMModule(
                    manufacturer=item.get('Manufacturer', 'Unknown').strip(),
                    part_number=item.get('PartNumber', 'Unknown').strip(),
                    capacity_gb=capacity_gb,
                    speed_mt_s=speed_mt_s,
                    slot_location=item.get('DeviceLocator', 'Unknown'),
                    serial_number=item.get('SerialNumber', '').strip() or None
                )
                modules.append(module)
            
            return modules
        except (json.JSONDecodeError, ValueError, KeyError):
            return []
    
    def _parse_macos_output(self, output: str) -> List[DetectedRAMModule]:
        """Parse macOS system_profiler JSON output."""
        try:
            data = json.loads(output)
            modules = []
            
            for item in data.get('SPMemoryDataType', []):
                for slot_data in item.get('_items', []):
                    size_str = slot_data.get('dimm_size', '0 GB')
                    capacity_match = re.search(r'(\d+)\s*GB', size_str)
                    capacity_gb = int(capacity_match.group(1)) if capacity_match else 0
                    
                    speed_str = slot_data.get('dimm_speed', '2400 MHz')
                    speed_match = re.search(r'(\d+)', speed_str)
                    speed_mhz = int(speed_match.group(1)) if speed_match else 2400
                    speed_mt_s = speed_mhz * 2  # Convert to MT/s
                    
                    module = DetectedRAMModule(
                        manufacturer=slot_data.get('dimm_manufacturer', 'Unknown'),
                        part_number=slot_data.get('dimm_part_number', 'Unknown'),
                        capacity_gb=capacity_gb,
                        speed_mt_s=speed_mt_s,
                        slot_location=slot_data.get('dimm_status', 'Unknown'),
                        chip_type=slot_data.get('dimm_type', 'Unknown')
                    )
                    modules.append(module)
            
            return modules
        except (json.JSONDecodeError, ValueError, KeyError):
            return []
    
    def _parse_lshw_output(self, output: str) -> List[DetectedRAMModule]:
        """Parse lshw output to extract memory information."""
        modules = []
        # Simple parsing for lshw output - this is a basic implementation
        # In practice, lshw output varies significantly
        lines = output.split('\n')
        current_module = {}
        
        for line in lines:
            line = line.strip()
            if 'bank' in line.lower() and 'memory' in line.lower():
                if current_module:
                    module = self._create_module_from_lshw(current_module)
                    if module:
                        modules.append(module)
                current_module = {}
            elif ':' in line and current_module is not None:
                key, value = line.split(':', 1)
                current_module[key.strip()] = value.strip()
        
        # Don't forget the last module
        if current_module:
            module = self._create_module_from_lshw(current_module)
            if module:
                modules.append(module)
        
        return modules
    
    def _create_module_from_lshw(self, data: Dict[str, str]) -> Optional[DetectedRAMModule]:
        """Create a DetectedRAMModule from lshw data."""
        try:
            size_str = data.get('size', '0')
            capacity_match = re.search(r'(\d+)GiB', size_str)
            capacity_gb = int(capacity_match.group(1)) if capacity_match else 0
            
            # Basic module creation for lshw
            return DetectedRAMModule(
                manufacturer=data.get('vendor', 'Unknown'),
                part_number=data.get('product', 'Unknown'),
                capacity_gb=capacity_gb,
                speed_mt_s=4800,  # Default speed
                slot_location=data.get('slot', 'Unknown')
            )
        except (ValueError, AttributeError):
            return None

    def _create_demo_modules(self) -> List[DetectedRAMModule]:
        """Create demo modules for systems where detection fails."""
        return [
            DetectedRAMModule(
                manufacturer="Corsair",
                part_number="CMK32GX5M2B5600C36",
                capacity_gb=16,
                speed_mt_s=5600,
                slot_location="DIMM_A1",
                chip_type="Samsung B-die",
                voltage=1.25
            ),
            DetectedRAMModule(
                manufacturer="Corsair", 
                part_number="CMK32GX5M2B5600C36",
                capacity_gb=16,
                speed_mt_s=5600,
                slot_location="DIMM_A2",
                chip_type="Samsung B-die",
                voltage=1.25
            )
        ]
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get basic system information."""
        info = {
            'os': platform.system(),
            'os_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'machine': platform.machine()
        }
        
        # Try to get CPU info per platform
        if platform.system() == "Linux":
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                cpu_match = re.search(r'model name\s*:\s*(.+)', cpuinfo)
                if cpu_match:
                    info['cpu_model'] = cpu_match.group(1).strip()
            except FileNotFoundError:
                pass
        elif platform.system() == "Windows":
            try:
                result = subprocess.run(
                    [
                        "powershell", "-NoProfile", "-Command",
                        "(Get-CimInstance Win32_Processor | Select-Object -First 1).Name",
                    ],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    info['cpu_model'] = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        return info
    
    def get_detection_summary(self) -> str:
        """Get a summary of the detection process."""
        if not self.detected_modules:
            return "❌ No DDR5 modules detected"
        
        total_capacity = sum(module.capacity_gb for module in self.detected_modules)
        module_count = len(self.detected_modules)
        
        summary = f"✅ Detected {module_count} DDR5 module(s) - Total: {total_capacity}GB\n"
        summary += f"🔍 Detection method: {self.detection_method}\n"
        summary += f"💻 System: {self.system_info.get('os', 'Unknown')} {self.system_info.get('architecture', '')}\n"
        
        for i, module in enumerate(self.detected_modules, 1):
            summary += f"  📦 Module {i}: {module}\n"
        
        return summary


# Global hardware detector instance
hardware_detector = HardwareDetector()


def detect_system_memory() -> List[DetectedRAMModule]:
    """Convenience function to detect system memory."""
    return hardware_detector.detect_system_memory()


def get_detected_modules() -> List[DetectedRAMModule]:
    """Get currently detected modules."""
    return hardware_detector.detected_modules


def get_system_summary() -> str:
    """Get system detection summary."""
    return hardware_detector.get_detection_summary()
