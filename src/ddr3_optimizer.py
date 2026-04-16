"""
Core AI Optimization Engine for DDR3 Memory Tuning

Provides genetic algorithm optimization for DDR3 memory parameter tuning,
mirroring the DDR5 AI optimizer architecture.
"""

import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass
import random
import logging

try:
    from .ddr3_models import DDR3Configuration
    from .ddr3_simulator import DDR3Simulator
except ImportError:
    from src.ddr3_models import DDR3Configuration
    from src.ddr3_simulator import DDR3Simulator

logger = logging.getLogger(__name__)


@dataclass
class DDR3OptimizationResult:
    """Result of a DDR3 optimization run."""

    best_config: DDR3Configuration
    best_score: float
    optimization_history: List[Dict[str, Any]]
    generation_count: int
    convergence_achieved: bool
    execution_time: float


class DDR3GeneticAlgorithmOptimizer:
    """Genetic Algorithm optimizer for DDR3 parameters."""

    def __init__(
        self,
        population_size: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elitism_ratio: float = 0.2,
        max_generations: int = 100,
    ) -> None:
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_ratio = elitism_ratio
        self.max_generations = max_generations
        self.simulator = DDR3Simulator()

    @staticmethod
    def _enforce_jedec_constraints(
        cfg: DDR3Configuration,
    ) -> DDR3Configuration:
        """Repair config to satisfy JEDEC-like timing relationships.

        Rules applied conservatively:
        - Frequency within 800..2133 MT/s
        - Voltages within safe DDR3 ranges
        - tRAS >= tRCD + tCL
        - tRC >= tRAS + tRP
        - All timings >= 1
        """
        repaired = cfg.model_copy()

        # Frequency
        repaired.frequency = int(max(800, min(2133, repaired.frequency)))

        # Voltages
        repaired.voltages.vdd = float(
            max(1.35, min(1.65, round(repaired.voltages.vdd, 3)))
        )
        repaired.voltages.vddq = float(
            max(1.35, min(1.65, round(repaired.voltages.vddq, 3)))
        )
        repaired.voltages.vtt = float(
            max(0.675, min(0.825, round(repaired.voltages.vtt, 3)))
        )

        t = repaired.timings
        # Floor all timing values to >= 1
        t.cl = max(1, t.cl)
        t.trcd = max(1, t.trcd)
        t.trp = max(1, t.trp)
        t.tras = max(1, t.tras)
        t.trc = max(1, t.trc)
        t.tcwl = max(1, t.tcwl)

        # Enforce: tRAS >= tRCD + CL
        min_tras = t.trcd + t.cl
        if t.tras < min_tras:
            t.tras = min_tras

        # Enforce: tRC >= tRAS + tRP
        min_trc = t.tras + t.trp
        if t.trc < min_trc:
            t.trc = min_trc

        return repaired

    def _generate_random_config(self) -> DDR3Configuration:
        """Generate a random DDR3 configuration within valid ranges."""
        valid_speeds = [800, 1066, 1333, 1600, 1866, 2133]
        freq = random.choice(valid_speeds)

        cl = random.randint(7, 15)
        trcd = random.randint(7, 15)
        trp = random.randint(7, 15)
        tras = max(cl + trcd, random.randint(20, 36))
        trc = max(tras + trp, random.randint(30, 50))

        cfg = DDR3Configuration(
            frequency=freq,
            timings=__import__(
                "src.ddr3_models", fromlist=["DDR3TimingParameters"]
            ).DDR3TimingParameters(
                cl=cl,
                trcd=trcd,
                trp=trp,
                tras=tras,
                trc=trc,
            ),
            voltages=__import__(
                "src.ddr3_models", fromlist=["DDR3VoltageParameters"]
            ).DDR3VoltageParameters(
                vdd=round(random.uniform(1.35, 1.65), 3),
                vddq=round(random.uniform(1.35, 1.65), 3),
                vtt=round(random.uniform(0.675, 0.825), 3),
            ),
        )
        return self._enforce_jedec_constraints(cfg)

    def _evaluate_fitness(
        self, config: DDR3Configuration, goal: str = "balanced"
    ) -> float:
        """Evaluate the fitness of a DDR3 configuration.

        Args:
            config: Configuration to evaluate
            goal: Optimization goal

        Returns:
            Fitness score (higher is better)
        """
        self.simulator.load_configuration(config)
        bandwidth = self.simulator.simulate_bandwidth("mixed")
        latency = self.simulator.simulate_latency("random")
        power = self.simulator.simulate_power_consumption()
        stability = config.get_stability_estimate()

        bw_score = bandwidth["effective_bandwidth_gbps"] * 10
        lat_score = max(0, 100 - latency["effective_latency_ns"])
        pwr_score = max(0, 100 - power["total_power_w"] * 10)
        stab_score = stability

        weights = {
            "performance": (0.5, 0.3, 0.05, 0.15),
            "stability": (0.15, 0.15, 0.1, 0.6),
            "efficiency": (0.2, 0.2, 0.4, 0.2),
            "balanced": (0.3, 0.25, 0.15, 0.3),
        }

        w = weights.get(goal, weights["balanced"])
        return (
            bw_score * w[0]
            + lat_score * w[1]
            + pwr_score * w[2]
            + stab_score * w[3]
        )

    def _crossover(
        self,
        parent1: DDR3Configuration,
        parent2: DDR3Configuration,
    ) -> DDR3Configuration:
        """Perform crossover between two parent configurations."""
        child = parent1.model_copy()

        if random.random() < 0.5:
            child.frequency = parent2.frequency
        if random.random() < 0.5:
            child.timings.cl = parent2.timings.cl
            child.timings.trcd = parent2.timings.trcd
        if random.random() < 0.5:
            child.timings.trp = parent2.timings.trp
            child.timings.tras = parent2.timings.tras
            child.timings.trc = parent2.timings.trc
        if random.random() < 0.5:
            child.voltages.vdd = parent2.voltages.vdd
            child.voltages.vddq = parent2.voltages.vddq

        return self._enforce_jedec_constraints(child)

    def _mutate(self, config: DDR3Configuration) -> DDR3Configuration:
        """Apply random mutations to a configuration."""
        mutated = config.model_copy()

        if random.random() < self.mutation_rate:
            valid_speeds = [800, 1066, 1333, 1600, 1866, 2133]
            mutated.frequency = random.choice(valid_speeds)

        if random.random() < self.mutation_rate:
            mutated.timings.cl += random.randint(-2, 2)
        if random.random() < self.mutation_rate:
            mutated.timings.trcd += random.randint(-2, 2)
        if random.random() < self.mutation_rate:
            mutated.timings.trp += random.randint(-2, 2)

        if random.random() < self.mutation_rate:
            mutated.voltages.vdd += round(
                random.uniform(-0.05, 0.05), 3
            )
        if random.random() < self.mutation_rate:
            mutated.voltages.vddq += round(
                random.uniform(-0.05, 0.05), 3
            )

        return self._enforce_jedec_constraints(mutated)

    def optimize(
        self,
        goal: str = "balanced",
        initial_config: DDR3Configuration = None,
    ) -> DDR3OptimizationResult:
        """Run genetic algorithm optimization.

        Args:
            goal: Optimization goal
            initial_config: Optional starting configuration

        Returns:
            DDR3OptimizationResult with best configuration found
        """
        import time

        start_time = time.time()

        # Initialize population
        population: List[DDR3Configuration] = []
        if initial_config:
            population.append(
                self._enforce_jedec_constraints(initial_config)
            )

        while len(population) < self.population_size:
            population.append(self._generate_random_config())

        history: List[Dict[str, Any]] = []
        best_config = population[0]
        best_score = float("-inf")
        convergence = False

        for gen in range(self.max_generations):
            # Evaluate fitness
            scores = [
                self._evaluate_fitness(cfg, goal) for cfg in population
            ]

            # Track best
            gen_best_idx = int(np.argmax(scores))
            gen_best_score = scores[gen_best_idx]

            if gen_best_score > best_score:
                best_score = gen_best_score
                best_config = population[gen_best_idx].model_copy()

            history.append(
                {
                    "generation": gen,
                    "best_score": gen_best_score,
                    "avg_score": float(np.mean(scores)),
                    "best_frequency": population[gen_best_idx].frequency,
                }
            )

            # Check convergence
            if len(history) > 10:
                recent = [h["best_score"] for h in history[-10:]]
                if max(recent) - min(recent) < 0.01:
                    convergence = True
                    break

            # Selection and reproduction
            elite_count = max(
                1, int(self.population_size * self.elitism_ratio)
            )
            sorted_indices = np.argsort(scores)[::-1]
            elites = [
                population[i].model_copy()
                for i in sorted_indices[:elite_count]
            ]

            new_population = list(elites)
            while len(new_population) < self.population_size:
                p1 = random.choice(elites)
                p2 = random.choice(population)
                if random.random() < self.crossover_rate:
                    child = self._crossover(p1, p2)
                else:
                    child = p1.model_copy()
                child = self._mutate(child)
                new_population.append(child)

            population = new_population

        execution_time = time.time() - start_time

        return DDR3OptimizationResult(
            best_config=best_config,
            best_score=best_score,
            optimization_history=history,
            generation_count=len(history),
            convergence_achieved=convergence,
            execution_time=execution_time,
        )
