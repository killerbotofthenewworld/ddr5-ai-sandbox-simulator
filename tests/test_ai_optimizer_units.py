# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false
# mypy: disable-error-code=attr-defined, unused-argument

import pytest

from src.ddr5_models import (
    DDR5Configuration,
    DDR5TimingParameters,
    DDR5VoltageParameters,
)
from src.ai_optimizer import (
    AIOptimizer,
    EnsembleOptimizer,
    GeneticAlgorithmOptimizer,
    ReinforcementLearningOptimizer,
    OptimizationResult,
)


def make_config(
    freq: int = 5600,
    cl: int = 40,
    trcd: int = 40,
    trp: int = 40,
    tras: int = 80,
    trc: int = 120,
    trfc: int = 300,
    vddq: float = 1.1,
    vpp: float = 1.8,
) -> DDR5Configuration:
    return DDR5Configuration(
        frequency=freq,
        timings=DDR5TimingParameters(
            cl=cl, trcd=trcd, trp=trp, tras=tras, trc=trc, trfc=trfc
        ),
        voltages=DDR5VoltageParameters(vddq=vddq, vpp=vpp),
    )


def test_apply_constraints_limits():
    base = make_config(freq=7000, vddq=1.2)
    opt = AIOptimizer()
    constrained = opt._apply_constraints(
        base, {"max_frequency": 6000, "max_voltage": 1.10}
    )
    assert constrained.frequency == 6000
    assert constrained.voltages.vddq == 1.10


@pytest.mark.parametrize(
    "goal,expected_rate",
    [
        ("performance", 0.15),
        ("stability", 0.05),
        ("efficiency", 0.10),
        ("balanced", 0.10),
    ],
)
def test_configure_for_goal_variants(goal: str, expected_rate: float):
    opt = AIOptimizer()
    # Default rate is 0.10; each goal adjusts per branch logic
    opt._configure_for_goal(goal)
    assert opt.ensemble_optimizer.ga_optimizer.mutation_rate == pytest.approx(
        expected_rate
    )


def test_get_optimization_suggestions_monkeypatched(monkeypatch):
    # Return metrics that trigger all suggestion branches
    class DummySim:
        def simulate_performance(self, _cfg):
            return {
                "memory_bandwidth": 70000,  # low
                "memory_latency": 20,  # high
                "stability_score": 0.6,  # low
            }

    import src.ai_optimizer as ai_mod

    monkeypatch.setattr(ai_mod, "DDR5Simulator", DummySim, raising=True)
    opt = AIOptimizer()
    sugg = opt.get_optimization_suggestions(make_config())
    kinds = {s["type"] for s in sugg}
    assert {"frequency", "timings", "voltage"}.issubset(kinds)


def test_export_optimization_history(tmp_path):
    opt = AIOptimizer()
    # Preload a fake history entry
    opt.optimization_history.append({"method": "genetic", "score": 0.5})
    out = tmp_path / "hist.json"
    opt.export_optimization_history(str(out))
    data = out.read_text(encoding="utf-8")
    assert "genetic" in data and "score" in data


def test_ga_enforce_jedec_constraints():
    ga = GeneticAlgorithmOptimizer()
    bad = make_config(
        freq=8400,  # max valid; exercise repair on other fields
        cl=0,
        trcd=0,
        trp=0,
        tras=1,
        trc=1,
        trfc=0,
        vddq=0.9,  # too low
        vpp=2.5,  # too high
    )
    fixed = ga._enforce_jedec_constraints(bad)
    assert 4000 <= fixed.frequency <= 8400
    assert 1.05 <= fixed.voltages.vddq <= 1.25
    assert 1.7 <= fixed.voltages.vpp <= 2.0
    # Derived relations
    assert fixed.timings.tras >= fixed.timings.trcd + fixed.timings.cl
    assert fixed.timings.trc >= fixed.timings.tras + fixed.timings.trp


def test_rl_actions_and_apply():
    rl = ReinforcementLearningOptimizer(epsilon=0.0)  # deterministic choose from Q
    cfg = make_config(freq=4400, cl=10, vddq=1.10)
    actions = rl.get_actions(cfg)
    # Can go up in freq, down in cl, up/down in vddq
    assert "freq_up" in actions and "cl_down" in actions and "vddq_down" in actions
    # Apply an action and ensure it changes config within bounds
    new_cfg = rl.apply_action(cfg, "freq_up")
    assert new_cfg.frequency >= cfg.frequency
    new_cfg = rl.apply_action(cfg, "vddq_down")
    assert new_cfg.voltages.vddq <= cfg.voltages.vddq
    # State key sanity
    key = rl.state_to_key(cfg)
    assert str(cfg.frequency) in key and str(cfg.timings.cl) in key


def test_ensemble_dispatch_and_combine(monkeypatch):
    base = make_config()
    ens = EnsembleOptimizer()

    # Lightweight fake results to avoid heavy compute
    def fake_res(_tag: str, score: float, n: int) -> OptimizationResult:
        hist = [{"generation": i, "best_fitness": score + i} for i in range(n)]
        return OptimizationResult(
            best_config=base.model_copy(),
            best_score=score,
            optimization_history=hist,
            generation_count=n,
            convergence_achieved=True,
            execution_time=0.01,
        )

    monkeypatch.setattr(
        ens.ga_optimizer, "optimize", lambda cfg: fake_res("ga", 0.6, 3), raising=True
    )
    monkeypatch.setattr(
        ens.rl_optimizer,
        "optimize",
        lambda cfg, episodes=500: fake_res("rl", 0.7, 2),
        raising=True,
    )

    # Direct method routes
    r1 = ens.optimize(base, method="genetic")
    r2 = ens.optimize(base, method="reinforcement")
    assert r1.best_score == 0.6
    assert r2.best_score == 0.7

    # Ensemble combines and picks rl (higher score)
    r3 = ens.optimize(base, method="ensemble")
    assert r3.best_score == 0.7
    # Combined history equals sum of parts
    assert r3.generation_count == 5


def test_ai_optimizer_orchestration_with_mocked_ensemble(monkeypatch):
    base = make_config(freq=6200)
    opt = AIOptimizer()

    # Mock ensemble to avoid heavy runs and control result
    def fake_optimize(cfg, method="ensemble") -> OptimizationResult:
        return OptimizationResult(
            best_config=cfg.model_copy(),
            best_score=0.88,
            optimization_history=[{"g": 0}],
            generation_count=1,
            convergence_achieved=True,
            execution_time=0.01,
        )

    monkeypatch.setattr(opt.ensemble_optimizer, "optimize", fake_optimize, raising=True)

    res = opt.optimize_configuration(
        base,
        optimization_goal="stability",
        method="ensemble",
        constraints={"max_frequency": 6000},
    )
    # Ensure constraints applied and history recorded
    assert res.best_config.frequency <= 6000
    assert (
        opt.optimization_history
        and opt.optimization_history[-1]["method"] == "ensemble"
    )
