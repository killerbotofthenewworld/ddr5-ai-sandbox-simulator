"""
Core AI Optimization Engine for DDR5 Memory Tuning

This module provides the fundamental AI optimization algorithms for DDR5 memory
parameter tuning, including genetic algorithms, reinforcement learning, and
ensemble methods.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import random
import logging
import json
from datetime import datetime

try:
    from .ddr5_models import DDR5Configuration
    from .ddr5_simulator import DDR5Simulator
except ImportError:
    from src.ddr5_models import DDR5Configuration
    from src.ddr5_simulator import DDR5Simulator

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of an optimization run"""

    best_config: DDR5Configuration
    best_score: float
    optimization_history: List[Dict[str, Any]]
    generation_count: int
    convergence_achieved: bool
    execution_time: float


class GeneticAlgorithmOptimizer:
    """Genetic Algorithm optimizer for DDR5 parameters"""

    def __init__(
        self,
        population_size: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elitism_ratio: float = 0.2,
        max_generations: int = 100,
    ):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_ratio = elitism_ratio
        self.max_generations = max_generations
        self.simulator = DDR5Simulator()

    @staticmethod
    def _enforce_jedec_constraints(cfg: DDR5Configuration) -> DDR5Configuration:
        """Repair config to satisfy JEDEC-like timing relationships and bounds.

        Rules applied conservatively:
        - Frequency within 4000..8400 MT/s
        - Voltages within nominal safe ranges (VDDQ 1.05..1.25, VPP 1.7..2.0)
        - tRAS >= tRCD + tCL
        - tRC >= tRAS + tRP
        - All timings >= 1
        """
        repaired = cfg.model_copy()

        # Frequency
        repaired.frequency = int(max(4000, min(8400, repaired.frequency)))

        # Voltages
        repaired.voltages.vddq = float(
            max(1.05, min(1.25, round(repaired.voltages.vddq, 3)))
        )
        repaired.voltages.vpp = float(
            max(1.7, min(2.0, round(repaired.voltages.vpp, 3)))
        )

        # Timings min bounds
        t = repaired.timings
        for name in ("cl", "trcd", "trp", "tras", "trc", "trfc"):
            if hasattr(t, name):
                setattr(t, name, max(1, int(getattr(t, name))))

        # Derived constraints
        t.tras = max(t.tras, t.trcd + t.cl)
        t.trc = max(t.trc, t.tras + t.trp)

        return repaired

    def create_random_config(self, base_config: DDR5Configuration) -> DDR5Configuration:
        """Create a random configuration based on a base configuration"""
        config = base_config.model_copy()

        # Randomly adjust timings within safe bounds
        for timing_name in ["cl", "trcd", "trp", "tras", "trc", "trfc"]:
            if hasattr(config.timings, timing_name):
                current_value = getattr(config.timings, timing_name)
                # Allow ±20% variation
                min_val = max(1, int(current_value * 0.8))
                max_val = int(current_value * 1.2)
            setattr(config.timings, timing_name, random.randint(min_val, max_val))

            # Randomly adjust frequency within DDR5 range
            config.frequency = random.randint(4000, 8400)

            # Randomly adjust voltages within safe range
            config.voltages.vddq = round(random.uniform(1.05, 1.25), 3)
            config.voltages.vpp = round(random.uniform(1.7, 2.0), 3)

            return self._enforce_jedec_constraints(config)

    def crossover(
        self,
        parent1: DDR5Configuration,
        parent2: DDR5Configuration,
    ) -> Tuple[DDR5Configuration, DDR5Configuration]:
        """Perform crossover between two parent configurations"""
        child1 = parent1.model_copy()
        child2 = parent2.model_copy()

        # Crossover timings
        for timing_name in ["cl", "trcd", "trp", "tras", "trc", "trfc"]:
            if random.random() < 0.5:
                val1 = getattr(parent1.timings, timing_name)
                val2 = getattr(parent2.timings, timing_name)
                setattr(child1.timings, timing_name, val2)
                setattr(child2.timings, timing_name, val1)

        # Crossover frequency
        if random.random() < 0.5:
            child1.frequency, child2.frequency = parent2.frequency, parent1.frequency

        # Crossover voltages
        if random.random() < 0.5:
            child1.voltages.vddq, child2.voltages.vddq = (
                parent2.voltages.vddq,
                parent1.voltages.vddq,
            )
        if random.random() < 0.5:
            child1.voltages.vpp, child2.voltages.vpp = (
                parent2.voltages.vpp,
                parent1.voltages.vpp,
            )

        return (
            self._enforce_jedec_constraints(child1),
            self._enforce_jedec_constraints(child2),
        )

    def mutate(self, config: DDR5Configuration) -> DDR5Configuration:
        """Mutate a configuration"""
        mutated = config.model_copy()

        # Mutate timings
        for timing_name in ["cl", "trcd", "trp", "tras", "trc", "trfc"]:
            if random.random() < self.mutation_rate:
                current_value = getattr(mutated.timings, timing_name)
                # Small random adjustment
                adjustment = random.randint(-2, 2)
                new_value = max(1, current_value + adjustment)
                setattr(mutated.timings, timing_name, new_value)

        # Mutate frequency
        if random.random() < self.mutation_rate:
            adjustment = random.randint(-200, 200)
            mutated.frequency = max(4000, min(8400, mutated.frequency + adjustment))

        # Mutate voltages
        if random.random() < self.mutation_rate:
            mutated.voltages.vddq = max(
                1.05,
                min(1.25, mutated.voltages.vddq + random.uniform(-0.02, 0.02)),
            )
        if random.random() < self.mutation_rate:
            mutated.voltages.vpp = max(
                1.7,
                min(2.0, mutated.voltages.vpp + random.uniform(-0.05, 0.05)),
            )

        return self._enforce_jedec_constraints(mutated)

    def evaluate_fitness(self, config: DDR5Configuration) -> float:
        """Evaluate the fitness of a configuration"""
        try:
            # Ensure constraints before evaluation
            config = self._enforce_jedec_constraints(config)
            metrics = self.simulator.simulate_performance(config)

            # Composite fitness score
            # Handle both legacy and current simulator keys
            m_bandwidth = metrics.get("memory_bandwidth", metrics.get("bandwidth", 0.0))
            m_latency = metrics.get("memory_latency", metrics.get("latency", 0.0))
            m_stability = metrics.get("stability_score", metrics.get("stability", 0.0))

            # Normalize bandwidth to ~0..1
            bandwidth_score = float(m_bandwidth) / 100000.0
            # Lower latency is better
            latency_score = 1.0 / (float(m_latency) + 1.0)
            stability_score = float(m_stability)

            # Weighted combination
            fitness = (
                0.4 * bandwidth_score + 0.3 * latency_score + 0.3 * stability_score
            )

            return max(0.0, fitness)
        except Exception as e:
            logger.warning(f"Error evaluating fitness: {e}")
            return 0.0

    def optimize(
        self, base_config: DDR5Configuration, target_metric: str = "overall"
    ) -> OptimizationResult:
        """Run genetic algorithm optimization"""
        start_time = datetime.now()

        # Initialize population
        population = [
            self.create_random_config(base_config) for _ in range(self.population_size)
        ]
        history = []

        best_config = None
        best_fitness = -1

        for generation in range(self.max_generations):
            # Evaluate fitness for all individuals
            fitness_scores = []
            for config in population:
                fitness = self.evaluate_fitness(config)
                fitness_scores.append(fitness)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_config = config.model_copy()

            # Record generation statistics
            gen_stats = {
                "generation": generation,
                "best_fitness": best_fitness,
                "avg_fitness": np.mean(fitness_scores),
                "std_fitness": np.std(fitness_scores),
                "timestamp": datetime.now().isoformat(),
            }
            history.append(gen_stats)

            logger.info(
                "Generation %d: Best=%.4f, Avg=%.4f",
                generation,
                best_fitness,
                gen_stats["avg_fitness"],
            )

            # Check convergence
            if len(history) >= 10:
                recent_best = [h["best_fitness"] for h in history[-10:]]
                if max(recent_best) - min(recent_best) < 0.001:
                    logger.info(f"Converged at generation {generation}")
                    break

            # Selection and reproduction
            new_population = []

            # Elitism - keep best individuals
            elite_count = int(self.population_size * self.elitism_ratio)
            elite_indices = sorted(
                range(len(fitness_scores)),
                key=lambda i: fitness_scores[i],
                reverse=True,
            )[:elite_count]
            for i in elite_indices:
                new_population.append(population[i].model_copy())

            # Generate offspring
            while len(new_population) < self.population_size:
                # Tournament selection
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)

                # Crossover
                if random.random() < self.crossover_rate:
                    child1, child2 = self.crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.model_copy(), parent2.model_copy()

                # Mutation
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)

                new_population.extend([child1, child2])

            # Trim to population size
            population = new_population[: self.population_size]

        execution_time = (datetime.now() - start_time).total_seconds()

        # Fallback to base_config if best_config somehow stayed None
        final_best = best_config or base_config
        return OptimizationResult(
            best_config=final_best,
            best_score=best_fitness,
            optimization_history=history,
            generation_count=len(history),
            convergence_achieved=len(history) < self.max_generations,
            execution_time=execution_time,
        )

    def _tournament_selection(
        self,
        population: List[DDR5Configuration],
        fitness_scores: List[float],
        tournament_size: int = 3,
    ) -> DDR5Configuration:
        """Tournament selection for genetic algorithm"""
        tournament_indices = random.sample(
            range(len(population)), min(tournament_size, len(population))
        )
        best_index = max(tournament_indices, key=lambda i: fitness_scores[i])
        return population[best_index]


