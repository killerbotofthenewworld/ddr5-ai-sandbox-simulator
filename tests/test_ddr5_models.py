"""
Unit tests for DDR5 models and validation.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))  # noqa: E402

from ddr5_models import (  # noqa: E402
    DDR5Configuration,
    DDR5TimingParameters,
    DDR5VoltageParameters,
    PerformanceMetrics,
    validate_ddr5_configuration,
)


class TestDDR5TimingParameters:
    """Test DDR5 timing parameter validation."""
    
    def test_valid_timings(self):
        """Test valid timing relationships."""
        timings = DDR5TimingParameters(
            cl=32,
            trcd=32,
            trp=32,
            tras=64,  # Updated tRAS to satisfy constraints
            trc=96  # Updated tRC to satisfy constraints
        )
        violations = timings.validate_relationships()
        assert len(violations) == 0
    
    def test_invalid_tras(self):
        """Test invalid tRAS relationship."""
        timings = DDR5TimingParameters(
            cl=32, trcd=32, trp=32, tras=50, trc=84  # tRAS < tRCD + CL
        )
        violations = timings.validate_relationships()
        assert len(violations) > 0
        assert "tRAS" in violations[0]
    
    def test_invalid_trc(self):
        """Test invalid tRC relationship."""
        timings = DDR5TimingParameters(
            cl=32, trcd=32, trp=32, tras=52, trc=80  # tRC < tRAS + tRP
        )
        violations = timings.validate_relationships()
        assert len(violations) > 0
        assert "tRC" in violations[0]


class TestDDR5VoltageParameters:
    """Test DDR5 voltage parameter validation."""
    
    def test_valid_voltages(self):
        """Test valid voltage ranges."""
        voltages = DDR5VoltageParameters(vddq=1.1, vpp=1.8)
        violations = voltages.validate_ranges()
        assert len(violations) == 0
    
    def test_invalid_vddq_low(self):
        """Test VDDQ too low."""
        voltages = DDR5VoltageParameters(vddq=0.9, vpp=1.8)
        violations = voltages.validate_ranges()
        assert len(violations) > 0
        assert "VDDQ" in violations[0]
    
    def test_invalid_vddq_high(self):
        """Test VDDQ too high."""
        voltages = DDR5VoltageParameters(vddq=1.3, vpp=1.8)
        violations = voltages.validate_ranges()
        assert len(violations) > 0
        assert "VDDQ" in violations[0]
    
    def test_invalid_vpp(self):
        """Test VPP out of range."""
        voltages = DDR5VoltageParameters(vddq=1.1, vpp=2.0)
        violations = voltages.validate_ranges()
        assert len(violations) > 0
        assert "VPP" in violations[0]


class TestDDR5Configuration:
    """Test complete DDR5 configuration."""
    
    def test_valid_configuration(self):
        """Test a valid DDR5 configuration."""
        config = DDR5Configuration(frequency=5600)
        config.calculate_performance_metrics()
        
        assert config.bandwidth_gbps is not None
        assert config.latency_ns is not None
        assert config.bandwidth_gbps > 0
        assert config.latency_ns > 0
    
    def test_frequency_validation(self):
        """Test frequency validation and rounding."""
        config = DDR5Configuration(frequency=5555)  # Invalid frequency
        # Should be rounded to nearest valid frequency
        assert config.frequency in [5200, 5600]
    
    def test_stability_estimate(self):
        """Test stability estimation."""
        config = DDR5Configuration(frequency=5600)
        stability = config.get_stability_estimate()
        
        assert 0 <= stability <= 100
        assert config.stability_score == stability
    
    def test_performance_calculation(self):
        """Test performance metric calculation."""
        config = DDR5Configuration(frequency=5600)
        config.calculate_performance_metrics()
        
        # Check bandwidth calculation
        expected_bandwidth = (5600 * 8 * 2) / 1000
        assert abs(config.bandwidth_gbps - expected_bandwidth) < 0.1
        
        # Check latency calculation
        clock_period = 2000 / 5600
        expected_latency = config.timings.cl * clock_period
        assert abs(config.latency_ns - expected_latency) < 0.1

    def test_lazy_metric_properties_compute_when_zero(self):
        """bandwidth_gbps/latency_ns should compute when internal metrics are zero."""
        config = DDR5Configuration(frequency=5200)
        # Ensure defaults are zero before property access
        assert config.performance_metrics.memory_bandwidth == 0
        assert config.performance_metrics.memory_latency == 0
        # Access properties triggers calculation
        bw = config.bandwidth_gbps
        lat = config.latency_ns
        assert bw > 0
        assert lat > 0

    def test_validate_configuration_strict_jedec_general_violation(self):
        """Strict JEDEC should add general violations when CL too low for frequency."""
        # Default CL=32 at high freq (e.g., 5600) yields < 13.75ns -> violation
        config = DDR5Configuration(frequency=5600)
        violations = config.validate_configuration(strict_jedec=True)
        assert any(
            "CL too low" in v for v in violations["general_violations"]
        )  # type: ignore[index]

    def test_validate_jedec_frequency_violation(self):
        """A non-JEDEC frequency should report frequency violation."""
        config = DDR5Configuration(frequency=5600)
        # Manually set a non-JEDEC frequency to bypass field validation
        config.frequency = 5000
        jedec = config.validate_jedec_compliance()
        assert len(jedec["jedec_frequency_violations"]) > 0  # type: ignore[index]


class TestDDR5Voltages:
    def test_vtt_property(self):
        volts = DDR5VoltageParameters(vddq=1.2, vpp=1.8)
        assert volts.vtt == 0.6


class TestPerformanceMetricsValidation:
    def test_negative_values_raise(self):
        with pytest.raises(ValueError):
            PerformanceMetrics(memory_bandwidth=-1.0)
        with pytest.raises(ValueError):
            PerformanceMetrics(memory_latency=-0.1)
        with pytest.raises(ValueError):
            PerformanceMetrics(power_consumption=-5.0)
        with pytest.raises(ValueError):
            PerformanceMetrics(stability_score=150)
        with pytest.raises(ValueError):
            PerformanceMetrics(signal_integrity=101)


class TestTopLevelValidation:
    def test_validate_ddr5_configuration_non_strict_includes_empty_jedec_lists(self):
        config = DDR5Configuration(frequency=5600)
        ok, details = validate_ddr5_configuration(config, strict_jedec=False)
        assert isinstance(ok, bool)
        # JEDEC lists should be present and empty in non-strict mode
        assert "jedec_frequency_violations" in details
        assert details["jedec_frequency_violations"] == []


if __name__ == "__main__":
    pytest.main([__file__])
