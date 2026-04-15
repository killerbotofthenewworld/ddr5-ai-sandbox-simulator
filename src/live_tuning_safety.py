"""
Live Tuning Safety Simulation Module
Comprehensive safety testing and validation for live DDR5 tuning capabilities.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time
import random
import numpy as np

from src.ddr5_models import DDR5Configuration, DDR5TimingParameters
from src.hardware_detection import DetectedRAMModule


class SafetyLevel(Enum):
    """Safety levels for live tuning operations."""
    CRITICAL_UNSAFE = "critical_unsafe"
    UNSAFE = "unsafe"
    CAUTION = "caution"
    SAFE = "safe"
    VERIFIED_SAFE = "verified_safe"


class TestType(Enum):
    """Types of safety tests."""
    VOLTAGE_VALIDATION = "voltage_validation"
    TIMING_VALIDATION = "timing_validation"
    THERMAL_SIMULATION = "thermal_simulation"
    STABILITY_PREDICTION = "stability_prediction"
    ROLLBACK_VERIFICATION = "rollback_verification"
    BIOS_COMPATIBILITY = "bios_compatibility"
    HARDWARE_LIMITS = "hardware_limits"


@dataclass
class SafetyTestResult:
    test_type: TestType
    safety_level: SafetyLevel
    score: float
    warnings: List[str]
    recommendations: List[str]
    details: Dict[str, Any]
    execution_time: float


@dataclass
class LiveTuningSafetyReport:
    overall_safety: SafetyLevel
    overall_score: float
    test_results: List[SafetyTestResult]
    detected_hardware: List[DetectedRAMModule]
    recommended_config: Optional[DDR5Configuration]
    critical_warnings: List[str]
    safety_recommendations: List[str]
    rollback_plan: Dict[str, Any]
    estimated_risk_level: str


class LiveTuningSafetyValidator:
    """Runs comprehensive safety validations for live tuning."""

    def __init__(self) -> None:
        # Basic manufacturer-specific limits (can be expanded)
        self.hardware_limits: Dict[str, Dict[str, Any]] = {
            "Generic": {"max_frequency": 6400, "min_cl": 28, "thermal_limit": 85},
            "Corsair": {"max_frequency": 6600, "min_cl": 28, "thermal_limit": 90},
            "G.SKILL": {"max_frequency": 6800, "min_cl": 28, "thermal_limit": 90},
            "Kingston": {"max_frequency": 6600, "min_cl": 28, "thermal_limit": 88},
        }
        self.test_results: List[SafetyTestResult] = []

    def run_comprehensive_safety_test(
        self,
        target_config: DDR5Configuration,
        detected_modules: List[DetectedRAMModule],
    ) -> LiveTuningSafetyReport:
        """Run comprehensive safety validation for live tuning."""
        print("🔒 Starting Live Tuning Safety Validation...")
        self.test_results = []

        tests = [
            self._test_voltage_safety,
            self._test_timing_safety,
            self._test_thermal_safety,
            self._test_stability_prediction,
            self._test_rollback_capability,
            self._test_bios_compatibility,
            self._test_hardware_limits,
        ]

        for test in tests:
            try:
                result = test(target_config, detected_modules)
                self.test_results.append(result)
                print(f"✅ {result.test_type.value}: {result.safety_level.value}")
            except (RuntimeError, ValueError) as e:
                self.test_results.append(
                    SafetyTestResult(
                        test_type=TestType.VOLTAGE_VALIDATION,
                        safety_level=SafetyLevel.CRITICAL_UNSAFE,
                        score=0.0,
                        warnings=[f"Test failed: {e}"],
                        recommendations=["Skip live tuning due to test failure"],
                        details={"error": str(e)},
                        execution_time=0.0,
                    )
                )

        return self._generate_safety_report(target_config, detected_modules)

    def _test_voltage_safety(
        self, config: DDR5Configuration, modules: List[DetectedRAMModule]
    ) -> SafetyTestResult:
        start_time = time.time()
        warnings: List[str] = []
        recommendations: List[str] = []

        limits = self._get_voltage_limits(modules)
        vddq = config.voltages.vddq
        vpp = config.voltages.vpp

        score = 1.0

        if vddq > limits["max_vddq"]:
            score *= 0.2
            warnings.append(f"VDDQ {vddq}V exceeds safe limit {limits['max_vddq']}V")
        elif vddq > limits["recommended_vddq"]:
            score *= 0.7
            warnings.append(
                f"VDDQ {vddq}V above recommended {limits['recommended_vddq']}V"
            )

        if vpp > limits["max_vpp"]:
            score *= 0.3
            warnings.append(f"VPP {vpp}V exceeds safe limit {limits['max_vpp']}V")

        stability = self._simulate_voltage_stability(vddq, vpp)
        score *= stability

        if stability < 0.8:
            warnings.append("Voltage stability concerns detected")
            recommendations.append("Consider lower voltages for better stability")

        if score >= 0.9:
            level = SafetyLevel.VERIFIED_SAFE
        elif score >= 0.7:
            level = SafetyLevel.SAFE
        elif score >= 0.5:
            level = SafetyLevel.CAUTION
        elif score >= 0.3:
            level = SafetyLevel.UNSAFE
        else:
            level = SafetyLevel.CRITICAL_UNSAFE

        if level in (SafetyLevel.SAFE, SafetyLevel.VERIFIED_SAFE):
            recommendations.append("Voltage parameters are within safe limits")

        return SafetyTestResult(
            test_type=TestType.VOLTAGE_VALIDATION,
            safety_level=level,
            score=score,
            warnings=warnings,
            recommendations=recommendations,
            details={"vddq": vddq, "vpp": vpp, "limits": limits, "stability": stability},
            execution_time=time.time() - start_time,
        )

    def _test_timing_safety(
        self, config: DDR5Configuration, modules: List[DetectedRAMModule]
    ) -> SafetyTestResult:
        start_time = time.time()
        warnings: List[str] = []
        recommendations: List[str] = []

        timings = config.timings
        frequency = config.frequency

        score = 1.0

        timing_violations = self._check_timing_relationships(timings, frequency)
        if timing_violations:
            score *= 0.4
            warnings.extend(timing_violations)

        hardware_compatibility = self._check_hardware_timing_limits(timings, modules)
        score *= hardware_compatibility

        stability_prediction = self._predict_timing_stability(timings, frequency)
        score *= stability_prediction

        if stability_prediction < 0.8:
            warnings.append("Aggressive timings may cause instability")
            recommendations.append("Consider more conservative timing values")

        if score >= 0.9:
            level = SafetyLevel.VERIFIED_SAFE
        elif score >= 0.7:
            level = SafetyLevel.SAFE
        elif score >= 0.5:
            level = SafetyLevel.CAUTION
        elif score >= 0.3:
            level = SafetyLevel.UNSAFE
        else:
            level = SafetyLevel.CRITICAL_UNSAFE

        return SafetyTestResult(
            test_type=TestType.TIMING_VALIDATION,
            safety_level=level,
            score=score,
            warnings=warnings,
            recommendations=recommendations,
            details={
                "timing_violations": timing_violations,
                "hardware_compatibility": hardware_compatibility,
                "stability_prediction": stability_prediction,
            },
            execution_time=time.time() - start_time,
        )

    def _test_thermal_safety(
        self, config: DDR5Configuration, modules: List[DetectedRAMModule]
    ) -> SafetyTestResult:
        start_time = time.time()
        warnings: List[str] = []
        recommendations: List[str] = []

        thermal_load = self._simulate_thermal_load(config, modules)
        score = 1.0

        for module in modules:
            manufacturer = module.manufacturer
            limits = self.hardware_limits.get(manufacturer, self.hardware_limits["Generic"])
            if thermal_load > limits["thermal_limit"]:
                score *= 0.2
                warnings.append(
                    f"Thermal load {thermal_load:.1f}°C exceeds limit {limits['thermal_limit']}°C"
                )
            elif thermal_load > limits["thermal_limit"] - 10:
                score *= 0.7
                warnings.append("Thermal load approaching limit")

        if thermal_load > 70:
            recommendations.append("Consider improved cooling before live tuning")

        if score >= 0.9:
            level = SafetyLevel.VERIFIED_SAFE
        elif score >= 0.7:
            level = SafetyLevel.SAFE
        elif score >= 0.5:
            level = SafetyLevel.CAUTION
        else:
            level = SafetyLevel.UNSAFE

        return SafetyTestResult(
            test_type=TestType.THERMAL_SIMULATION,
            safety_level=level,
            score=score,
            warnings=warnings,
            recommendations=recommendations,
            details={"thermal_load": thermal_load},
            execution_time=time.time() - start_time,
        )

    def _test_stability_prediction(
        self, config: DDR5Configuration, _modules: List[DetectedRAMModule]
    ) -> SafetyTestResult:
        start_time = time.time()
        warnings: List[str] = []
        recommendations: List[str] = []

        stability_score = self._predict_system_stability(config, _modules)

        if stability_score < 0.6:
            warnings.append("Low stability prediction - high risk of crashes")
            recommendations.append("Use more conservative settings")
        elif stability_score < 0.8:
            warnings.append("Moderate stability concerns")
            recommendations.append("Extensive testing recommended")

        if stability_score >= 0.95:
            level = SafetyLevel.VERIFIED_SAFE
        elif stability_score >= 0.85:
            level = SafetyLevel.SAFE
        elif stability_score >= 0.7:
            level = SafetyLevel.CAUTION
        elif stability_score >= 0.5:
            level = SafetyLevel.UNSAFE
        else:
            level = SafetyLevel.CRITICAL_UNSAFE

        return SafetyTestResult(
            test_type=TestType.STABILITY_PREDICTION,
            safety_level=level,
            score=stability_score,
            warnings=warnings,
            recommendations=recommendations,
            details={"predicted_stability": stability_score},
            execution_time=time.time() - start_time,
        )

    def _test_rollback_capability(
        self, _config: DDR5Configuration, _modules: List[DetectedRAMModule]
    ) -> SafetyTestResult:
        start_time = time.time()
        warnings: List[str] = []
        recommendations: List[str] = []

        rollback_score = 1.0

        bios_rollback = self._check_bios_rollback_support()
        if not bios_rollback:
            rollback_score *= 0.5
            warnings.append("BIOS rollback capability uncertain")

        backup_capability = self._check_backup_capability()
        rollback_score *= backup_capability

        if backup_capability < 0.8:
            warnings.append("Limited backup/restore capability")
            recommendations.append("Manual BIOS reset may be required")

        level = SafetyLevel.SAFE if rollback_score >= 0.8 else SafetyLevel.CAUTION

        return SafetyTestResult(
            test_type=TestType.ROLLBACK_VERIFICATION,
            safety_level=level,
            score=rollback_score,
            warnings=warnings,
            recommendations=recommendations,
            details={"bios_rollback": bios_rollback, "backup_capability": backup_capability},
            execution_time=time.time() - start_time,
        )

    def _test_bios_compatibility(
        self, config: DDR5Configuration, _modules: List[DetectedRAMModule]
    ) -> SafetyTestResult:
        start_time = time.time()
        warnings: List[str] = []
        recommendations: List[str] = []

        compatibility_score = self._check_bios_compatibility(config)

        if compatibility_score < 0.7:
            warnings.append("BIOS may not support all requested parameters")
            recommendations.append("Verify BIOS version and capabilities")

        level = SafetyLevel.SAFE if compatibility_score >= 0.8 else SafetyLevel.CAUTION

        return SafetyTestResult(
            test_type=TestType.BIOS_COMPATIBILITY,
            safety_level=level,
            score=compatibility_score,
            warnings=warnings,
            recommendations=recommendations,
            details={"compatibility_score": compatibility_score},
            execution_time=time.time() - start_time,
        )

    def _test_hardware_limits(
        self, config: DDR5Configuration, modules: List[DetectedRAMModule]
    ) -> SafetyTestResult:
        start_time = time.time()
        warnings: List[str] = []
        recommendations: List[str] = []

        score = 1.0
        for module in modules:
            limits = self.hardware_limits.get(module.manufacturer, self.hardware_limits["Generic"])
            if config.frequency > limits["max_frequency"]:
                score *= 0.1
                warnings.append(
                    f"Frequency {config.frequency} exceeds hardware limit {limits['max_frequency']}"
                )
            if config.timings.cl < limits["min_cl"]:
                score *= 0.3
                warnings.append(f"CL {config.timings.cl} too aggressive")

        level = SafetyLevel.SAFE if score >= 0.8 else SafetyLevel.UNSAFE

        return SafetyTestResult(
            test_type=TestType.HARDWARE_LIMITS,
            safety_level=level,
            score=score,
            warnings=warnings,
            recommendations=recommendations,
            details={"hardware_limits_check": score},
            execution_time=time.time() - start_time,
        )

    # Helper methods
    def _get_voltage_limits(self, _modules: List[DetectedRAMModule]) -> Dict[str, float]:
        return {
            "max_vddq": 1.35,
            "recommended_vddq": 1.25,
            "max_vpp": 2.0,
            "recommended_vpp": 1.8,
        }

    def _simulate_voltage_stability(self, vddq: float, vpp: float) -> float:
        base = 1.0
        if vddq > 1.2:
            base *= (1.4 - vddq)
        if vpp > 1.9:
            base *= (2.1 - vpp)
        return max(0.0, min(1.0, base + random.uniform(-0.1, 0.05)))

    def _check_timing_relationships(self, timings: DDR5TimingParameters, _frequency: int) -> List[str]:
        violations: List[str] = []
        if timings.tras < (timings.trcd + timings.cl):
            violations.append("tRAS must be >= tRCD + CL")
        if timings.trc < (timings.tras + timings.trp):
            violations.append("tRC must be >= tRAS + tRP")
        if timings.cl < 20:
            violations.append("CL too aggressive for DDR5")
        return violations

    def _check_hardware_timing_limits(
        self, timings: DDR5TimingParameters, modules: List[DetectedRAMModule]
    ) -> float:
        compatibility = 1.0
        for module in modules:
            if "Kingston" in module.manufacturer:
                if timings.cl < 28:
                    compatibility *= 0.8
            else:
                if timings.cl < 32:
                    compatibility *= 0.6
        return compatibility

    def _predict_timing_stability(self, timings: DDR5TimingParameters, frequency: int) -> float:
        base = 1.0
        cl_ratio = timings.cl / (frequency / 100)
        if cl_ratio < 0.8:
            base *= 0.7
        return max(0.0, min(1.0, base + random.uniform(-0.1, 0.05)))

    def _simulate_thermal_load(
        self, config: DDR5Configuration, _modules: List[DetectedRAMModule]
    ) -> float:
        base_temp = 45.0
        freq_factor = (config.frequency - 4000) / 100 * 2.0
        voltage_factor = (config.voltages.vddq - 1.1) * 20.0
        total = base_temp + freq_factor + voltage_factor
        return max(30.0, total + random.uniform(-5, 10))

    def _predict_system_stability(
        self, config: DDR5Configuration, _modules: List[DetectedRAMModule]
    ) -> float:
        base = 0.9
        if config.frequency > 6000:
            base *= 0.85
        if config.voltages.vddq > 1.25:
            base *= 0.8
        if config.timings.cl < 32:
            base *= 0.9
        return max(0.0, min(1.0, base + random.uniform(-0.1, 0.1)))

    def _check_bios_rollback_support(self) -> bool:
        return random.choice([True, False])

    def _check_backup_capability(self) -> float:
        return random.uniform(0.6, 1.0)

    def _check_bios_compatibility(self, _config: DDR5Configuration) -> float:
        return random.uniform(0.7, 1.0)

    def _generate_safety_report(
        self, config: DDR5Configuration, modules: List[DetectedRAMModule]
    ) -> LiveTuningSafetyReport:
        scores = [r.score for r in self.test_results]
        overall_score = float(np.mean(scores)) if scores else 0.0

        critical = [r for r in self.test_results if r.safety_level == SafetyLevel.CRITICAL_UNSAFE]
        unsafe = [r for r in self.test_results if r.safety_level == SafetyLevel.UNSAFE]

        if critical:
            overall_level = SafetyLevel.CRITICAL_UNSAFE
        elif unsafe:
            overall_level = SafetyLevel.UNSAFE
        elif overall_score >= 0.9:
            overall_level = SafetyLevel.VERIFIED_SAFE
        elif overall_score >= 0.7:
            overall_level = SafetyLevel.SAFE
        else:
            overall_level = SafetyLevel.CAUTION

        all_recs: List[str] = []
        for r in self.test_results:
            all_recs.extend(r.recommendations)

        critical_warnings = [w for r in self.test_results for w in r.warnings if r.safety_level in (SafetyLevel.CRITICAL_UNSAFE, SafetyLevel.UNSAFE)]

        rollback_plan = {
            "method": "BIOS manual reset",
            "steps": "1. Power off, 2. Clear CMOS, 3. Reset to defaults",
            "estimated_time": "5-10 minutes",
            "risk_level": "Low",
        }

        if overall_level == SafetyLevel.CRITICAL_UNSAFE:
            risk = "CRITICAL - Do not proceed"
        elif overall_level == SafetyLevel.UNSAFE:
            risk = "HIGH - Not recommended"
        elif overall_level == SafetyLevel.CAUTION:
            risk = "MEDIUM - Proceed with caution"
        elif overall_level == SafetyLevel.SAFE:
            risk = "LOW - Generally safe"
        else:
            risk = "MINIMAL - Verified safe"

        return LiveTuningSafetyReport(
            overall_safety=overall_level,
            overall_score=overall_score,
            test_results=self.test_results,
            detected_hardware=modules,
            recommended_config=config if overall_level in (SafetyLevel.SAFE, SafetyLevel.VERIFIED_SAFE) else None,
            critical_warnings=critical_warnings,
            safety_recommendations=sorted(set(all_recs)),
            rollback_plan=rollback_plan,
            estimated_risk_level=risk,
        )


def quick_safety_check(config: DDR5Configuration, modules: List[DetectedRAMModule]) -> str:
    """Quick safety assessment label for display."""
    validator = LiveTuningSafetyValidator()
    report = validator.run_comprehensive_safety_test(config, modules)
    if report.overall_safety == SafetyLevel.VERIFIED_SAFE:
        return "🟢 VERIFIED SAFE"
    elif report.overall_safety == SafetyLevel.SAFE:
        return "🟢 SAFE"
    elif report.overall_safety == SafetyLevel.CAUTION:
        return "🟡 CAUTION"
    elif report.overall_safety == SafetyLevel.UNSAFE:
        return "🔴 UNSAFE"
    else:
        return "⚠️ CRITICAL"