class ReinforcementLearningOptimizer:
    """Q-Learning based optimizer for DDR5 parameters"""

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
    ) -> None:
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.q_table = {}
        self.simulator = DDR5Simulator()

    def state_to_key(self, config: DDR5Configuration) -> str:
        """Convert configuration to state key"""
        return (
            f"{config.frequency}_"
            f"{config.timings.cl}_"
            f"{config.timings.trcd}_"
            f"{config.voltages.vddq:.2f}"
        )

    def get_actions(self, config: DDR5Configuration) -> List[str]:
        """Get possible actions from current state"""
        actions = []

        # Frequency adjustments
        if config.frequency > 4000:
            actions.append("freq_down")
        if config.frequency < 8400:
            actions.append("freq_up")

        # Timing adjustments
        if config.timings.cl > 1:
            actions.append("cl_down")
        actions.append("cl_up")

        # Voltage adjustments
        if config.voltages.vddq > 1.05:
            actions.append("vddq_down")
        if config.voltages.vddq < 1.25:
            actions.append("vddq_up")

        return actions

    def apply_action(self, config: DDR5Configuration, action: str) -> DDR5Configuration:
        """Apply action to configuration"""
        new_config = config.model_copy()

        if action == "freq_up":
            new_config.frequency = min(8400, new_config.frequency + 100)
        elif action == "freq_down":
            new_config.frequency = max(4000, new_config.frequency - 100)
        elif action == "cl_up":
            new_config.timings.cl += 1
        elif action == "cl_down":
            new_config.timings.cl = max(1, new_config.timings.cl - 1)
        elif action == "vddq_up":
            new_config.voltages.vddq = min(1.25, new_config.voltages.vddq + 0.01)
        elif action == "vddq_down":
            new_config.voltages.vddq = max(1.05, new_config.voltages.vddq - 0.01)

        return new_config

    def optimize(
        self, base_config: DDR5Configuration, episodes: int = 1000
    ) -> OptimizationResult:
        """Run reinforcement learning optimization"""
        start_time = datetime.now()
        history = []

        best_config = base_config.model_copy()
        best_score = self.evaluate_config(base_config)

        current_config = base_config.model_copy()

        for episode in range(episodes):
            state_key = self.state_to_key(current_config)
            actions = self.get_actions(current_config)

            if not actions:
                break

            # Epsilon-greedy action selection
            if random.random() < self.epsilon or state_key not in self.q_table:
                action = random.choice(actions)
            else:
                q_values = self.q_table[state_key]
                action = max(q_values, key=q_values.get)

            # Apply action and get reward
            new_config = self.apply_action(current_config, action)
            reward = self.evaluate_config(new_config)

            # Update Q-table
            if state_key not in self.q_table:
                self.q_table[state_key] = {a: 0.0 for a in actions}

            new_state_key = self.state_to_key(new_config)
            new_actions = self.get_actions(new_config)

            if new_actions and new_state_key in self.q_table:
                max_future_q = max(self.q_table[new_state_key].values())
            else:
                max_future_q = 0.0

            current_q = self.q_table[state_key][action]
            new_q = current_q + self.learning_rate * (
                reward + self.discount_factor * max_future_q - current_q
            )
            self.q_table[state_key][action] = new_q

            # Update best configuration
            if reward > best_score:
                best_score = reward
                best_config = new_config.model_copy()

            # Record episode statistics
            episode_stats = {
                "episode": episode,
                "reward": reward,
                "best_score": best_score,
                "epsilon": self.epsilon,
                "action": action,
                "timestamp": datetime.now().isoformat(),
            }
            history.append(episode_stats)

            # Update state and epsilon
            current_config = new_config
            self.epsilon *= self.epsilon_decay

            if episode % 100 == 0:
                logger.info(
                    "Episode %d: Reward=%.4f, Best=%.4f, Epsilon=%.4f",
                    episode,
                    reward,
                    best_score,
                    self.epsilon,
                )

        execution_time = (datetime.now() - start_time).total_seconds()

        return OptimizationResult(
            best_config=best_config,
            best_score=best_score,
            optimization_history=history,
            generation_count=episodes,
            convergence_achieved=True,
            execution_time=execution_time,
        )

    def evaluate_config(self, config: DDR5Configuration) -> float:
        """Evaluate configuration and return reward"""
        try:
            metrics = self.simulator.simulate_performance(config)
            # Handle both legacy and current simulator keys
            m_bandwidth = metrics.get("memory_bandwidth", metrics.get("bandwidth", 0.0))
            m_latency = metrics.get("memory_latency", metrics.get("latency", 0.0))
            m_stability = metrics.get("stability_score", metrics.get("stability", 0.0))
            # Composite reward based on performance metrics
            return (
                float(m_bandwidth) / 100000.0
                + 1.0 / (float(m_latency) + 1.0)
                + float(m_stability)
            ) / 3.0
        except Exception:
            return 0.0


