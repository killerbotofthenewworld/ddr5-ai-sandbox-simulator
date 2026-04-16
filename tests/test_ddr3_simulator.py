"""
Tests for DDR3 Simulator
"""

import pytest
from src.ddr3_models import (
    DDR3Configuration,
    DDR3TimingParameters,
    DDR3VoltageParameters,
)
from src.ddr3_simulator import DDR3Simulator


def make_config(
    freq: int = 1600,
    cl: int = 11,
    trcd: int = 11,
    trp: int = 11,
    tras: int = 28,
    trc: int = 39,
    vdd: float = 1.5,
) -> DDR3Configuration:
    """Helper factory for DDR3 test configurations."""
    return DDR3Configuration(
        frequency=freq,
        timings=DDR3TimingParameters(
            cl=cl, trcd=trcd, trp=trp, tras=tras, trc=trc
        ),
        voltages=DDR3VoltageParameters(vdd=vdd, vddq=vdd, vtt=vdd / 2),
    )


class TestDDR3Simulator:
    """Tests for DDR3Simulator class."""

    def test_simulator_initialization(self):
        sim = DDR3Simulator()
        assert sim.current_config is not None
        assert sim.simulation_cache == {}

    def test_load_configuration(self):
        sim = DDR3Simulator()
        config = make_config(freq=1333)
        sim.load_configuration(config)
        assert sim.current_config.frequency == 1333
        assert sim.simulation_cache == {}

    def test_simulate_bandwidth_sequential(self):
        sim = DDR3Simulator()
        sim.load_configuration(make_config())
        result = sim.simulate_bandwidth("sequential")
        assert "theoretical_bandwidth_gbps" in result
        assert "effective_bandwidth_gbps" in result
        assert result["effective_bandwidth_gbps"] > 0

    def test_simulate_bandwidth_random(self):
        sim = DDR3Simulator()
        sim.load_configuration(make_config())
        seq = sim.simulate_bandwidth("sequential")
        rand = sim.simulate_bandwidth("random")
        assert (
            rand["effective_bandwidth_gbps"]
            < seq["effective_bandwidth_gbps"]
        )

    def test_simulate_latency(self):
        sim = DDR3Simulator()
        sim.load_configuration(make_config())
        result = sim.simulate_latency("random")
        assert "base_latency_ns" in result
        assert "effective_latency_ns" in result
        assert result["effective_latency_ns"] > 0

    def test_simulate_power_consumption(self):
        sim = DDR3Simulator()
        sim.load_configuration(make_config())
        result = sim.simulate_power_consumption()
        assert "total_power_w" in result
        assert result["total_power_w"] > 0

    def test_run_stability_test(self):
        sim = DDR3Simulator()
        sim.load_configuration(make_config())
        result = sim.run_stability_test()
        assert "test_result" in result
        assert result["test_result"] in [
            "EXCELLENT",
            "STABLE",
            "MARGINAL",
            "UNSTABLE",
            "FAILED",
        ]

    def test_simulate_performance(self):
        sim = DDR3Simulator()
        config = make_config()
        result = sim.simulate_performance(config)
        assert "score" in result
        assert "bandwidth" in result
        assert "latency" in result
        assert "power" in result
        assert "stability" in result

    def test_predict_stability(self):
        sim = DDR3Simulator()
        config = make_config()
        score = sim.predict_stability(config)
        assert 0.0 <= score <= 1.0

    def test_estimate_power(self):
        sim = DDR3Simulator()
        config = make_config()
        power = sim.estimate_power(config)
        assert power > 0


class TestDDR3SimulatorCaching:
    """Tests for simulator caching behavior."""

    def test_bandwidth_cache(self):
        sim = DDR3Simulator()
        sim.load_configuration(make_config())
        r1 = sim.simulate_bandwidth("sequential")
        r2 = sim.simulate_bandwidth("sequential")
        assert r1 is r2  # Same cached object

    def test_power_cache(self):
        sim = DDR3Simulator()
        sim.load_configuration(make_config())
        r1 = sim.simulate_power_consumption()
        r2 = sim.simulate_power_consumption()
        assert r1 is r2

    def test_cache_cleared_on_load(self):
        sim = DDR3Simulator()
        sim.load_configuration(make_config())
        sim.simulate_bandwidth("sequential")
        assert len(sim.simulation_cache) > 0
        sim.load_configuration(make_config(freq=1333))
        assert len(sim.simulation_cache) == 0

    def test_bandwidth_cache_key_includes_frequency(self):
        sim = DDR3Simulator()
        sim.load_configuration(make_config(freq=1600))
        r1 = sim.simulate_bandwidth("sequential")
        sim.simulation_cache.clear()
        sim.current_config = make_config(freq=1333)
        sim.current_config.calculate_performance_metrics()
        r2 = sim.simulate_bandwidth("sequential")
        assert r1["theoretical_bandwidth_gbps"] != pytest.approx(
            r2["theoretical_bandwidth_gbps"]
        )


class TestDDR3SimulatorEdgeCases:
    """Edge case tests for DDR3 simulator."""

    def test_command_overhead_increases_with_frequency(self):
        sim = DDR3Simulator()
        base_over = sim._calculate_command_overhead()
        sim.current_config = make_config(freq=2133)
        high_over = sim._calculate_command_overhead()
        assert high_over > base_over

    def test_estimate_power_does_not_mutate_current_config(self):
        sim = DDR3Simulator()
        original = make_config(freq=1600)
        sim.load_configuration(original)
        other = make_config(freq=1333)
        sim.estimate_power(other)
        assert sim.current_config.frequency == 1600

    def test_higher_frequency_higher_bandwidth(self):
        sim = DDR3Simulator()
        sim.load_configuration(make_config(freq=1333))
        bw_low = sim.simulate_bandwidth("sequential")
        sim.load_configuration(make_config(freq=2133))
        bw_high = sim.simulate_bandwidth("sequential")
        assert (
            bw_high["effective_bandwidth_gbps"]
            > bw_low["effective_bandwidth_gbps"]
        )
