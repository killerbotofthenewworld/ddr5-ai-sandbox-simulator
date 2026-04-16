"""
DDR3 Memory Simulator
Core simulation engine for DDR3 memory behavior and performance.
"""

from typing import Dict, List, Any

try:
    from .ddr3_models import DDR3Configuration, DDR3TimingParameters
except ImportError:
    from src.ddr3_models import DDR3Configuration, DDR3TimingParameters


class DDR3Simulator:
    """DDR3 memory behavior simulator."""

    def __init__(self) -> None:
        """Initialize the DDR3 simulator."""
        self.current_config = DDR3Configuration()
        self.simulation_cache: Dict[str, Any] = {}

        # Performance coefficients (derived from empirical DDR3 data)
        self.performance_coefficients = {
            "bandwidth_efficiency": 0.80,  # Real vs theoretical bandwidth
            "latency_penalty": 1.20,  # Additional latency factors
            "power_coefficient": 0.018,  # Power per MHz per volt
            "thermal_coefficient": 0.010,  # Temperature rise per watt
        }

    def load_configuration(self, config: DDR3Configuration) -> None:
        """Load a DDR3 configuration for simulation."""
        self.current_config = config
        self.current_config.calculate_performance_metrics()
        self.simulation_cache.clear()

    def simulate_bandwidth(
        self,
        access_pattern: str = "sequential",
        queue_depth: int = 16,
    ) -> Dict[str, float]:
        """
        Simulate memory bandwidth under different access patterns.

        Args:
            access_pattern: "sequential", "random", "mixed"
            queue_depth: Command queue depth

        Returns:
            Dictionary with bandwidth metrics
        """
        freq = self.current_config.frequency
        cache_key = f"bandwidth_{access_pattern}_{queue_depth}_{freq}"
        if cache_key in self.simulation_cache:
            return self.simulation_cache[cache_key]

        base_bandwidth = self.current_config.bandwidth_gbps

        efficiency = self.performance_coefficients["bandwidth_efficiency"]

        # Access pattern efficiency
        pattern_efficiency = {
            "sequential": 0.92,
            "random": 0.55,
            "mixed": 0.70,
        }

        # Queue depth impact (DDR3 has smaller queue depth benefit)
        queue_efficiency = min(1.0, 0.6 + (queue_depth / 32) * 0.4)

        # Timing impact
        timing_efficiency = self._calculate_timing_efficiency()

        effective_bandwidth = (
            base_bandwidth
            * efficiency
            * pattern_efficiency[access_pattern]
            * queue_efficiency
            * timing_efficiency
        )

        result = {
            "theoretical_bandwidth_gbps": base_bandwidth,
            "effective_bandwidth_gbps": effective_bandwidth,
            "efficiency_percent": (effective_bandwidth / base_bandwidth) * 100,
            "access_pattern": access_pattern,
            "queue_depth": queue_depth,
        }

        self.simulation_cache[cache_key] = result
        return result

    def simulate_latency(
        self,
        access_pattern: str = "random",
        bank_conflicts: bool = True,
    ) -> Dict[str, float]:
        """
        Simulate memory latency characteristics.

        Args:
            access_pattern: "random", "sequential", "worst_case"
            bank_conflicts: Whether to simulate bank conflicts

        Returns:
            Dictionary with latency metrics
        """
        cache_key = f"latency_{access_pattern}_{bank_conflicts}"
        if cache_key in self.simulation_cache:
            return self.simulation_cache[cache_key]

        base_latency = self.current_config.latency_ns

        # Access pattern impact
        pattern_penalty = {
            "sequential": 1.0,
            "random": 1.3,
            "worst_case": 1.6,
        }

        # Bank conflict penalty (DDR3 has 8 banks)
        conflict_penalty = 1.4 if bank_conflicts else 1.0

        # Command overhead
        command_overhead = self._calculate_command_overhead()

        effective_latency = (
            base_latency
            * pattern_penalty[access_pattern]
            * conflict_penalty
            + command_overhead
        )

        result = {
            "base_latency_ns": base_latency,
            "effective_latency_ns": effective_latency,
            "overhead_ns": command_overhead,
            "access_pattern": access_pattern,
            "bank_conflicts_enabled": bank_conflicts,
        }

        self.simulation_cache[cache_key] = result
        return result

    def simulate_power_consumption(self) -> Dict[str, float]:
        """
        Simulate power consumption based on configuration.

        Returns:
            Dictionary with power metrics
        """
        cache_key = "power_consumption"
        if cache_key in self.simulation_cache:
            return self.simulation_cache[cache_key]

        frequency_mhz = self.current_config.frequency
        vdd = self.current_config.voltages.vdd

        # Dynamic power (frequency and voltage dependent)
        dynamic_power = (
            frequency_mhz
            * self.performance_coefficients["power_coefficient"]
            * (vdd**2)
        )

        # Static power (voltage dependent) – DDR3 draws more static power
        static_power = 300 + (vdd - 1.5) * 800

        # Additional power for higher frequencies
        if frequency_mhz > 1600:
            frequency_penalty = (frequency_mhz - 1600) * 0.15
            dynamic_power += frequency_penalty

        total_power = dynamic_power + static_power

        bandwidth_gbps = self.current_config.bandwidth_gbps

        result = {
            "dynamic_power_mw": dynamic_power,
            "static_power_mw": static_power,
            "total_power_mw": total_power,
            "total_power_w": total_power / 1000,
            "power_efficiency_mb_per_mw": (bandwidth_gbps * 1000)
            / total_power,
        }

        self.simulation_cache[cache_key] = result
        return result

    def run_stability_test(
        self,
        test_duration_minutes: int = 30,
        stress_level: str = "medium",
    ) -> Dict[str, Any]:
        """
        Simulate memory stability testing.

        Args:
            test_duration_minutes: Duration of stability test
            stress_level: "light", "medium", "heavy", "extreme"

        Returns:
            Dictionary with stability test results
        """
        config_violations = self.current_config.validate_configuration()
        stability_score = self.current_config.get_stability_estimate()

        # Stress level impact
        stress_factors = {
            "light": 0.9,
            "medium": 1.0,
            "heavy": 1.2,
            "extreme": 1.5,
        }

        stress_factor = stress_factors[stress_level]
        adjusted_stability = stability_score / stress_factor

        # Duration impact
        duration_factor = 1.0 - (test_duration_minutes / 1000)
        final_stability = adjusted_stability * duration_factor

        # Determine test result
        if final_stability >= 90:
            test_result = "EXCELLENT"
            error_rate = 0.0
        elif final_stability >= 75:
            test_result = "STABLE"
            error_rate = 0.001
        elif final_stability >= 60:
            test_result = "MARGINAL"
            error_rate = 0.01
        elif final_stability >= 40:
            test_result = "UNSTABLE"
            error_rate = 0.1
        else:
            test_result = "FAILED"
            error_rate = 1.0

        return {
            "test_result": test_result,
            "stability_score": final_stability,
            "error_rate": error_rate,
            "violations": config_violations,
            "test_duration_minutes": test_duration_minutes,
            "stress_level": stress_level,
            "recommendation": self._get_stability_recommendation(
                final_stability, config_violations
            ),
        }

    def simulate_performance(
        self,
        config: DDR3Configuration = None,
        temperature: float = 25.0,
    ) -> Dict[str, Any]:
        """
        Comprehensive performance simulation for a DDR3 configuration.

        Args:
            config: DDR3 configuration to simulate (uses current if None)
            temperature: Ambient temperature in Celsius

        Returns:
            Dictionary with comprehensive performance metrics
        """
        if config:
            old_config = self.current_config
            self.current_config = config
            self.current_config.calculate_performance_metrics()

        try:
            # Adjust configuration for temperature
            thermal_coeff = self.performance_coefficients[
                "thermal_coefficient"
            ]
            self.current_config.voltages.vdd -= temperature * thermal_coeff
            self.current_config.voltages.vddq -= temperature * thermal_coeff

            # Run various simulations
            bandwidth_results = self.simulate_bandwidth("mixed")
            latency_results = self.simulate_latency("random")
            power_results = self.simulate_power_consumption()
            stability_results = self.run_stability_test()

            # Calculate overall performance score
            performance_score = (
                (bandwidth_results["effective_bandwidth_gbps"] / 50.0) * 40
                + (100.0 / latency_results["effective_latency_ns"]) * 30
                + (100.0 - power_results["total_power_w"]) * 15
                + stability_results["stability_score"] * 15
            )

            bw_gbps = bandwidth_results["effective_bandwidth_gbps"]
            bandwidth_mbps = bw_gbps * 1000
            power_mw = power_results["total_power_w"] * 1000

            return {
                "score": min(100.0, max(0.0, performance_score)),
                "bandwidth": bandwidth_mbps,
                "latency": latency_results["effective_latency_ns"],
                "power": power_mw,
                "stability": stability_results["stability_score"],
                "detailed_bandwidth": bandwidth_results,
                "detailed_latency": latency_results,
                "detailed_power": power_results,
                "detailed_stability": stability_results,
                "config": config or self.current_config,
            }

        finally:
            if config:
                self.current_config = old_config

    def predict_stability(self, config: DDR3Configuration) -> float:
        """Predict configuration stability as a single score.

        Args:
            config: DDR3 configuration to analyze

        Returns:
            Stability score between 0.0 and 1.0
        """
        return config.get_stability_estimate() / 100.0

    def estimate_power(self, config: DDR3Configuration) -> float:
        """Estimate power consumption in watts.

        Args:
            config: DDR3 configuration to analyze

        Returns:
            Power consumption in watts
        """
        original_config = self.current_config
        self.current_config = config
        try:
            power_result = self.simulate_power_consumption()
            return power_result["total_power_w"]
        finally:
            self.current_config = original_config

    def _calculate_timing_efficiency(self) -> float:
        """Calculate efficiency based on timing parameters."""
        timings = self.current_config.timings
        baseline = DDR3TimingParameters()

        cl_ratio = timings.cl / baseline.cl
        trcd_ratio = timings.trcd / baseline.trcd
        trp_ratio = timings.trp / baseline.trp

        avg_ratio = (cl_ratio + trcd_ratio + trp_ratio) / 3

        if avg_ratio < 0.8:
            return 1.15
        elif avg_ratio < 0.9:
            return 1.08
        elif avg_ratio < 1.0:
            return 1.03
        else:
            return max(0.95, 1.1 - avg_ratio)

    def _calculate_command_overhead(self) -> float:
        """
        Calculate command processing overhead.

        Returns:
            Command overhead in nanoseconds.
        """
        # DDR3 has higher base command overhead than DDR5
        base_overhead = 3.5

        # Additional overhead for high frequencies
        frequency_overhead = max(
            0, (self.current_config.frequency - 1600) * 0.002
        )

        return base_overhead + frequency_overhead

    def _get_stability_recommendation(
        self,
        stability_score: float,
        config_violations: Any,
    ) -> str:
        """
        Generate stability recommendations based on score and violations.

        Args:
            stability_score: Calculated stability score
            config_violations: Configuration violations dict

        Returns:
            Recommendation string
        """
        recommendations: List[str] = []

        if stability_score < 0.6:
            recommendations.append("Increase voltage slightly")
            recommendations.append("Reduce frequency")
        if stability_score < 0.7:
            recommendations.append("Consider better cooling solutions")
        if stability_score < 0.8:
            recommendations.append(
                "Check memory seating and motherboard slots"
            )

        for violation in config_violations:
            if violation == "timing_violations":
                recommendations.append("Relax timings in BIOS")
            elif violation == "voltage_violations":
                recommendations.append("Adjust voltage settings")
            elif violation == "temperature_violations":
                recommendations.append("Improve cooling or reduce load")
            elif violation == "frequency_violations":
                recommendations.append("Lower the memory frequency")

        if not recommendations:
            return "No action needed. System is stable."

        return " | ".join(recommendations)
