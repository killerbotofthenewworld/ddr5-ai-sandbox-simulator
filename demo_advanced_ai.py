#!/usr/bin/env python3
"""
Demo: Advanced AI DDR5 Optimization

Runs the AI optimizer on a sample DDR5 configuration and prints results.
"""

import sys
from pathlib import Path

# Ensure src is on the path
sys.path.insert(0, str(Path(__file__).parent))

from src.ddr5_models import DDR5Configuration, DDR5TimingParameters, DDR5VoltageParameters
from src.ddr5_simulator import DDR5Simulator
from src.ai_optimizer import GeneticAlgorithmOptimizer


def main() -> None:
    """Run a quick AI optimization demo."""
    print("=" * 60)
    print("  DDR5 Advanced AI Optimization Demo")
    print("=" * 60)

    # Create a baseline config
    base_config = DDR5Configuration(
        frequency=5600,
        timings=DDR5TimingParameters(cl=32, trcd=32, trp=32, tras=64, trc=96),
        voltages=DDR5VoltageParameters(vddq=1.1, vpp=1.8),
    )

    print(f"\nBaseline: DDR5-{base_config.frequency} CL{base_config.timings.cl}")

    # Simulate baseline performance
    sim = DDR5Simulator()
    sim.load_configuration(base_config)
    baseline_perf = sim.simulate_performance()
    print(f"  Score      : {baseline_perf['score']:.1f}")
    print(f"  Bandwidth  : {baseline_perf['bandwidth']:.0f} MB/s")
    print(f"  Latency    : {baseline_perf['latency']:.2f} ns")
    print(f"  Power      : {baseline_perf['power']:.0f} mW")
    print(f"  Stability  : {baseline_perf['stability']:.1f}")

    # Run a small genetic-algorithm optimisation
    print("\nRunning Genetic Algorithm (10 generations, pop=20) ...")
    ga = GeneticAlgorithmOptimizer(
        population_size=20,
        max_generations=10,
        mutation_rate=0.15,
    )
    result = ga.optimize(base_config)

    best = result.best_config
    print(f"\nOptimised : DDR5-{best.frequency} CL{best.timings.cl}")
    print(f"  Best score : {result.best_score:.1f}")
    print(f"  Generations: {result.generation_count}")
    print(f"  Converged  : {result.convergence_achieved}")
    print(f"  Time       : {result.execution_time:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
