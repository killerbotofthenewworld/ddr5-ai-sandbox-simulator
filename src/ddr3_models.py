"""
DDR3 Memory Configuration and Parameter Models

DDR3 JEDEC specifications with proper timing relationships,
voltage ranges, and frequency bins.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
from pydantic import BaseModel, Field, field_validator


@dataclass
class DDR3TimingParameters:
    """DDR3 primary and secondary timing parameters."""

    # Primary timings
    cl: int = 11  # CAS Latency (typical DDR3-1600)
    trcd: int = 11  # RAS to CAS delay
    trp: int = 11  # Row precharge time
    tras: int = 28  # Row active time

    # Secondary timings
    trc: int = 39  # Row cycle time
    trfc: int = 160  # Refresh cycle time (2Gb density)
    trefi: int = 7800  # Refresh interval (ns, 7.8 us)
    twr: int = 12  # Write recovery time
    trtp: int = 6  # Read to precharge
    tcwl: int = 8  # CAS Write Latency

    # Sub-timings
    tfaw: int = 24  # Four bank activate window
    trrd: int = 5  # Row activate to row activate
    twtr: int = 6  # Write to read delay
    tccd: int = 4  # Column to column delay

    def validate_relationships(self) -> List[str]:
        """Validate DDR3 timing relationships and return any violations."""
        violations = []

        if self.tras < (self.trcd + self.cl):
            violations.append(
                f"tRAS ({self.tras}) must be >= tRCD + CL ({self.trcd + self.cl})"
            )

        if self.trc < (self.tras + self.trp):
            violations.append(
                f"tRC ({self.trc}) must be >= tRAS + tRP ({self.tras + self.trp})"
            )

        if self.tcwl > self.cl:
            violations.append(
                f"tCWL ({self.tcwl}) should be <= CL ({self.cl})"
            )

        return violations


@dataclass
class DDR3VoltageParameters:
    """DDR3 voltage parameters."""

    vdd: float = 1.5  # Core voltage (V) – standard DDR3
    vddq: float = 1.5  # I/O voltage (V)
    vtt: float = 0.75  # Termination voltage (V)

    def validate_ranges(self) -> List[str]:
        """Validate voltage ranges and return any violations."""
        violations = []

        if not (1.35 <= self.vdd <= 1.65):
            violations.append(
                f"VDD ({self.vdd}V) must be between 1.35V and 1.65V"
            )

        if not (1.35 <= self.vddq <= 1.65):
            violations.append(
                f"VDDQ ({self.vddq}V) must be between 1.35V and 1.65V"
            )

        if not (0.675 <= self.vtt <= 0.825):
            violations.append(
                f"VTT ({self.vtt}V) must be between 0.675V and 0.825V"
            )

        return violations


@dataclass
class DDR3PerformanceMetrics:
    """Performance metrics for DDR3 memory configurations."""

    memory_bandwidth: float = 0.0  # GB/s
    memory_latency: float = 0.0  # nanoseconds
    stability_score: float = 0.0  # 0-100 scale
    power_consumption: float = 0.0  # watts
    temperature: float = 0.0  # celsius
    signal_integrity: float = 0.0  # 0-100 scale
    thermal_throttling: bool = False
    ecc_enabled: bool = False
    xmp_enabled: bool = False

    def __post_init__(self) -> None:
        """Validate performance metrics after initialization."""
        if self.stability_score < 0 or self.stability_score > 100:
            raise ValueError("Stability score must be between 0 and 100")
        if self.signal_integrity < 0 or self.signal_integrity > 100:
            raise ValueError("Signal integrity must be between 0 and 100")
        if self.memory_bandwidth < 0:
            raise ValueError("Memory bandwidth cannot be negative")
        if self.memory_latency < 0:
            raise ValueError("Memory latency cannot be negative")
        if self.power_consumption < 0:
            raise ValueError("Power consumption cannot be negative")


class DDR3Configuration(BaseModel):
    """Complete DDR3 memory configuration."""

    # Basic specifications
    frequency: int = Field(
        default=1600,
        ge=800,
        le=2133,
        description="Memory frequency in MT/s",
    )
    capacity: int = Field(default=8, description="Capacity per stick in GB")
    rank_count: int = Field(
        default=1, ge=1, le=2, description="Number of ranks per DIMM"
    )
    channel_count: int = Field(
        default=2, description="Number of memory channels"
    )

    # Additional attributes for compatibility
    temperature: float = Field(
        default=55.0, description="Operating temperature in Celsius"
    )

    # Timing and voltage parameters
    timings: DDR3TimingParameters = Field(
        default_factory=DDR3TimingParameters
    )
    voltages: DDR3VoltageParameters = Field(
        default_factory=DDR3VoltageParameters
    )

    # Performance metrics (calculated)
    performance_metrics: DDR3PerformanceMetrics = Field(
        default_factory=DDR3PerformanceMetrics
    )

    @property
    def capacity_gb(self) -> int:
        """Get capacity in GB for compatibility."""
        return self.capacity

    # --- Compatibility proxy properties ---
    @property
    def power_consumption(self) -> float:
        """Total power consumption (watts), proxied from performance_metrics."""
        return self.performance_metrics.power_consumption

    @power_consumption.setter
    def power_consumption(self, value: float) -> None:
        self.performance_metrics.power_consumption = value

    @property
    def signal_integrity(self) -> float:
        """Signal integrity score (0-100), proxied from performance_metrics."""
        return self.performance_metrics.signal_integrity

    @signal_integrity.setter
    def signal_integrity(self, value: float) -> None:
        self.performance_metrics.signal_integrity = value

    @property
    def thermal_throttling(self) -> bool:
        """Thermal throttling flag, proxied from performance_metrics."""
        return self.performance_metrics.thermal_throttling

    @thermal_throttling.setter
    def thermal_throttling(self, value: bool) -> None:
        self.performance_metrics.thermal_throttling = value

    @property
    def ecc_enabled(self) -> bool:
        """ECC enabled flag, proxied from performance_metrics."""
        return self.performance_metrics.ecc_enabled

    @ecc_enabled.setter
    def ecc_enabled(self, value: bool) -> None:
        self.performance_metrics.ecc_enabled = value

    @property
    def xmp_enabled(self) -> bool:
        """XMP enabled flag, proxied from performance_metrics."""
        return self.performance_metrics.xmp_enabled

    @xmp_enabled.setter
    def xmp_enabled(self, value: bool) -> None:
        self.performance_metrics.xmp_enabled = value

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: int) -> int:
        """Ensure frequency is a valid DDR3 speed."""
        valid_speeds = [800, 1066, 1333, 1600, 1866, 2133]
        if v not in valid_speeds:
            closest = min(valid_speeds, key=lambda x: abs(x - v))
            return closest
        return v

    def calculate_performance_metrics(self) -> None:
        """Calculate bandwidth and latency metrics."""
        # Theoretical bandwidth = frequency * 8 bytes * channels / 1000
        # DDR3 uses 64-bit bus per channel
        self.performance_metrics.memory_bandwidth = (
            self.frequency * 8 * self.channel_count
        ) / 1000

        # First word latency = CL / (frequency / 2) * 1000 (convert to ns)
        clock_period_ns = 2000 / self.frequency  # DDR uses double data rate
        self.performance_metrics.memory_latency = (
            self.timings.cl * clock_period_ns
        )

    def validate_configuration(
        self, strict_jedec: bool = False
    ) -> Dict[str, List[str]]:
        """Validate entire configuration and return violations by category."""
        violations = {
            "timing_violations": self.timings.validate_relationships(),
            "voltage_violations": self.voltages.validate_ranges(),
            "general_violations": [],
        }

        # Check frequency vs timing compatibility (only in strict mode)
        if strict_jedec:
            min_cycle_time = 2000 / self.frequency  # ns
            if self.timings.cl * min_cycle_time < 13.125:  # DDR3 min tCL
                violations["general_violations"].append(
                    f"CL too low for frequency {self.frequency} MT/s"
                )

        return violations

    def get_stability_estimate(self) -> float:
        """Estimate configuration stability based on timing margins."""
        violations = self.validate_configuration()
        total_violations = sum(len(v) for v in violations.values())

        margin_score = 100

        # Penalize tight timings
        base_timings = DDR3TimingParameters()
        timing_factors = {
            "cl": (self.timings.cl - base_timings.cl) / base_timings.cl,
            "trcd": (
                self.timings.trcd - base_timings.trcd
            ) / base_timings.trcd,
            "trp": (self.timings.trp - base_timings.trp) / base_timings.trp,
        }

        for factor in timing_factors.values():
            if factor < -0.2:  # More than 20% tighter than JEDEC
                margin_score -= 15
            elif factor < -0.1:  # 10-20% tighter
                margin_score -= 8

        # Penalize high voltages
        if self.voltages.vdd > 1.55:
            margin_score -= 10
        if self.voltages.vddq > 1.55:
            margin_score -= 10

        if total_violations > 0:
            self.performance_metrics.stability_score = max(
                0, 50 - (total_violations * 10)
            )
        else:
            self.performance_metrics.stability_score = max(
                0, min(100, margin_score)
            )

        return self.performance_metrics.stability_score

    def validate_jedec_compliance(self) -> Dict[str, List[str]]:
        """Validate configuration against JEDEC DDR3 standards."""
        violations: Dict[str, List[str]] = {
            "jedec_frequency_violations": [],
            "jedec_timing_violations": [],
            "jedec_voltage_violations": [],
        }
        # JEDEC frequency validation
        jedec_frequencies = [800, 1066, 1333, 1600, 1866, 2133]
        if self.frequency not in jedec_frequencies:
            violations["jedec_frequency_violations"].append(
                f"Frequency {self.frequency} MT/s is not JEDEC standard. "
                f"Valid: {jedec_frequencies}"
            )
        # JEDEC timing validation (DDR3 min tCL ~13.125 ns)
        cycle_time_ns = 2000 / self.frequency
        min_ns = 13.125
        if self.timings.cl * cycle_time_ns < min_ns:
            violations["jedec_timing_violations"].append(
                f"tCL ({self.timings.cl * cycle_time_ns:.2f}ns) "
                f"below JEDEC minimum ({min_ns}ns)"
            )
        if self.timings.trcd * cycle_time_ns < min_ns:
            violations["jedec_timing_violations"].append(
                f"tRCD ({self.timings.trcd * cycle_time_ns:.2f}ns) "
                f"below JEDEC minimum ({min_ns}ns)"
            )
        if self.timings.trp * cycle_time_ns < min_ns:
            violations["jedec_timing_violations"].append(
                f"tRP ({self.timings.trp * cycle_time_ns:.2f}ns) "
                f"below JEDEC minimum ({min_ns}ns)"
            )
        # JEDEC voltage validation
        if not (1.35 <= self.voltages.vdd <= 1.65):
            violations["jedec_voltage_violations"].append(
                f"VDD ({self.voltages.vdd}V) outside JEDEC range "
                "(1.35V - 1.65V)"
            )
        if not (1.35 <= self.voltages.vddq <= 1.65):
            violations["jedec_voltage_violations"].append(
                f"VDDQ ({self.voltages.vddq}V) outside JEDEC range "
                "(1.35V - 1.65V)"
            )
        return violations

    @property
    def bandwidth_gbps(self) -> float:
        """Get theoretical bandwidth in GB/s."""
        if self.performance_metrics.memory_bandwidth == 0:
            self.calculate_performance_metrics()
        return self.performance_metrics.memory_bandwidth

    @property
    def latency_ns(self) -> float:
        """Get first word latency in nanoseconds."""
        if self.performance_metrics.memory_latency == 0:
            self.calculate_performance_metrics()
        return self.performance_metrics.memory_latency

    @property
    def stability_score(self) -> float:
        """Get stability score."""
        return self.performance_metrics.stability_score


def validate_ddr3_configuration(
    config: DDR3Configuration, strict_jedec: bool = False
) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate a DDR3 configuration and return validation results.

    Args:
        config: DDR3Configuration to validate
        strict_jedec: Whether to enforce strict JEDEC compliance

    Returns:
        Tuple of (is_valid, violations_dict)
    """
    violations = config.validate_configuration()

    if strict_jedec:
        jedec_violations = config.validate_jedec_compliance()
        all_violations = {**violations, **jedec_violations}
    else:
        all_violations = violations
        all_violations.update(
            {
                "jedec_frequency_violations": [],
                "jedec_timing_violations": [],
                "jedec_voltage_violations": [],
            }
        )

    is_valid = not any(
        violation_list for violation_list in all_violations.values()
    )

    return is_valid, all_violations