class EnsembleOptimizer:
    """Ensemble optimizer combining multiple optimization strategies"""

    def __init__(self):
        self.ga_optimizer = GeneticAlgorithmOptimizer(
            population_size=30, max_generations=50
        )
        self.rl_optimizer = ReinforcementLearningOptimizer(epsilon=0.2)

    def optimize(
        self, base_config: DDR5Configuration, method: str = "ensemble"
    ) -> OptimizationResult:
        """Run ensemble optimization"""
        start_time = datetime.now()

        if method == "genetic":
            return self.ga_optimizer.optimize(base_config)
        elif method == "reinforcement":
            return self.rl_optimizer.optimize(base_config, episodes=500)
        elif method == "ensemble":
            # Run both optimizers and combine results
            ga_result = self.ga_optimizer.optimize(base_config)
            rl_result = self.rl_optimizer.optimize(base_config, episodes=500)

            # Select best result
            if ga_result.best_score > rl_result.best_score:
                best_result = ga_result
            else:
                best_result = rl_result

            # Combine history
            combined_history = []
            combined_history.extend(
                [{**h, "method": "genetic"} for h in ga_result.optimization_history]
            )
            combined_history.extend(
                [
                    {**h, "method": "reinforcement"}
                    for h in rl_result.optimization_history
                ]
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            return OptimizationResult(
                best_config=best_result.best_config,
                best_score=best_result.best_score,
                optimization_history=combined_history,
                generation_count=len(combined_history),
                convergence_achieved=best_result.convergence_achieved,
                execution_time=execution_time,
            )
        else:
            raise ValueError(f"Unknown optimization method: {method}")


class AIOptimizer:
    """Main AI Optimizer class that orchestrates different optimization strategies"""

    def __init__(self):
        self.ensemble_optimizer = EnsembleOptimizer()
        self.optimization_history = []

    def optimize_configuration(
        self,
        base_config: DDR5Configuration,
        optimization_goal: str = "performance",
        method: str = "ensemble",
        constraints: Optional[Dict[str, Any]] = None,
    ) -> OptimizationResult:
        """
        Optimize DDR5 configuration using AI algorithms

        Args:
            base_config: Starting configuration
            optimization_goal: "performance", "stability", "efficiency", or "balanced"
            method: "genetic", "reinforcement", or "ensemble"
            constraints: Optional constraints dict
        """
        logger.info(
            "Starting AI optimization with method: %s, goal: %s",
            method,
            optimization_goal,
        )

        # Apply constraints to base configuration if provided
        if constraints:
            base_config = self._apply_constraints(base_config, constraints)

        # Configure optimizer based on goal
        self._configure_for_goal(optimization_goal)

        # Run optimization
        result = self.ensemble_optimizer.optimize(base_config, method)

        # Store in history
        optimization_record = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "goal": optimization_goal,
            "base_config": base_config.model_dump(),
            "result_config": result.best_config.model_dump(),
            "score": result.best_score,
            "execution_time": result.execution_time,
            "convergence": result.convergence_achieved,
        }
        self.optimization_history.append(optimization_record)

        logger.info(f"Optimization completed. Best score: {result.best_score:.4f}")

        return result

    def _apply_constraints(
        self, config: DDR5Configuration, constraints: Dict[str, Any]
    ) -> DDR5Configuration:
        """Apply constraints to configuration"""
        constrained_config = config.model_copy()

        if "max_frequency" in constraints:
            constrained_config.frequency = min(
                constrained_config.frequency, constraints["max_frequency"]
            )

        if "max_voltage" in constraints:
            constrained_config.voltages.vddq = min(
                constrained_config.voltages.vddq, constraints["max_voltage"]
            )

        if "min_stability" in constraints:
            # This would require integration with stability prediction
            pass

        return constrained_config

    def _configure_for_goal(self, goal: str):
        """Configure optimizers based on optimization goal"""
        if goal == "performance":
            # Emphasize bandwidth and speed
            self.ensemble_optimizer.ga_optimizer.mutation_rate = 0.15
        elif goal == "stability":
            # More conservative approach
            self.ensemble_optimizer.ga_optimizer.mutation_rate = 0.05
        elif goal == "efficiency":
            # Balance performance and power
            self.ensemble_optimizer.ga_optimizer.mutation_rate = 0.1
        # "balanced" uses default settings

    def get_optimization_suggestions(
        self, current_config: DDR5Configuration
    ) -> List[Dict[str, Any]]:
        """Get AI-powered suggestions for configuration improvements"""
        suggestions = []

        # Analyze current configuration
        simulator = DDR5Simulator()
        current_metrics = simulator.simulate_performance(current_config)

        # Generate suggestions based on AI analysis
        if isinstance(current_metrics, dict):
            bandwidth = current_metrics.get("memory_bandwidth", 0)
            latency = current_metrics.get("memory_latency", 0)
            stability = current_metrics.get("stability_score", 0)
        else:
            bandwidth = current_metrics.memory_bandwidth
            latency = current_metrics.memory_latency
            stability = current_metrics.stability_score

        if bandwidth < 80000:  # Low bandwidth
            suggestions.append(
                {
                    "type": "frequency",
                    "suggestion": "Increase memory frequency for better bandwidth",
                    "confidence": 0.8,
                    "expected_improvement": "10-15% bandwidth increase",
                }
            )

        if latency > 15:  # High latency
            suggestions.append(
                {
                    "type": "timings",
                    "suggestion": "Tighten primary timings (CL, tRCD, tRP)",
                    "confidence": 0.7,
                    "expected_improvement": "5-10% latency reduction",
                }
            )

        if stability < 0.8:  # Low stability
            suggestions.append(
                {
                    "type": "voltage",
                    "suggestion": "Slightly increase VDDQ voltage for stability",
                    "confidence": 0.6,
                    "expected_improvement": "Improved stability score",
                }
            )

        return suggestions

    def export_optimization_history(self, filename: str):
        """Export optimization history to file"""
        with open(filename, "w") as f:
            json.dump(self.optimization_history, f, indent=2)

        logger.info(f"Optimization history exported to {filename}")
