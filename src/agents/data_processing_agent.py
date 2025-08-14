
from typing import Dict, Any, List, Union, Optional
import logging
import statistics
from datetime import datetime
import json

from .base_agent import BaseWorkerAgent
from ..core.models import AgentCapability, Task, TaskStatus


logger = logging.getLogger(__name__)


class DataProcessingAgent(BaseWorkerAgent):
    
    def __init__(self, name: str = "DataProcessor"):
        capabilities = [AgentCapability.DATA_PROCESSING, AgentCapability.ANALYSIS]
        super().__init__(name, capabilities, "data_processor")
        
        # Agent-specific configuration
        self.max_data_points = 100000  # Maximum number of data points to process
        self.precision = 4  # Decimal precision for calculations
        
        self.logger.info(f"Data Processing Agent '{name}' initialized")
    
    def execute(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = datetime.utcnow()
        
        try:
            # Extract data from task parameters
            data = task.parameters.get('data', [])
            operation = task.parameters.get('operation', 'calculate_statistics')
            
            # Try to get data from context if not in task parameters
            if not data:
                data = context.get('data', [])
            
            if not data:
                raise ValueError("No data provided for processing")
            
            # Convert data to numerical format if needed
            processed_data = self._prepare_data(data)
            
            if not processed_data:
                raise ValueError("No valid numerical data found")
            
            if len(processed_data) > self.max_data_points:
                raise ValueError(f"Data size exceeds maximum limit of {self.max_data_points} points")
            
            self.logger.info(f"Processing {operation} on {len(processed_data)} data points")
            
            # Perform the requested operation
            if operation == 'calculate_statistics':
                result = self._calculate_statistics(processed_data, task.parameters)
            elif operation == 'aggregate':
                result = self._aggregate_data(processed_data, task.parameters)
            elif operation == 'filter':
                result = self._filter_data(processed_data, task.parameters)
            elif operation == 'transform':
                result = self._transform_data(processed_data, task.parameters)
            elif operation == 'analyze_distribution':
                result = self._analyze_distribution(processed_data, task.parameters)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Prepare the final result
            final_result = {
                'operation': operation,
                'input_data_count': len(processed_data),
                'result': result,
                'execution_time': execution_time,
                'agent_id': self.agent_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Data processing completed in {execution_time:.2f}s")
            return final_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Data processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'error': error_msg,
                'execution_time': execution_time,
                'agent_id': self.agent_id,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _prepare_data(self, data: Any) -> List[float]:
        processed_data = []
        
        # Handle different data formats
        if isinstance(data, str):
            # Try to parse as JSON first
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                # Try to split as comma-separated values
                data = [x.strip() for x in data.split(',')]
        
        if isinstance(data, (list, tuple)):
            for item in data:
                try:
                    # Handle nested structures
                    if isinstance(item, (list, tuple)):
                        processed_data.extend(self._prepare_data(item))
                    elif isinstance(item, dict):
                        # Extract numerical values from dictionary
                        for value in item.values():
                            if isinstance(value, (int, float)):
                                processed_data.append(float(value))
                    else:
                        # Convert to float
                        processed_data.append(float(item))
                except (ValueError, TypeError):
                    # Skip non-numerical values
                    continue
        
        elif isinstance(data, dict):
            # Extract numerical values from dictionary
            for value in data.values():
                if isinstance(value, (int, float)):
                    processed_data.append(float(value))
                elif isinstance(value, (list, tuple)):
                    processed_data.extend(self._prepare_data(value))
        
        elif isinstance(data, (int, float)):
            processed_data.append(float(data))
        
        else:
            try:
                processed_data.append(float(data))
            except (ValueError, TypeError):
                pass
        
        return processed_data
    
    def _calculate_statistics(self, data: List[float], parameters: Dict[str, Any]) -> Dict[str, Any]:
        if not data:
            return {'error': 'No data to process'}
        
        result = {
            'count': len(data),
            'sum': round(sum(data), self.precision),
            'mean': round(statistics.mean(data), self.precision),
            'min': round(min(data), self.precision),
            'max': round(max(data), self.precision),
            'range': round(max(data) - min(data), self.precision)
        }
        
        # Add median and mode if there are enough data points
        if len(data) >= 1:
            result['median'] = round(statistics.median(data), self.precision)
        
        if len(data) >= 2:
            try:
                result['mode'] = round(statistics.mode(data), self.precision)
            except statistics.StatisticsError:
                # No unique mode
                result['mode'] = None
            
            # Calculate standard deviation and variance
            result['std_dev'] = round(statistics.stdev(data), self.precision)
            result['variance'] = round(statistics.variance(data), self.precision)
        
        # Calculate percentiles if requested
        if parameters.get('include_percentiles', False) and len(data) >= 4:
            sorted_data = sorted(data)
            result['percentiles'] = {
                'p25': round(statistics.quantiles(sorted_data, n=4)[0], self.precision),
                'p50': round(statistics.quantiles(sorted_data, n=4)[1], self.precision),
                'p75': round(statistics.quantiles(sorted_data, n=4)[2], self.precision)
            }
        
        return result
    
    def _aggregate_data(self, data: List[float], parameters: Dict[str, Any]) -> Dict[str, Any]:
        operations = parameters.get('operations', ['sum', 'mean', 'count'])
        
        result = {}
        
        for op in operations:
            if op == 'sum':
                result['sum'] = round(sum(data), self.precision)
            elif op == 'mean':
                result['mean'] = round(statistics.mean(data), self.precision)
            elif op == 'count':
                result['count'] = len(data)
            elif op == 'min':
                result['min'] = round(min(data), self.precision)
            elif op == 'max':
                result['max'] = round(max(data), self.precision)
            elif op == 'median':
                result['median'] = round(statistics.median(data), self.precision)
            elif op == 'std_dev' and len(data) >= 2:
                result['std_dev'] = round(statistics.stdev(data), self.precision)
        
        return result
    
    def _filter_data(self, data: List[float], parameters: Dict[str, Any]) -> Dict[str, Any]:
        condition = parameters.get('condition', 'greater_than')
        threshold = parameters.get('threshold', 0.0)
        
        if condition == 'greater_than':
            filtered_data = [x for x in data if x > threshold]
        elif condition == 'less_than':
            filtered_data = [x for x in data if x < threshold]
        elif condition == 'equal_to':
            filtered_data = [x for x in data if abs(x - threshold) < 1e-10]
        elif condition == 'between':
            min_val = parameters.get('min_value', min(data))
            max_val = parameters.get('max_value', max(data))
            filtered_data = [x for x in data if min_val <= x <= max_val]
        elif condition == 'outliers':
            # Remove outliers using IQR method
            if len(data) >= 4:
                sorted_data = sorted(data)
                q1 = statistics.quantiles(sorted_data, n=4)[0]
                q3 = statistics.quantiles(sorted_data, n=4)[2]
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                filtered_data = [x for x in data if lower_bound <= x <= upper_bound]
            else:
                filtered_data = data
        else:
            raise ValueError(f"Unsupported filter condition: {condition}")
        
        return {
            'filtered_data': filtered_data,
            'original_count': len(data),
            'filtered_count': len(filtered_data),
            'removed_count': len(data) - len(filtered_data),
            'condition': condition,
            'threshold': threshold
        }
    
    def _transform_data(self, data: List[float], parameters: Dict[str, Any]) -> Dict[str, Any]:
        transformation = parameters.get('transformation', 'normalize')
        
        if transformation == 'normalize':
            # Normalize to 0-1 range
            min_val = min(data)
            max_val = max(data)
            range_val = max_val - min_val
            
            if range_val == 0:
                transformed_data = [0.0] * len(data)
            else:
                transformed_data = [(x - min_val) / range_val for x in data]
        
        elif transformation == 'standardize':
            # Standardize to mean=0, std=1
            if len(data) >= 2:
                mean_val = statistics.mean(data)
                std_val = statistics.stdev(data)
                
                if std_val == 0:
                    transformed_data = [0.0] * len(data)
                else:
                    transformed_data = [(x - mean_val) / std_val for x in data]
            else:
                transformed_data = data
        
        elif transformation == 'logarithm':
            # Apply natural logarithm (only for positive values)
            import math
            transformed_data = []
            for x in data:
                if x > 0:
                    transformed_data.append(math.log(x))
                else:
                    transformed_data.append(float('nan'))
        
        elif transformation == 'square':
            transformed_data = [x ** 2 for x in data]
        
        elif transformation == 'sqrt':
            # Square root (only for non-negative values)
            import math
            transformed_data = []
            for x in data:
                if x >= 0:
                    transformed_data.append(math.sqrt(x))
                else:
                    transformed_data.append(float('nan'))
        
        else:
            raise ValueError(f"Unsupported transformation: {transformation}")
        
        # Round results
        transformed_data = [round(x, self.precision) if not (isinstance(x, float) and (x != x)) else x 
                          for x in transformed_data]
        
        return {
            'transformed_data': transformed_data,
            'transformation': transformation,
            'original_count': len(data),
            'valid_results': len([x for x in transformed_data if not (isinstance(x, float) and (x != x))])
        }
    
    def _analyze_distribution(self, data: List[float], parameters: Dict[str, Any]) -> Dict[str, Any]:
        num_bins = parameters.get('num_bins', 10)
        
        # Create histogram
        min_val = min(data)
        max_val = max(data)
        bin_width = (max_val - min_val) / num_bins if max_val != min_val else 1
        
        bins = []
        for i in range(num_bins):
            bin_start = min_val + i * bin_width
            bin_end = min_val + (i + 1) * bin_width
            bin_count = len([x for x in data if bin_start <= x < bin_end])
            
            # Include max value in the last bin
            if i == num_bins - 1:
                bin_count = len([x for x in data if bin_start <= x <= bin_end])
            
            bins.append({
                'range': f"[{round(bin_start, self.precision)}, {round(bin_end, self.precision)})",
                'count': bin_count,
                'frequency': round(bin_count / len(data), self.precision)
            })
        
        # Calculate basic distribution metrics
        mean_val = statistics.mean(data)
        median_val = statistics.median(data)
        
        # Skewness approximation (using Pearson's method)
        if len(data) >= 2:
            std_val = statistics.stdev(data)
            skewness = 3 * (mean_val - median_val) / std_val if std_val > 0 else 0
        else:
            skewness = 0
        
        return {
            'histogram': bins,
            'distribution_stats': {
                'mean': round(mean_val, self.precision),
                'median': round(median_val, self.precision),
                'skewness': round(skewness, self.precision),
                'range': round(max_val - min_val, self.precision)
            },
            'num_bins': num_bins
        }
    
    def can_handle_task(self, task: Task) -> bool:
        # Check if it's a data processing task
        if task.task_type in ['data_processing', 'calculate_statistics', 'analysis']:
            return True
        
        # Check if the task has data to process
        if 'data' in task.parameters:
            return True
        
        # Fall back to base capability checking
        return super().can_handle_task(task)
    
    def health_check(self) -> bool:
        try:
            # Basic health check from parent
            if not super().health_check():
                return False
            
            # Test basic data processing capability
            test_data = [1, 2, 3, 4, 5]
            test_result = self._calculate_statistics(test_data, {})
            
            if not test_result or 'mean' not in test_result or test_result['mean'] != 3.0:
                self.set_error("Data processing capability test failed")
                return False
            
            self.logger.debug(f"Data Processing Agent {self.name} health check passed")
            return True
            
        except Exception as e:
            self.set_error(f"Health check failed: {str(e)}")
            return False
