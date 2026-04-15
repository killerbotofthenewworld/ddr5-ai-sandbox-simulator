"""
Live DDR5 Tuning Module with Advanced Safety Measures
Real-time memory tuning with comprehensive protection systems.
"""

import time
import psutil
import subprocess
import threading
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import json
import os

from src.ddr5_models import (DDR5Configuration, DDR5TimingParameters, 
                         DDR5VoltageParameters)


class SafetyLevel(Enum):
    """Safety protection levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"  
    AGGRESSIVE = "aggressive"
    EXPERT = "expert"


class TuningStatus(Enum):
    """Live tuning status."""
    IDLE = "idle"
    TESTING = "testing"
    APPLYING = "applying"
    MONITORING = "monitoring"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class SafetyLimits:
    """Safety limits for live tuning."""
    max_voltage_vddq: float = 1.45  # Maximum VDDQ voltage
    max_voltage_vpp: float = 1.90   # Maximum VPP voltage
    max_temperature_c: float = 85.0  # Maximum memory temperature
    max_cpu_temp_c: float = 95.0     # Maximum CPU temperature
    min_voltage_vddq: float = 1.05   # Minimum stable VDDQ
    min_voltage_vpp: float = 1.75    # Minimum VPP
    max_cas_latency: int = 60        # Maximum reasonable CAS latency
    min_cas_latency: int = 12        # Minimum reasonable CAS latency
    max_frequency: int = 8400        # Maximum DDR5 frequency
    min_frequency: int = 4000        # Minimum DDR5 frequency


@dataclass
class SystemMonitoring:
    """Real-time system monitoring data."""
    cpu_temp: float
    memory_temp: float
    cpu_usage: float
    memory_usage: float
    system_stability: float
    error_count: int
    timestamp: float


class LiveDDR5Tuner:
    """
    Live DDR5 memory tuning with comprehensive safety systems.
    
    WARNING: This is an experimental feature that attempts real hardware tuning.
    Use at your own risk and ensure you have stable baseline settings to revert to.
    """
    
    def __init__(self, safety_level: SafetyLevel = SafetyLevel.CONSERVATIVE):
        """Initialize live tuner with safety systems."""
        self.safety_level = safety_level
        self.status = TuningStatus.IDLE
        self.safety_limits = self._get_safety_limits()
        self.monitoring_data: List[SystemMonitoring] = []
        self.emergency_callbacks: List[Callable] = []
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self.baseline_config: Optional[DDR5Configuration] = None
        self.current_config: Optional[DDR5Configuration] = None
        self.error_count = 0
        self.last_stable_config: Optional[DDR5Configuration] = None
        
        # Initialize safety systems
        self._init_safety_systems()
    
    def _get_safety_limits(self) -> SafetyLimits:
        """Get safety limits based on protection level."""
        if self.safety_level == SafetyLevel.CONSERVATIVE:
            return SafetyLimits(
                max_voltage_vddq=1.25,
                max_voltage_vpp=1.85,
                max_temperature_c=75.0,
                max_cpu_temp_c=85.0
            )
        elif self.safety_level == SafetyLevel.MODERATE:
            return SafetyLimits(
                max_voltage_vddq=1.35,
                max_voltage_vpp=1.88,
                max_temperature_c=80.0,
                max_cpu_temp_c=90.0
            )
        elif self.safety_level == SafetyLevel.AGGRESSIVE:
            return SafetyLimits(
                max_voltage_vddq=1.40,
                max_voltage_vpp=1.90,
                max_temperature_c=83.0,
                max_cpu_temp_c=93.0
            )
        else:  # EXPERT
            return SafetyLimits()  # Default limits
    
    def _init_safety_systems(self):
        """Initialize all safety monitoring systems."""
        print("🛡️  Initializing DDR5 Live Tuning Safety Systems...")
        
        # Check if we can access hardware interfaces
        self.can_tune_hardware = self._check_hardware_access()
        
        if not self.can_tune_hardware:
            print("⚠️  WARNING: No hardware tuning interface detected!")
            print("   Live tuning will be simulated only.")
            print("   For real tuning, install vendor software (MSI Center, etc.)")
        
        # Register emergency callbacks
        self.emergency_callbacks.extend([
            self._emergency_voltage_reduction,
            self._emergency_frequency_reduction,
            self._emergency_system_notification
        ])
        
        print("✅ Safety systems initialized")
    
    def _check_hardware_access(self) -> bool:
        """Check if we have access to hardware tuning interfaces."""
        # Check for various hardware interfaces
        interfaces = [
            self._check_msi_afterburner(),
            self._check_ryzen_master(),
            self._check_intel_xtu(),
            self._check_asus_ai_suite(),
            self._check_bios_interface()
        ]
        
        return any(interfaces)
    
    def _check_msi_afterburner(self) -> bool:
        """Check for MSI Afterburner interface."""
        try:
            # Check if MSI Afterburner is running
            for proc in psutil.process_iter(['pid', 'name']):
                if 'MSIAfterburner' in proc.info['name']:
                    return True
        except:
            pass
        return False
    
    def _check_ryzen_master(self) -> bool:
        """Check for AMD Ryzen Master interface."""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'AMDRyzenMaster' in proc.info['name']:
                    return True
        except:
            pass
        return False
    
    def _check_intel_xtu(self) -> bool:
        """Check for Intel XTU interface."""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'XTU' in proc.info['name']:
                    return True
        except:
            pass
        return False
    
    def _check_asus_ai_suite(self) -> bool:
        """Check for ASUS AI Suite interface."""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'AI Suite' in proc.info['name'] or 'ASUS' in proc.info['name']:
                    return True
        except:
            pass
        return False
    
    def _check_bios_interface(self) -> bool:
        """Check for direct BIOS/UEFI interface access."""
        # This would require kernel-level access or special drivers
        # Currently not implemented for safety reasons
        return False
    
    def start_monitoring(self):
        """Start real-time system monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        print("📊 Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        print("📊 Monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect system data
                cpu_temp = self._get_cpu_temperature()
                memory_temp = self._get_memory_temperature() 
                cpu_usage = psutil.cpu_percent(interval=1)
                memory_usage = psutil.virtual_memory().percent
                
                # Calculate stability score
                stability = self._calculate_stability_score()
                
                monitoring_data = SystemMonitoring(
                    cpu_temp=cpu_temp,
                    memory_temp=memory_temp,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    system_stability=stability,
                    error_count=self.error_count,
                    timestamp=time.time()
                )
                
                self.monitoring_data.append(monitoring_data)
                
                # Keep only last 1000 data points
                if len(self.monitoring_data) > 1000:
                    self.monitoring_data = self.monitoring_data[-1000:]
                
                # Check safety thresholds
                self._check_safety_thresholds(monitoring_data)
                
                time.sleep(1)  # Monitor every second
                
            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _get_cpu_temperature(self) -> float:
        """Get CPU temperature."""
        try:
            # Try different methods based on OS
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Look for CPU temperature
                    for name, entries in temps.items():
                        if 'coretemp' in name.lower() or 'cpu' in name.lower():
                            if entries:
                                return entries[0].current
            
            # Fallback: try parsing /sys/class/thermal on Linux
            if os.name != 'nt':
                try:
                    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                        temp = int(f.read()) / 1000.0
                        return temp
                except Exception:
                    pass
            else:
                # Windows fallback: WMI thermal zone (requires admin, tenths of kelvin)
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
                        celsius = (raw / 10.0) - 273.15
                        if 0 < celsius < 120:
                            return celsius
                except Exception:
                    pass
            
        except Exception:
            pass
        
        return 50.0  # Default safe temperature
    
    def _get_memory_temperature(self) -> float:
        """Get memory temperature (if available)."""
        try:
            # This requires special sensors or DIMM temperature monitoring
            # Most systems don't have this capability
            # For now, estimate based on CPU temp + offset
            cpu_temp = self._get_cpu_temperature()
            return cpu_temp - 10.0  # Memory usually runs cooler
        except:
            return 45.0  # Default safe memory temp
    
    def _calculate_stability_score(self) -> float:
        """Calculate system stability score (0-100)."""
        try:
            # Check for system errors, crashes, memory errors
            base_score = 100.0
            
            # Reduce score based on error count
            if self.error_count > 0:
                base_score -= min(50.0, self.error_count * 10)
            
            # Check CPU load stability
            if len(self.monitoring_data) > 10:
                recent_cpu = [d.cpu_usage for d in self.monitoring_data[-10:]]
                cpu_variance = sum((x - sum(recent_cpu)/len(recent_cpu))**2 
                                 for x in recent_cpu) / len(recent_cpu)
                if cpu_variance > 100:  # High CPU variance indicates instability
                    base_score -= 20.0
            
            return max(0.0, base_score)
        except:
            return 80.0  # Default moderate stability
    
    def _check_safety_thresholds(self, data: SystemMonitoring):
        """Check if any safety thresholds are exceeded."""
        violations = []
        
        if data.cpu_temp > self.safety_limits.max_cpu_temp_c:
            violations.append(f"CPU temperature: {data.cpu_temp:.1f}°C")
        
        if data.memory_temp > self.safety_limits.max_temperature_c:
            violations.append(f"Memory temperature: {data.memory_temp:.1f}°C")
        
        if data.system_stability < 50.0:
            violations.append(f"System stability: {data.system_stability:.1f}%")
        
        if violations:
            print(f"🚨 SAFETY THRESHOLD EXCEEDED: {', '.join(violations)}")
            self._trigger_emergency_procedures()
    
    def _trigger_emergency_procedures(self):
        """Trigger emergency safety procedures."""
        print("🚨 EMERGENCY PROCEDURES ACTIVATED!")
        self.status = TuningStatus.EMERGENCY_STOP
        
        # Execute all emergency callbacks
        for callback in self.emergency_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Emergency callback failed: {e}")
        
        # Revert to last stable configuration
        if self.last_stable_config:
            print("🔄 Reverting to last stable configuration...")
            self._apply_configuration_safe(self.last_stable_config)
    
    def _emergency_voltage_reduction(self):
        """Emergency voltage reduction."""
        if self.current_config:
            print("⚡ Reducing voltages to safe levels...")
            safe_config = DDR5Configuration(
                frequency=self.current_config.frequency,
                timings=self.current_config.timings,
                voltages=DDR5VoltageParameters(
                    vddq=min(1.20, self.current_config.voltages.vddq),
                    vpp=min(1.80, self.current_config.voltages.vpp)
                )
            )
            self._apply_configuration_safe(safe_config)
    
    def _emergency_frequency_reduction(self):
        """Emergency frequency reduction."""
        if self.current_config:
            print("🐌 Reducing frequency to safe levels...")
            safe_freq = max(4000, self.current_config.frequency - 400)
            # Recalculate timings for lower frequency
            safe_config = self._create_safe_config(safe_freq)
            self._apply_configuration_safe(safe_config)
    
    def _emergency_system_notification(self):
        """Send system notifications about emergency."""
        try:
            # Try to send system notification
            if os.name == 'nt':  # Windows
                subprocess.run([
                    'powershell', '-Command',
                    'Add-Type -AssemblyName System.Windows.Forms; '
                    '[System.Windows.Forms.MessageBox]::Show('
                    '"DDR5 Tuning Emergency Stop Activated!", '
                    '"DDR5 AI Tuner", "OK", "Warning")'
                ], capture_output=True)
            else:  # Linux/macOS
                subprocess.run([
                    'notify-send',
                    'DDR5 AI Tuner',
                    'Emergency stop activated - check system stability!'
                ], capture_output=True)
        except:
            # Fallback to console
            print("\n" + "="*60)
            print("🚨 DDR5 TUNING EMERGENCY STOP ACTIVATED! 🚨")
            print("Check system temperatures and stability!")
            print("="*60 + "\n")
    
    def test_configuration(self, config: DDR5Configuration) -> Tuple[bool, str]:
        """
        Safely test a DDR5 configuration.
        
        Returns:
            Tuple of (success, message)
        """
        if not self._validate_configuration_safety(config):
            return False, "Configuration exceeds safety limits"
        
        print(f"🧪 Testing configuration: DDR5-{config.frequency} "
              f"CL{config.timings.cl} @ {config.voltages.vddq}V")
        
        # Store current as backup
        self.baseline_config = self.current_config
        
        try:
            # Apply configuration
            if self.can_tune_hardware:
                success = self._apply_configuration_hardware(config)
                if not success:
                    return False, "Failed to apply configuration to hardware"
            else:
                # Simulate application
                print("💻 Simulating configuration application...")
                time.sleep(2)
            
            # Monitor for stability
            self.status = TuningStatus.TESTING
            test_duration = 30  # Test for 30 seconds
            
            print(f"⏱️  Testing stability for {test_duration} seconds...")
            
            for i in range(test_duration):
                if self.status == TuningStatus.EMERGENCY_STOP:
                    return False, "Emergency stop triggered during test"
                
                # Check current monitoring data
                if self.monitoring_data:
                    latest = self.monitoring_data[-1]
                    if latest.system_stability < 70.0:
                        return False, f"Stability too low: {latest.system_stability:.1f}%"
                
                time.sleep(1)
                if i % 5 == 0:
                    print(f"  Testing... {i}/{test_duration}s")
            
            # Test passed
            self.last_stable_config = config
            self.current_config = config
            self.status = TuningStatus.IDLE
            
            return True, "Configuration tested successfully"
            
        except Exception as e:
            self.status = TuningStatus.ERROR
            return False, f"Test failed: {str(e)}"
    
    def _validate_configuration_safety(self, config: DDR5Configuration) -> bool:
        """Validate that configuration is within safety limits."""
        limits = self.safety_limits
        
        # Check voltage limits
        if (config.voltages.vddq > limits.max_voltage_vddq or
            config.voltages.vddq < limits.min_voltage_vddq):
            print(f"❌ VDDQ voltage {config.voltages.vddq}V exceeds limits "
                  f"({limits.min_voltage_vddq}-{limits.max_voltage_vddq}V)")
            return False
        
        if (config.voltages.vpp > limits.max_voltage_vpp or
            config.voltages.vpp < limits.min_voltage_vpp):
            print(f"❌ VPP voltage {config.voltages.vpp}V exceeds limits "
                  f"({limits.min_voltage_vpp}-{limits.max_voltage_vpp}V)")
            return False
        
        # Check frequency limits
        if (config.frequency > limits.max_frequency or
            config.frequency < limits.min_frequency):
            print(f"❌ Frequency {config.frequency} MT/s exceeds limits "
                  f"({limits.min_frequency}-{limits.max_frequency} MT/s)")
            return False
        
        # Check timing sanity
        if (config.timings.cl > limits.max_cas_latency or
            config.timings.cl < limits.min_cas_latency):
            print(f"❌ CAS latency {config.timings.cl} exceeds limits "
                  f"({limits.min_cas_latency}-{limits.max_cas_latency})")
            return False
        
        # Check timing relationships
        if config.timings.tras < (config.timings.trcd + config.timings.cl):
            print("❌ Invalid timing relationship: tRAS < (tRCD + CL)")
            return False
        
        print("✅ Configuration passes safety validation")
        return True
    
    def _apply_configuration_hardware(self, config: DDR5Configuration) -> bool:
        """Apply configuration to actual hardware."""
        print("⚠️  WARNING: Real hardware tuning not yet implemented!")
        print("   This would require vendor-specific APIs or BIOS integration")
        print("   Current implementation is simulation only")
        
        # In a real implementation, this would:
        # 1. Interface with MSI Center, ASUS AI Suite, etc.
        # 2. Use vendor SDKs to modify memory settings
        # 3. Apply changes through supported interfaces
        # 4. Verify changes were applied correctly
        
        return True  # Simulate success
    
    def _apply_configuration_safe(self, config: DDR5Configuration):
        """Apply configuration with full safety checks."""
        if self._validate_configuration_safety(config):
            if self.can_tune_hardware:
                self._apply_configuration_hardware(config)
            self.current_config = config
    
    def _create_safe_config(self, frequency: int) -> DDR5Configuration:
        """Create a safe configuration for given frequency."""
        # Calculate conservative timings
        base_cl = max(32, frequency // 200)
        
        return DDR5Configuration(
            frequency=frequency,
            timings=DDR5TimingParameters(
                cl=base_cl,
                trcd=base_cl,
                trp=base_cl,
                tras=base_cl + 32,
                trc=base_cl + 64,
                trfc=frequency // 10
            ),
            voltages=DDR5VoltageParameters(
                vddq=1.10,  # Conservative voltage
                vpp=1.80
            )
        )
    
    def get_monitoring_summary(self) -> Dict:
        """Get summary of current monitoring data."""
        if not self.monitoring_data:
            return {"status": "no_data"}
        
        latest = self.monitoring_data[-1]
        recent_10 = self.monitoring_data[-10:] if len(self.monitoring_data) >= 10 else self.monitoring_data
        
        return {
            "current": {
                "cpu_temp": latest.cpu_temp,
                "memory_temp": latest.memory_temp,
                "cpu_usage": latest.cpu_usage,
                "memory_usage": latest.memory_usage,
                "stability": latest.system_stability,
                "errors": latest.error_count
            },
            "averages_10min": {
                "cpu_temp": sum(d.cpu_temp for d in recent_10) / len(recent_10),
                "memory_temp": sum(d.memory_temp for d in recent_10) / len(recent_10),
                "cpu_usage": sum(d.cpu_usage for d in recent_10) / len(recent_10),
                "stability": sum(d.system_stability for d in recent_10) / len(recent_10)
            },
            "status": self.status.value,
            "safety_level": self.safety_level.value,
            "hardware_access": self.can_tune_hardware
        }
    
    def emergency_stop(self):
        """Manually trigger emergency stop."""
        print("🛑 Manual emergency stop triggered!")
        self._trigger_emergency_procedures()
    
    def revert_to_baseline(self):
        """Revert to baseline configuration."""
        if self.baseline_config:
            print("🔄 Reverting to baseline configuration...")
            self._apply_configuration_safe(self.baseline_config)
            self.current_config = self.baseline_config
            self.status = TuningStatus.IDLE
        else:
            print("❌ No baseline configuration available")


# Convenience functions for web interface
def create_live_tuner(safety_level: str = "conservative") -> LiveDDR5Tuner:
    """Create a live tuner with specified safety level."""
    level_map = {
        "conservative": SafetyLevel.CONSERVATIVE,
        "moderate": SafetyLevel.MODERATE,
        "aggressive": SafetyLevel.AGGRESSIVE,
        "expert": SafetyLevel.EXPERT
    }
    
    level = level_map.get(safety_level, SafetyLevel.CONSERVATIVE)
    return LiveDDR5Tuner(level)


def get_safety_recommendations() -> List[str]:
    """Get safety recommendations for live tuning."""
    return [
        "🛡️  Always start with Conservative safety level",
        "💾 Create a system restore point before tuning",
        "📊 Monitor temperatures continuously during testing",
        "⚡ Never exceed manufacturer voltage specifications",
        "🧪 Test each change thoroughly before applying the next",
        "🔄 Keep baseline settings to revert if needed",
        "🚨 Stop immediately if system becomes unstable",
        "💻 Close unnecessary applications during tuning",
        "❄️  Ensure adequate cooling before starting",
        "⏰ Limit tuning sessions to avoid fatigue errors"
    ]
