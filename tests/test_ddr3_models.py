"""
Tests for DDR3 Memory Models
"""

import pytest
from src.ddr3_models import (
    DDR3TimingParameters,
    DDR3VoltageParameters,
    DDR3PerformanceMetrics,
    DDR3Configuration,
    validate_ddr3_configuration,
)


class TestDDR3TimingParameters:
    """Tests for DDR3TimingParameters dataclass."""

    def test_valid_timings(self):
        timings = DDR3TimingParameters(
            cl=11, trcd=11, trp=11, tras=28, trc=39
        )
        violations = timings.validate_relationships()
        assert len(violations) == 0

    def test_invalid_tras(self):
        timings = DDR3TimingParameters(
            cl=11, trcd=11, trp=11, tras=15, trc=39
        )
        violations = timings.validate_relationships()
        assert any("tRAS" in v for v in violations)

    def test_invalid_trc(self):
        timings = DDR3TimingParameters(
            cl=11, trcd=11, trp=11, tras=28, trc=30
        )
        violations = timings.validate_relationships()
        assert any("tRC" in v for v in violations)

    def test_invalid_tcwl(self):
        timings = DDR3TimingParameters(cl=9, tcwl=12)
        violations = timings.validate_relationships()
        assert any("tCWL" in v for v in violations)

    def test_default_timings_are_valid(self):
        timings = DDR3TimingParameters()
        violations = timings.validate_relationships()
        assert len(violations) == 0


class TestDDR3VoltageParameters:
    """Tests for DDR3VoltageParameters dataclass."""

    def test_valid_voltages(self):
        voltages = DDR3VoltageParameters(vdd=1.5, vddq=1.5, vtt=0.75)
        violations = voltages.validate_ranges()
        assert len(violations) == 0

    def test_ddr3l_voltages(self):
        """DDR3L operates at 1.35V."""
        voltages = DDR3VoltageParameters(vdd=1.35, vddq=1.35, vtt=0.675)
        violations = voltages.validate_ranges()
        assert len(violations) == 0

    def test_invalid_vdd_low(self):
        voltages = DDR3VoltageParameters(vdd=1.2)
        violations = voltages.validate_ranges()
        assert any("VDD" in v for v in violations)

    def test_invalid_vdd_high(self):
        voltages = DDR3VoltageParameters(vdd=1.7)
        violations = voltages.validate_ranges()
        assert any("VDD" in v for v in violations)

    def test_invalid_vtt(self):
        voltages = DDR3VoltageParameters(vtt=1.0)
        violations = voltages.validate_ranges()
        assert any("VTT" in v for v in violations)


class TestDDR3PerformanceMetrics:
    """Tests for DDR3PerformanceMetrics dataclass."""

    def test_valid_metrics(self):
        metrics = DDR3PerformanceMetrics(
            memory_bandwidth=12.8,
            memory_latency=13.75,
            stability_score=85.0,
        )
        assert metrics.memory_bandwidth == 12.8

    def test_negative_bandwidth_raises(self):
        with pytest.raises(ValueError):
            DDR3PerformanceMetrics(memory_bandwidth=-1.0)

    def test_negative_latency_raises(self):
        with pytest.raises(ValueError):
            DDR3PerformanceMetrics(memory_latency=-1.0)

    def test_stability_out_of_range(self):
        with pytest.raises(ValueError):
            DDR3PerformanceMetrics(stability_score=101.0)


class TestDDR3Configuration:
    """Tests for DDR3Configuration Pydantic model."""

    def test_valid_configuration(self):
        config = DDR3Configuration(frequency=1600)
        assert config.frequency == 1600

    def test_frequency_validation(self):
        config = DDR3Configuration(frequency=1500)
        assert config.frequency in [800, 1066, 1333, 1600, 1866, 2133]

    def test_frequency_snap_to_nearest(self):
        config = DDR3Configuration(frequency=1700)
        assert config.frequency == 1600

    def test_stability_estimate(self):
        config = DDR3Configuration()
        score = config.get_stability_estimate()
        assert 0 <= score <= 100

    def test_performance_calculation(self):
        config = DDR3Configuration(frequency=1600)
        config.calculate_performance_metrics()
        assert config.performance_metrics.memory_bandwidth > 0
        assert config.performance_metrics.memory_latency > 0

    def test_lazy_metric_properties_compute_when_zero(self):
        config = DDR3Configuration(frequency=1600)
        bw = config.bandwidth_gbps
        lat = config.latency_ns
        assert bw > 0
        assert lat > 0

    def test_validate_configuration_basic(self):
        config = DDR3Configuration()
        violations = config.validate_configuration()
        assert "timing_violations" in violations
        assert "voltage_violations" in violations

    def test_validate_jedec_frequency_violation(self):
        config = DDR3Configuration.__new__(DDR3Configuration)
        # Manually set a non-JEDEC frequency via __dict__
        object.__setattr__(config, "__dict__", {
            "frequency": 999,
            "capacity": 8,
            "rank_count": 1,
            "channel_count": 2,
            "temperature": 55.0,
            "timings": DDR3TimingParameters(),
            "voltages": DDR3VoltageParameters(),
            "performance_metrics": DDR3PerformanceMetrics(),
        })
        object.__setattr__(config, "__pydantic_fields_set__", set())
        violations = config.validate_jedec_compliance()
        assert len(violations["jedec_frequency_violations"]) > 0

    def test_capacity_gb_property(self):
        config = DDR3Configuration(capacity=4)
        assert config.capacity_gb == 4

    def test_proxy_properties(self):
        config = DDR3Configuration()
        config.power_consumption = 5.0
        assert config.performance_metrics.power_consumption == 5.0
        config.signal_integrity = 90.0
        assert config.performance_metrics.signal_integrity == 90.0
        config.thermal_throttling = True
        assert config.performance_metrics.thermal_throttling is True
        config.ecc_enabled = True
        assert config.performance_metrics.ecc_enabled is True
        config.xmp_enabled = True
        assert config.performance_metrics.xmp_enabled is True


class TestDDR3Validation:
    """Tests for the validate_ddr3_configuration function."""

    def test_valid_config_non_strict(self):
        config = DDR3Configuration()
        is_valid, violations = validate_ddr3_configuration(config)
        assert is_valid is True

    def test_valid_config_strict(self):
        config = DDR3Configuration(frequency=1600)
        is_valid, violations = validate_ddr3_configuration(
            config, strict_jedec=True
        )
        assert "jedec_frequency_violations" in violations
        assert "jedec_timing_violations" in violations
        assert "jedec_voltage_violations" in violations

    def test_non_strict_includes_empty_jedec_lists(self):
        config = DDR3Configuration()
        _, violations = validate_ddr3_configuration(config)
        assert violations["jedec_frequency_violations"] == []
        assert violations["jedec_timing_violations"] == []
        assert violations["jedec_voltage_violations"] == []
