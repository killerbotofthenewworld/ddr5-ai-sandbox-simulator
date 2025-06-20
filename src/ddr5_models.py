"""
DDR5 Memory Configuration and Parameter Models
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator


@dataclass
class DDR5TimingParameters:
    """DDR5 primary and secondary timing parameters."""
    
    # Primary timings
    cl: int = 32  # CAS Latency
    trcd: int = 32  # RAS to CAS delay
    trp: int = 32  # Row precharge time
    tras: int = 64  # Row active time (updated to satisfy tRAS >= tRCD + CL)
    
    # Secondary timings
    trc: int = 96  # Row cycle time (updated to satisfy tRC >= tRAS + tRP)
    trfc: int = 295  # Refresh cycle time
    trefi: int = 3904  # Refresh interval
    twr: int = 24  # Write recovery time
    trtp: int = 12  # Read to precharge
    tcwl: int = 31  # CAS Write Latency (updated to satisfy tCWL >= CL - 1)
    
    # Sub-timings
    tfaw: int = 16  # Four bank activate window
    trrd_s: int = 4  # Row activate to row activate (same bank group)
    trrd_l: int = 6  # Row activate to row activate (different bank group)
    twtr_s: int = 3  # Write to read (same bank group)
    twtr_l: int = 9  # Write to read (different bank group)
    tccd_l: int = 5  # Column to column delay (different bank group)
    trrds: int = 4  # Alias for trrd_s for compatibility
    trrdl: int = 6  # Alias for trrd_l for compatibility
    
    def validate_relationships(self) -> List[str]:
        """Validate DDR5 timing relationships and return any violations."""
        violations = []
        
        if self.tras < (self.trcd + self.cl):
            violations.append(f"tRAS ({self.tras}) must be >= tRCD + CL ({self.trcd + self.cl})")
        
        if self.trc < (self.tras + self.trp):
            violations.append(f"tRC ({self.trc}) must be >= tRAS + tRP ({self.tras + self.trp})")
        
        if self.tcwl < (self.cl - 1):
            violations.append(f"tCWL ({self.tcwl}) should be >= CL - 1 ({self.cl - 1})")
        
        return violations


@dataclass
class DDR5VoltageParameters:
    """DDR5 voltage parameters."""
    
    vddq: float = 1.1  # Core voltage (V)
    vpp: float = 1.8   # Wordline boost voltage (V)
    vddq_tx: float = 1.1  # TX voltage (V)
    vddq_rx: float = 1.1  # RX voltage (V)
    
    def validate_ranges(self) -> List[str]:
        """Validate voltage ranges and return any violations."""
        violations = []
        
        if not (1.0 <= self.vddq <= 1.2):
            violations.append(f"VDDQ ({self.vddq}V) must be between 1.0V and 1.2V")
        
        if not (1.7 <= self.vpp <= 1.9):
            violations.append(f"VPP ({self.vpp}V) must be between 1.7V and 1.9V")
        
        return violations


class DDR5Configuration(BaseModel):
    """Complete DDR5 memory configuration."""
    
    # Basic specifications
    frequency: int = Field(default=5600, ge=4000, le=8400, description="Memory frequency in MT/s")
    capacity: int = Field(default=16, description="Capacity per stick in GB")
    rank_count: int = Field(default=1, ge=1, le=2, description="Number of ranks per DIMM")
    
    # Timing and voltage parameters
    timings: DDR5TimingParameters = Field(default_factory=DDR5TimingParameters)
    voltages: DDR5VoltageParameters = Field(default_factory=DDR5VoltageParameters)
    
    # Performance metrics (calculated)
    bandwidth_gbps: Optional[float] = Field(default=None, description="Theoretical bandwidth in GB/s")
    latency_ns: Optional[float] = Field(default=None, description="First word latency in ns")
    stability_score: Optional[float] = Field(default=None, ge=0, le=100, description="Stability score (0-100)")
    
    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v):
        """Ensure frequency is a valid DDR5 speed."""
        valid_speeds = [
            3200, 3600, 4000, 4400, 4800, 5200, 5600, 6000,
            6400, 6800, 7200, 7600, 8000, 8400
        ]
        if v not in valid_speeds:
            closest = min(valid_speeds, key=lambda x: abs(x - v))
            return closest
        return v
    
    def calculate_performance_metrics(self) -> None:
        """Calculate bandwidth and latency metrics."""
        # Theoretical bandwidth = frequency * 8 bytes * 2 channels / 1000
        self.bandwidth_gbps = (self.frequency * 8 * 2) / 1000
        
        # First word latency = CL / (frequency / 2) * 1000 (convert to ns)
        clock_period_ns = 2000 / self.frequency  # DDR uses double data rate
        self.latency_ns = self.timings.cl * clock_period_ns
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """Validate entire configuration and return violations by category."""
        violations = {
            'timing_violations': self.timings.validate_relationships(),
            'voltage_violations': self.voltages.validate_ranges(),
            'general_violations': []
        }
        
        # Check frequency vs timing compatibility
        min_cycle_time = 2000 / self.frequency  # ns
        if self.timings.cl * min_cycle_time < 13.75:  # DDR5 minimum tCL
            violations['general_violations'].append(
                f"CL too low for frequency {self.frequency} MT/s"
            )
        
        return violations
    
    def get_stability_estimate(self) -> float:
        """Estimate configuration stability based on timing margins."""
        violations = self.validate_configuration()
        total_violations = sum(len(v) for v in violations.values())
        
        # Calculate margin_score before assigning stability_score
        margin_score = 100
        
        # Penalize tight timings
        base_timings = DDR5TimingParameters()
        timing_factors = {
            'cl': (self.timings.cl - base_timings.cl) / base_timings.cl,
            'trcd': (
                self.timings.trcd - base_timings.trcd
            ) / base_timings.trcd,
            'trp': (self.timings.trp - base_timings.trp) / base_timings.trp,
        }

        for factor in timing_factors.values():
            if factor < -0.2:  # More than 20% tighter than JEDEC
                margin_score -= 15
            elif factor < -0.1:  # 10-20% tighter
                margin_score -= 8

        # Penalize high voltages
        if self.voltages.vddq > 1.15:
            margin_score -= 10
        if self.voltages.vpp > 1.85:
            margin_score -= 10

        # Ensure stability_score is always set
        if total_violations > 0:
            self.stability_score = max(0, 50 - (total_violations * 10))
        else:
            self.stability_score = max(0, min(100, margin_score))
        
        return self.stability_score
    
    def validate_jedec_compliance(self) -> Dict[str, List[str]]:
        """Validate configuration against JEDEC DDR5 standards."""
        violations = {
            'jedec_frequency_violations': [],
            'jedec_timing_violations': [],
            'jedec_voltage_violations': []
        }
        # JEDEC frequency validation
        jedec_frequencies = [4000, 4400, 4800, 5200, 5600, 6000, 6400, 6800, 7200, 7600, 8000, 8400]
        if self.frequency not in jedec_frequencies:
            violations['jedec_frequency_violations'].append(
                f"Frequency {self.frequency} MT/s is not JEDEC standard. Valid: {jedec_frequencies}")
        # JEDEC timing validation (example: tCL, tRCD, tRP >= 13.75ns)
        cycle_time_ns = 2000 / self.frequency
        min_ns = 13.75
        if self.timings.cl * cycle_time_ns < min_ns:
            violations['jedec_timing_violations'].append(
                f"tCL ({self.timings.cl * cycle_time_ns:.2f}ns) below JEDEC minimum ({min_ns}ns)")
        if self.timings.trcd * cycle_time_ns < min_ns:
            violations['jedec_timing_violations'].append(
                f"tRCD ({self.timings.trcd * cycle_time_ns:.2f}ns) below JEDEC minimum ({min_ns}ns)")
        if self.timings.trp * cycle_time_ns < min_ns:
            violations['jedec_timing_violations'].append(
                f"tRP ({self.timings.trp * cycle_time_ns:.2f}ns) below JEDEC minimum ({min_ns}ns)")
        # JEDEC voltage validation
        if not (1.0 <= self.voltages.vddq <= 1.2):
            violations['jedec_voltage_violations'].append(
                f"VDDQ ({self.voltages.vddq}V) outside JEDEC range (1.0V - 1.2V)")
        if not (1.7 <= self.voltages.vpp <= 1.9):
            violations['jedec_voltage_violations'].append(
                f"VPP ({self.voltages.vpp}V) outside JEDEC range (1.7V - 1.9V)")
        return violations
