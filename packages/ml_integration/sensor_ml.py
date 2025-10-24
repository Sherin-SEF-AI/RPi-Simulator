"""
Machine Learning Models for Sensor Simulation

Uses ML to create realistic sensor behavior patterns based on real-world data.
"""

import numpy as np
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import pickle
import time


@dataclass
class SensorReading:
    """Single sensor reading with metadata"""
    timestamp: float
    value: float
    temperature: float
    humidity: float
    pressure: float
    metadata: Dict[str, Any] = None


class SensorMLModel(ABC):
    """Base class for sensor ML models"""
    
    def __init__(self, sensor_type: str):
        self.sensor_type = sensor_type
        self.model = None
        self.is_trained = False
        self.training_data: List[SensorReading] = []
        
    @abstractmethod
    def train(self, data: List[SensorReading]) -> bool:
        """Train the model on sensor data"""
        pass
        
    @abstractmethod
    def predict(self, input_features: Dict[str, float]) -> float:
        """Predict sensor value based on input features"""
        pass
        
    def save_model(self, filepath: str) -> bool:
        """Save trained model to file"""
        try:
            model_data = {
                "sensor_type": self.sensor_type,
                "model": self.model,
                "is_trained": self.is_trained,
                "training_samples": len(self.training_data)
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
            
    def load_model(self, filepath: str) -> bool:
        """Load trained model from file"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
                
            self.sensor_type = model_data["sensor_type"]
            self.model = model_data["model"]
            self.is_trained = model_data["is_trained"]
            
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False


class NoisePredictor(SensorMLModel):
    """Predicts sensor noise patterns using ML"""
    
    def __init__(self, sensor_type: str):
        super().__init__(sensor_type)
        self.noise_history: List[float] = []
        self.base_noise_level = 0.1
        
    def train(self, data: List[SensorReading]) -> bool:
        """Train noise prediction model"""
        if len(data) < 100:
            print("Insufficient training data for noise prediction")
            return False
            
        try:
            # Extract features and noise levels
            features = []
            noise_levels = []
            
            for i in range(1, len(data)):
                prev_reading = data[i-1]
                curr_reading = data[i]
                
                # Calculate noise as deviation from expected value
                expected_change = self._calculate_expected_change(prev_reading, curr_reading)
                actual_change = curr_reading.value - prev_reading.value
                noise = abs(actual_change - expected_change)
                
                # Features: temperature, humidity, time_delta, previous_noise
                feature_vector = [
                    curr_reading.temperature,
                    curr_reading.humidity,
                    curr_reading.timestamp - prev_reading.timestamp,
                    self.noise_history[-1] if self.noise_history else 0.1
                ]
                
                features.append(feature_vector)
                noise_levels.append(noise)
                self.noise_history.append(noise)
                
            # Simple linear regression model (would use sklearn in production)
            features_array = np.array(features)
            noise_array = np.array(noise_levels)
            
            # Calculate correlation coefficients
            self.model = {
                "feature_weights": np.corrcoef(features_array.T, noise_array)[:-1, -1],
                "base_noise": np.mean(noise_array),
                "noise_std": np.std(noise_array)
            }
            
            self.is_trained = True
            print(f"✅ Noise predictor trained on {len(data)} samples")
            return True
            
        except Exception as e:
            print(f"❌ Noise predictor training failed: {e}")
            return False
            
    def predict(self, input_features: Dict[str, float]) -> float:
        """Predict noise level based on environmental conditions"""
        if not self.is_trained:
            return self.base_noise_level
            
        try:
            # Extract features in same order as training
            feature_vector = [
                input_features.get("temperature", 25.0),
                input_features.get("humidity", 50.0),
                input_features.get("time_delta", 1.0),
                self.noise_history[-1] if self.noise_history else 0.1
            ]
            
            # Apply learned weights
            predicted_noise = self.model["base_noise"]
            for i, weight in enumerate(self.model["feature_weights"]):
                if i < len(feature_vector):
                    predicted_noise += weight * feature_vector[i] * 0.01  # Scale factor
                    
            # Add some randomness
            import random
            predicted_noise += random.gauss(0, self.model["noise_std"] * 0.1)
            
            return max(0, predicted_noise)
            
        except Exception as e:
            print(f"Noise prediction error: {e}")
            return self.base_noise_level
            
    def _calculate_expected_change(self, prev: SensorReading, curr: SensorReading) -> float:
        """Calculate expected sensor value change"""
        # Simple model - would be more sophisticated in production
        time_delta = curr.timestamp - prev.timestamp
        temp_effect = (curr.temperature - prev.temperature) * 0.1
        
        return temp_effect


class DriftPredictor(SensorMLModel):
    """Predicts long-term sensor drift using ML"""
    
    def __init__(self, sensor_type: str):
        super().__init__(sensor_type)
        self.drift_rate = 0.0  # units per hour
        self.drift_history: List[Tuple[float, float]] = []  # (time, cumulative_drift)
        
    def train(self, data: List[SensorReading]) -> bool:
        """Train drift prediction model"""
        if len(data) < 1000:  # Need lots of data for drift analysis
            print("Insufficient training data for drift prediction")
            return False
            
        try:
            # Analyze long-term trends
            timestamps = [r.timestamp for r in data]
            values = [r.value for r in data]
            
            # Calculate moving averages to remove noise
            window_size = 50
            smoothed_values = []
            
            for i in range(window_size, len(values)):
                avg = sum(values[i-window_size:i]) / window_size
                smoothed_values.append(avg)
                
            # Calculate drift rate (linear regression)
            if len(smoothed_values) > 100:
                x = np.array(timestamps[window_size:])
                y = np.array(smoothed_values)
                
                # Simple linear regression
                n = len(x)
                sum_x = np.sum(x)
                sum_y = np.sum(y)
                sum_xy = np.sum(x * y)
                sum_x2 = np.sum(x * x)
                
                # Calculate slope (drift rate)
                self.drift_rate = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                
                # Convert to units per hour
                self.drift_rate *= 3600  # seconds to hours
                
                self.model = {
                    "drift_rate": self.drift_rate,
                    "base_value": np.mean(values[:100]),  # Initial baseline
                    "confidence": min(1.0, len(data) / 10000)  # More data = higher confidence
                }
                
                self.is_trained = True
                print(f"✅ Drift predictor trained: {self.drift_rate:.6f} units/hour")
                return True
                
        except Exception as e:
            print(f"❌ Drift predictor training failed: {e}")
            
        return False
        
    def predict(self, input_features: Dict[str, float]) -> float:
        """Predict current drift amount"""
        if not self.is_trained:
            return 0.0
            
        try:
            current_time = input_features.get("timestamp", time.time())
            start_time = input_features.get("start_time", current_time)
            
            # Calculate elapsed time in hours
            elapsed_hours = (current_time - start_time) / 3600.0
            
            # Apply drift rate
            drift_amount = self.drift_rate * elapsed_hours
            
            # Add some non-linearity for realism
            if elapsed_hours > 24:  # After 24 hours, drift may accelerate
                acceleration_factor = 1 + (elapsed_hours - 24) * 0.01
                drift_amount *= acceleration_factor
                
            return drift_amount
            
        except Exception as e:
            print(f"Drift prediction error: {e}")
            return 0.0


class TemperatureCompensator(SensorMLModel):
    """ML model for temperature compensation of sensors"""
    
    def __init__(self, sensor_type: str):
        super().__init__(sensor_type)
        self.temp_coefficients = {}
        
    def train(self, data: List[SensorReading]) -> bool:
        """Train temperature compensation model"""
        if len(data) < 500:
            return False
            
        try:
            # Group readings by temperature ranges
            temp_ranges = {}
            
            for reading in data:
                temp_bucket = int(reading.temperature / 5) * 5  # 5°C buckets
                if temp_bucket not in temp_ranges:
                    temp_ranges[temp_bucket] = []
                temp_ranges[temp_bucket].append(reading.value)
                
            # Calculate average value for each temperature range
            temp_corrections = {}
            baseline_temp = 25  # Reference temperature
            baseline_value = None
            
            for temp, values in temp_ranges.items():
                avg_value = sum(values) / len(values)
                temp_corrections[temp] = avg_value
                
                if abs(temp - baseline_temp) < 3:  # Close to baseline
                    baseline_value = avg_value
                    
            if baseline_value is None:
                baseline_value = list(temp_corrections.values())[0]
                
            # Calculate temperature coefficients
            coefficients = {}
            for temp, value in temp_corrections.items():
                if len(temp_corrections[temp]) > 10:  # Enough samples
                    temp_diff = temp - baseline_temp
                    value_diff = value - baseline_value
                    
                    if temp_diff != 0:
                        coefficient = value_diff / temp_diff
                        coefficients[temp] = coefficient
                        
            self.model = {
                "baseline_temp": baseline_temp,
                "baseline_value": baseline_value,
                "coefficients": coefficients,
                "temp_ranges": temp_corrections
            }
            
            self.is_trained = True
            print(f"✅ Temperature compensator trained with {len(coefficients)} coefficients")
            return True
            
        except Exception as e:
            print(f"❌ Temperature compensator training failed: {e}")
            return False
            
    def predict(self, input_features: Dict[str, float]) -> float:
        """Predict temperature compensation offset"""
        if not self.is_trained:
            return 0.0
            
        try:
            current_temp = input_features.get("temperature", 25.0)
            baseline_temp = self.model["baseline_temp"]
            
            temp_diff = current_temp - baseline_temp
            
            # Find closest temperature coefficient
            closest_temp = min(self.model["coefficients"].keys(), 
                             key=lambda t: abs(t - current_temp))
            
            coefficient = self.model["coefficients"].get(closest_temp, 0.0)
            
            # Calculate compensation
            compensation = coefficient * temp_diff
            
            return compensation
            
        except Exception as e:
            print(f"Temperature compensation error: {e}")
            return 0.0


class SensorBehaviorLearner:
    """Learn and replicate real sensor behavior patterns"""
    
    def __init__(self):
        self.models: Dict[str, SensorMLModel] = {}
        self.training_data: Dict[str, List[SensorReading]] = {}
        
    def add_sensor_model(self, sensor_id: str, sensor_type: str) -> None:
        """Add a sensor for ML modeling"""
        self.models[sensor_id] = {
            "noise_predictor": NoisePredictor(sensor_type),
            "drift_predictor": DriftPredictor(sensor_type),
            "temp_compensator": TemperatureCompensator(sensor_type)
        }
        self.training_data[sensor_id] = []
        
    def add_training_data(self, sensor_id: str, reading: SensorReading) -> None:
        """Add training data for a sensor"""
        if sensor_id in self.training_data:
            self.training_data[sensor_id].append(reading)
            
            # Auto-train when we have enough data
            if len(self.training_data[sensor_id]) % 1000 == 0:
                self.train_sensor_models(sensor_id)
                
    def train_sensor_models(self, sensor_id: str) -> Dict[str, bool]:
        """Train all models for a sensor"""
        if sensor_id not in self.models or sensor_id not in self.training_data:
            return {}
            
        data = self.training_data[sensor_id]
        results = {}
        
        for model_name, model in self.models[sensor_id].items():
            results[model_name] = model.train(data)
            
        return results
        
    def get_enhanced_reading(self, sensor_id: str, base_value: float,
                           environment: Dict[str, float]) -> float:
        """Get ML-enhanced sensor reading"""
        if sensor_id not in self.models:
            return base_value
            
        enhanced_value = base_value
        
        try:
            models = self.models[sensor_id]
            
            # Apply noise prediction
            if models["noise_predictor"].is_trained:
                predicted_noise = models["noise_predictor"].predict(environment)
                import random
                noise = random.gauss(0, predicted_noise)
                enhanced_value += noise
                
            # Apply drift prediction
            if models["drift_predictor"].is_trained:
                drift = models["drift_predictor"].predict(environment)
                enhanced_value += drift
                
            # Apply temperature compensation
            if models["temp_compensator"].is_trained:
                temp_compensation = models["temp_compensator"].predict(environment)
                enhanced_value += temp_compensation
                
        except Exception as e:
            print(f"ML enhancement error: {e}")
            
        return enhanced_value
        
    def load_real_world_data(self, filepath: str) -> bool:
        """Load real-world sensor data for training"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            for sensor_id, readings in data.items():
                if sensor_id not in self.training_data:
                    self.training_data[sensor_id] = []
                    
                for reading_data in readings:
                    reading = SensorReading(
                        timestamp=reading_data["timestamp"],
                        value=reading_data["value"],
                        temperature=reading_data.get("temperature", 25.0),
                        humidity=reading_data.get("humidity", 50.0),
                        pressure=reading_data.get("pressure", 1013.25),
                        metadata=reading_data.get("metadata", {})
                    )
                    self.training_data[sensor_id].append(reading)
                    
            print(f"✅ Loaded real-world data for {len(data)} sensors")
            return True
            
        except Exception as e:
            print(f"❌ Error loading real-world data: {e}")
            return False
            
    def export_training_data(self, filepath: str) -> bool:
        """Export collected training data"""
        try:
            export_data = {}
            
            for sensor_id, readings in self.training_data.items():
                export_data[sensor_id] = [
                    {
                        "timestamp": r.timestamp,
                        "value": r.value,
                        "temperature": r.temperature,
                        "humidity": r.humidity,
                        "pressure": r.pressure,
                        "metadata": r.metadata or {}
                    }
                    for r in readings
                ]
                
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            print(f"✅ Exported training data to {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting training data: {e}")
            return False
            
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get statistics about trained models"""
        stats = {
            "sensors": len(self.models),
            "total_training_samples": sum(len(data) for data in self.training_data.values()),
            "trained_models": {}
        }
        
        for sensor_id, models in self.models.items():
            sensor_stats = {
                "training_samples": len(self.training_data.get(sensor_id, [])),
                "models_trained": {}
            }
            
            for model_name, model in models.items():
                sensor_stats["models_trained"][model_name] = model.is_trained
                
            stats["trained_models"][sensor_id] = sensor_stats
            
        return stats