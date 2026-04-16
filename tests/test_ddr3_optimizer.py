"""
Tests for DDR3 GA Optimizer constraints and basic optimization.
"""

import pytest
from src.ddr3_models import DDR3Configuration, DDR3TimingParameters
from src.ddr3_optimizer import DDR3GeneticAlgorithmOptimizer


class TestDDR3GAConstraints:
    """Tests for JEDEC constraint enforcement in the DDR3 GA optimizer."""

    def test_enforce_jedec_constraints_frequency(self):
        cfg = DDR3Configuration(frequency=800)
        cfg_obj = cfg.model_copy()
        # Force an out-of-range frequency
        object.__setattr__(cfg_obj, "frequency", 500)
        repaired = DDR3GeneticAlgorithmOptimizer._enforce_jedec_constraints(
            cfg_obj
        )
        assert 800 <= repaired.frequency <= 2133

    def test_enforce_jedec_constraints_voltages(self):
        cfg = DDR3Configuration()
        cfg.voltages.vdd = 2.0
        cfg.voltages.vddq = 1.0
        repaired = DDR3GeneticAlgorithmOptimizer._enforce_jedec_constraints(
            cfg
        )
        assert 1.35 <= repaired.voltages.vdd <= 1.65
        assert 1.35 <= repaired.voltages.vddq <= 1.65

    def test_enforce_jedec_constraints_tras(self):
        cfg = DDR3Configuration()
        cfg.timings.cl = 11
        cfg.timings.trcd = 11
        cfg.timings.tras = 10  # Too low
        repaired = DDR3GeneticAlgorithmOptimizer._enforce_jedec_constraints(
            cfg
        )
        assert repaired.timings.tras >= (
            repaired.timings.trcd + repaired.timings.cl
        )

    def test_enforce_jedec_constraints_trc(self):
        cfg = DDR3Configuration()
        cfg.timings.tras = 28
        cfg.timings.trp = 11
        cfg.timings.trc = 20  # Too low
        repaired = DDR3GeneticAlgorithmOptimizer._enforce_jedec_constraints(
            cfg
        )
        assert repaired.timings.trc >= (
            repaired.timings.tras + repaired.timings.trp
        )

    def test_random_configs_obey_constraints(self):
        """Generate many random configs and verify all satisfy constraints."""
        opt = DDR3GeneticAlgorithmOptimizer(population_size=10)
        for _ in range(50):
            cfg = opt._generate_random_config()
            assert 800 <= cfg.frequency <= 2133
            assert 1.35 <= cfg.voltages.vdd <= 1.65
            assert cfg.timings.tras >= cfg.timings.trcd + cfg.timings.cl
            assert cfg.timings.trc >= cfg.timings.tras + cfg.timings.trp


class TestDDR3Optimization:
    """Basic optimization tests."""

    def test_optimization_runs(self):
        opt = DDR3GeneticAlgorithmOptimizer(
            population_size=10, max_generations=5
        )
        result = opt.optimize(goal="balanced")
        assert result.best_score > 0
        assert result.generation_count > 0
        assert len(result.optimization_history) > 0

    def test_optimization_with_initial_config(self):
        opt = DDR3GeneticAlgorithmOptimizer(
            population_size=10, max_generations=5
        )
        initial = DDR3Configuration(frequency=1600)
        result = opt.optimize(goal="performance", initial_config=initial)
        assert result.best_config is not None

    def test_optimization_goals(self):
        opt = DDR3GeneticAlgorithmOptimizer(
            population_size=10, max_generations=3
        )
        for goal in ["performance", "stability", "efficiency", "balanced"]:
            result = opt.optimize(goal=goal)
            assert result.best_score > 0
