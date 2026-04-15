"""
Advanced Hyperparameter Optimization for DDR5 AI using Optuna
Automatically finds optimal hyperparameters for AI models.
"""

import optuna
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import logging
from pathlib import Path

from src.ddr5_models import DDR5Configuration, DDR5TimingParameters, DDR5VoltageParameters
from src.ddr5_simulator import DDR5Simulator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HyperparameterOptimizer:
    """Advanced hyperparameter optimization using Optuna."""
    
    def __init__(self, simulator: DDR5Simulator = None):
        """Initialize the hyperparameter optimizer."""
        self.simulator = simulator or DDR5Simulator()
        self.study = None
        self.best_params = {}
        self.optimization_history = []
        
        # Model registry
        self.model_registry = {
            'random_forest': self._create_random_forest,
            'gradient_boost': self._create_gradient_boost,
            'neural_network': self._create_neural_network,
            'gaussian_process': self._create_gaussian_process
        }
        
        # Training data cache
        self.X_train = None
        self.y_performance = None
        self.y_stability = None
        
    def generate_training_data(self, n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate comprehensive training data for hyperparameter optimization."""
        logger.info(f"Generating {n_samples} training samples...")
        
        configurations = []
        performance_scores = []
        stability_scores = []
        
        # Generate diverse DDR5 configurations
        for _ in range(n_samples):
            # Random frequency selection
            frequency = np.random.choice([4000, 4400, 4800, 5200, 5600, 6000, 6400, 6800, 7200])
            
            # Generate timing parameters with realistic relationships
            base_cl = np.random.randint(14, 48)
            cl = base_cl
            trcd = base_cl + np.random.randint(0, 8)
            trp = base_cl + np.random.randint(0, 8)
            tras = max(trcd + cl, np.random.randint(32, 120))
            trc = tras + trp + np.random.randint(0, 20)
            
            # Generate voltage parameters
            vddq = np.random.uniform(1.0, 1.4)
            vpp = np.random.uniform(1.7, 2.0)
            vdd1 = np.random.uniform(1.7, 2.0)
            vdd2 = np.random.uniform(1.0, 1.4)
            vddq_tx = np.random.uniform(1.0, 1.4)
            
            try:
                # Create configuration
                config = DDR5Configuration(
                    frequency=frequency,
                    timings=DDR5TimingParameters(
                        cl=cl, trcd=trcd, trp=trp, tras=tras, trc=trc
                    ),
                    voltages=DDR5VoltageParameters(
                        vddq=vddq, vpp=vpp, vdd1=vdd1, vdd2=vdd2, vddq_tx=vddq_tx
                    )
                )
                
                # Simulate performance
                result = self.simulator.simulate_performance(config)
                
                # Convert to feature vector
                feature_vector = self._config_to_features(config)
                configurations.append(feature_vector)
                performance_scores.append(result['bandwidth'])
                stability_scores.append(result['stability'])
                
            except Exception as e:
                logger.warning(f"Skipping invalid configuration: {e}")
                continue
        
        X = np.array(configurations)
        y_perf = np.array(performance_scores)
        y_stab = np.array(stability_scores)
        
        logger.info(f"Generated {len(X)} valid training samples")
        return X, y_perf, y_stab
    
    def _config_to_features(self, config: DDR5Configuration) -> List[float]:
        """Convert DDR5 configuration to feature vector."""
        return [
            config.frequency,
            config.timings.cl,
            config.timings.trcd,
            config.timings.trp,
            config.timings.tras,
            config.timings.trc,
            config.voltages.vddq,
            config.voltages.vpp,
            config.voltages.vdd1,
            config.voltages.vdd2,
            config.voltages.vddq_tx,
            # Derived features
            config.timings.tras / config.timings.cl,  # tRAS/CL ratio
            config.timings.trc / config.timings.tras,  # tRC/tRAS ratio
            config.voltages.vddq * config.frequency / 1000,  # Power proxy
            config.timings.cl / (config.frequency / 1000),  # Timing efficiency
        ]
    
    def _create_random_forest(self, trial: optuna.Trial) -> RandomForestRegressor:
        """Create Random Forest with trial parameters."""
        return RandomForestRegressor(
            n_estimators=trial.suggest_int('rf_n_estimators', 50, 500),
            max_depth=trial.suggest_int('rf_max_depth', 3, 30),
            min_samples_split=trial.suggest_int('rf_min_samples_split', 2, 20),
            min_samples_leaf=trial.suggest_int('rf_min_samples_leaf', 1, 10),
            max_features=trial.suggest_categorical('rf_max_features', ['sqrt', 'log2', None]),
            random_state=42,
            n_jobs=-1
        )
    
    def _create_gradient_boost(self, trial: optuna.Trial) -> GradientBoostingRegressor:
        """Create Gradient Boosting with trial parameters."""
        return GradientBoostingRegressor(
            n_estimators=trial.suggest_int('gb_n_estimators', 50, 300),
            learning_rate=trial.suggest_float('gb_learning_rate', 0.01, 0.3),
            max_depth=trial.suggest_int('gb_max_depth', 3, 15),
            min_samples_split=trial.suggest_int('gb_min_samples_split', 2, 20),
            min_samples_leaf=trial.suggest_int('gb_min_samples_leaf', 1, 10),
            subsample=trial.suggest_float('gb_subsample', 0.6, 1.0),
            random_state=42
        )
    
    def _create_neural_network(self, trial: optuna.Trial) -> MLPRegressor:
        """Create Neural Network with trial parameters."""
        n_layers = trial.suggest_int('mlp_n_layers', 1, 4)
        layer_sizes = []
        
        for i in range(n_layers):
            layer_size = trial.suggest_int(f'mlp_layer_{i}_size', 16, 256)
            layer_sizes.append(layer_size)
        
        return MLPRegressor(
            hidden_layer_sizes=tuple(layer_sizes),
            learning_rate_init=trial.suggest_float('mlp_learning_rate', 0.0001, 0.1),
            alpha=trial.suggest_float('mlp_alpha', 0.0001, 0.1),
            batch_size=trial.suggest_categorical('mlp_batch_size', [32, 64, 128, 256]),
            max_iter=trial.suggest_int('mlp_max_iter', 200, 1000),
            random_state=42
        )
    
    def _create_gaussian_process(self, trial: optuna.Trial) -> GaussianProcessRegressor:
        """Create Gaussian Process with trial parameters."""
        kernel_type = trial.suggest_categorical('gp_kernel', ['rbf', 'matern'])
        length_scale = trial.suggest_float('gp_length_scale', 0.1, 10.0)
        
        if kernel_type == 'rbf':
            kernel = RBF(length_scale=length_scale)
        else:
            nu = trial.suggest_categorical('gp_nu', [0.5, 1.5, 2.5])
            kernel = Matern(length_scale=length_scale, nu=nu)
        
        return GaussianProcessRegressor(
            kernel=kernel,
            alpha=trial.suggest_float('gp_alpha', 1e-12, 1e-2),
            random_state=42
        )
    
    def optimize_model_hyperparameters(
        self, 
        model_type: str, 
        target: str = 'performance',
        n_trials: int = 100,
        timeout: Optional[int] = 3600
    ) -> Dict[str, Any]:
        """Optimize hyperparameters for a specific model type."""
        
        if self.X_train is None:
            self.X_train, self.y_performance, self.y_stability = self.generate_training_data()
        
        # Select target variable
        y_target = self.y_performance if target == 'performance' else self.y_stability
        
        def objective(trial):
            """Objective function for hyperparameter optimization."""
            try:
                # Create model with trial parameters
                model = self.model_registry[model_type](trial)
                
                # Perform cross-validation
                cv_scores = cross_val_score(
                    model, self.X_train, y_target, 
                    cv=5, scoring='neg_mean_squared_error', n_jobs=-1
                )
                
                # Return negative MSE (to maximize)
                return -np.mean(cv_scores)
                
            except Exception as e:
                logger.warning(f"Trial failed: {e}")
                return float('inf')
        
        # Create study
        study_name = f"{model_type}_{target}_optimization"
        self.study = optuna.create_study(
            direction='minimize',
            study_name=study_name,
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        
        logger.info(f"Starting hyperparameter optimization for {model_type} ({target})")
        logger.info(f"Running {n_trials} trials with timeout {timeout}s")
        
        # Optimize
        self.study.optimize(objective, n_trials=n_trials, timeout=timeout)
        
        # Store best parameters
        self.best_params[f"{model_type}_{target}"] = self.study.best_params
        
        # Create best model
        best_model = self.model_registry[model_type](self.study.best_trial)
        best_model.fit(self.X_train, y_target)
        
        # Evaluate best model
        y_pred = best_model.predict(self.X_train)
        mse = mean_squared_error(y_target, y_pred)
        r2 = r2_score(y_target, y_pred)
        
        results = {
            'model_type': model_type,
            'target': target,
            'best_params': self.study.best_params,
            'best_score': self.study.best_value,
            'mse': mse,
            'r2_score': r2,
            'n_trials': len(self.study.trials),
            'best_model': best_model
        }
        
        logger.info(f"Optimization complete for {model_type} ({target})")
        logger.info(f"Best score: {self.study.best_value:.4f}")
        logger.info(f"R² score: {r2:.4f}")
        
        return results
    
    def optimize_all_models(
        self, 
        n_trials_per_model: int = 50,
        timeout_per_model: int = 1800
    ) -> Dict[str, Dict[str, Any]]:
        """Optimize hyperparameters for all model types and targets."""
        
        results = {}
        
        # Generate training data once
        if self.X_train is None:
            self.X_train, self.y_performance, self.y_stability = self.generate_training_data()
        
        # Optimize each model for each target
        for model_type in self.model_registry.keys():
            for target in ['performance', 'stability']:
                try:
                    logger.info(f"Optimizing {model_type} for {target}...")
                    result = self.optimize_model_hyperparameters(
                        model_type=model_type,
                        target=target,
                        n_trials=n_trials_per_model,
                        timeout=timeout_per_model
                    )
                    results[f"{model_type}_{target}"] = result
                    
                except Exception as e:
                    logger.error(f"Failed to optimize {model_type} for {target}: {e}")
                    continue
        
        return results
    
    def save_optimization_results(self, results: Dict[str, Any], output_dir: str = "optimization_results"):
        """Save optimization results to disk."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save best parameters
        best_params_file = output_path / "best_hyperparameters.json"
        import json
        with open(best_params_file, 'w') as f:
            # Convert to JSON-serializable format
            json_params = {}
            for key, value in self.best_params.items():
                json_params[key] = value
            json.dump(json_params, f, indent=2)
        
        # Save models
        for key, result in results.items():
            if 'best_model' in result:
                model_file = output_path / f"{key}_model.pkl"
                joblib.dump(result['best_model'], model_file)
        
        # Save optimization history
        history_file = output_path / "optimization_history.json"
        with open(history_file, 'w') as f:
            json.dump(self.optimization_history, f, indent=2)
        
        logger.info(f"Optimization results saved to {output_path}")
    
    def load_optimized_models(self, input_dir: str = "optimization_results") -> Dict[str, Any]:
        """Load previously optimized models."""
        input_path = Path(input_dir)
        
        if not input_path.exists():
            logger.warning(f"Optimization results directory {input_path} not found")
            return {}
        
        models = {}
        
        # Load best parameters
        best_params_file = input_path / "best_hyperparameters.json"
        if best_params_file.exists():
            import json
            with open(best_params_file, 'r') as f:
                self.best_params = json.load(f)
        
        # Load models
        for model_file in input_path.glob("*_model.pkl"):
            model_name = model_file.stem.replace('_model', '')
            models[model_name] = joblib.load(model_file)
        
        logger.info(f"Loaded {len(models)} optimized models from {input_path}")
        return models
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """Get insights from the optimization process."""
        if not self.study:
            return {"error": "No optimization study available"}
        
        insights = {
            'best_params': self.study.best_params,
            'best_value': self.study.best_value,
            'n_trials': len(self.study.trials),
            'pruned_trials': len([t for t in self.study.trials if t.state == optuna.trial.TrialState.PRUNED]),
            'failed_trials': len([t for t in self.study.trials if t.state == optuna.trial.TrialState.FAIL]),
            'parameter_importance': optuna.importance.get_param_importances(self.study)
        }
        
        return insights
    
    def create_optimization_report(self, results: Dict[str, Any]) -> str:
        """Create a comprehensive optimization report."""
        report = []
        report.append("# DDR5 AI Hyperparameter Optimization Report")
        report.append("=" * 50)
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"- Total models optimized: {len(results)}")
        report.append(f"- Training samples: {len(self.X_train) if self.X_train is not None else 'N/A'}")
        report.append("")
        
        # Results for each model
        for model_key, result in results.items():
            report.append(f"## {model_key.replace('_', ' ').title()}")
            report.append(f"- Best Score: {result.get('best_score', 'N/A'):.4f}")
            report.append(f"- R² Score: {result.get('r2_score', 'N/A'):.4f}")
            report.append(f"- MSE: {result.get('mse', 'N/A'):.4f}")
            report.append(f"- Trials: {result.get('n_trials', 'N/A')}")
            
            # Best parameters
            report.append("### Best Parameters:")
            for param, value in result.get('best_params', {}).items():
                report.append(f"- {param}: {value}")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        best_performance = min(results.values(), key=lambda x: x.get('best_score', float('inf')))
        report.append(f"- Best performing model: {best_performance.get('model_type', 'Unknown')}")
        report.append(f"- Recommended for production use")
        report.append("")
        
        return "\n".join(report)


# Example usage and testing
if __name__ == "__main__":
    # Initialize optimizer
    optimizer = HyperparameterOptimizer()
    
    # Optimize a single model (for testing)
    results = optimizer.optimize_model_hyperparameters(
        model_type='random_forest',
        target='performance',
        n_trials=10  # Reduced for testing
    )
    
    print("Optimization Results:")
    print(f"Best score: {results['best_score']:.4f}")
    print(f"R² score: {results['r2_score']:.4f}")
    print(f"Best parameters: {results['best_params']}")
