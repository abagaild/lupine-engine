"""
Scene Instance Performance Monitor for Lupine Engine
Provides real-time monitoring and optimization of scene instances
"""

import time
import threading
import gc
from typing import Dict, Any, List, Optional, Callable
from collections import deque
from dataclasses import dataclass
from .scene_instance import SceneInstance

# Optional psutil import for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. System monitoring will be limited.")


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time"""
    timestamp: float
    memory_usage: int
    cpu_usage: float
    active_instances: int
    pooled_instances: int
    load_time_avg: float
    gc_collections: int


class SceneInstanceMonitor:
    """
    Real-time performance monitor for scene instances with features:
    - Memory usage tracking
    - CPU performance monitoring
    - Load time analysis
    - Automatic optimization suggestions
    - Performance alerts
    - Historical data collection
    """
    
    def __init__(self, instance_manager):
        self.instance_manager = instance_manager
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self.monitor_interval = 1.0  # seconds
        
        # Performance data
        self.performance_history: deque = deque(maxlen=1000)  # Last 1000 snapshots
        self.load_times: deque = deque(maxlen=100)  # Last 100 load times
        self.memory_samples: deque = deque(maxlen=500)  # Last 500 memory samples
        
        # Thresholds and alerts
        self.memory_threshold = 100 * 1024 * 1024  # 100MB
        self.load_time_threshold = 1.0  # 1 second
        self.cpu_threshold = 80.0  # 80%
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        
        # Optimization recommendations
        self.optimization_suggestions: List[str] = []
        
        # Performance baselines
        self.baseline_metrics: Dict[str, float] = {}

    def start_monitoring(self) -> None:
        """Start real-time performance monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Scene instance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("Scene instance monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect performance snapshot
                snapshot = self._collect_performance_snapshot()
                self.performance_history.append(snapshot)
                
                # Check for alerts
                self._check_performance_alerts(snapshot)
                
                # Update optimization suggestions
                self._update_optimization_suggestions()
                
                # Sleep until next interval
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(self.monitor_interval)

    def _collect_performance_snapshot(self) -> PerformanceSnapshot:
        """Collect current performance metrics"""
        # Get system metrics (with fallback if psutil not available)
        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                process = psutil.Process()
                memory_usage = process.memory_info().rss
                cpu_usage = process.cpu_percent()
            except Exception:
                memory_usage = 0
                cpu_usage = 0.0
        else:
            # Fallback metrics
            memory_usage = 0
            cpu_usage = 0.0
        
        # Get instance manager statistics
        stats = self.instance_manager.get_statistics()
        active_instances = stats.get('total_active_instances', 0)
        pooled_instances = stats.get('total_pooled_instances', 0)
        
        # Calculate average load time
        load_time_avg = sum(self.load_times) / len(self.load_times) if self.load_times else 0.0
        
        # Get garbage collection stats
        gc_stats = gc.get_stats()
        gc_collections = sum(stat.get('collections', 0) for stat in gc_stats)
        
        return PerformanceSnapshot(
            timestamp=time.time(),
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            active_instances=active_instances,
            pooled_instances=pooled_instances,
            load_time_avg=load_time_avg,
            gc_collections=gc_collections
        )

    def _check_performance_alerts(self, snapshot: PerformanceSnapshot) -> None:
        """Check for performance issues and trigger alerts"""
        alerts = []
        
        # Memory usage alert
        if snapshot.memory_usage > self.memory_threshold:
            alerts.append({
                'type': 'memory',
                'severity': 'high',
                'message': f"High memory usage: {snapshot.memory_usage / 1024 / 1024:.1f}MB",
                'suggestion': "Consider reducing instance pool sizes or clearing unused instances"
            })
        
        # CPU usage alert
        if snapshot.cpu_usage > self.cpu_threshold:
            alerts.append({
                'type': 'cpu',
                'severity': 'medium',
                'message': f"High CPU usage: {snapshot.cpu_usage:.1f}%",
                'suggestion': "Check for performance bottlenecks in scene loading"
            })
        
        # Load time alert
        if snapshot.load_time_avg > self.load_time_threshold:
            alerts.append({
                'type': 'load_time',
                'severity': 'medium',
                'message': f"Slow load times: {snapshot.load_time_avg:.2f}s average",
                'suggestion': "Consider preloading frequently used scenes"
            })
        
        # Too many active instances
        if snapshot.active_instances > 100:
            alerts.append({
                'type': 'instance_count',
                'severity': 'low',
                'message': f"Many active instances: {snapshot.active_instances}",
                'suggestion': "Consider using instance pooling more aggressively"
            })
        
        # Trigger alert callbacks
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    print(f"Error in alert callback: {e}")

    def _update_optimization_suggestions(self) -> None:
        """Update optimization suggestions based on current performance"""
        self.optimization_suggestions.clear()
        
        if len(self.performance_history) < 10:
            return
        
        recent_snapshots = list(self.performance_history)[-10:]
        
        # Analyze memory trend
        memory_trend = self._calculate_trend([s.memory_usage for s in recent_snapshots])
        if memory_trend > 0.1:  # Increasing memory usage
            self.optimization_suggestions.append(
                "Memory usage is increasing. Consider running garbage collection or optimizing instance pools."
            )
        
        # Analyze load time trend
        load_time_trend = self._calculate_trend([s.load_time_avg for s in recent_snapshots])
        if load_time_trend > 0.1:  # Increasing load times
            self.optimization_suggestions.append(
                "Load times are increasing. Consider preloading scenes or optimizing scene complexity."
            )
        
        # Check instance pool efficiency
        avg_active = sum(s.active_instances for s in recent_snapshots) / len(recent_snapshots)
        avg_pooled = sum(s.pooled_instances for s in recent_snapshots) / len(recent_snapshots)
        
        if avg_pooled > avg_active * 2:
            self.optimization_suggestions.append(
                "Instance pools may be oversized. Consider reducing pool sizes to save memory."
            )
        elif avg_pooled < avg_active * 0.1:
            self.optimization_suggestions.append(
                "Instance pools may be undersized. Consider increasing pool sizes for better performance."
            )

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate the trend (slope) of a series of values"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        # Linear regression slope
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        return slope

    def record_load_time(self, load_time: float) -> None:
        """Record a scene load time for analysis"""
        self.load_times.append(load_time)

    def record_memory_sample(self, memory_usage: int) -> None:
        """Record a memory usage sample"""
        self.memory_samples.append(memory_usage)

    def add_alert_callback(self, callback: Callable) -> None:
        """Add a callback for performance alerts"""
        self.alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable) -> None:
        """Remove an alert callback"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance metrics"""
        if not self.performance_history:
            return {}
        
        recent_snapshots = list(self.performance_history)[-10:]
        latest = self.performance_history[-1]
        
        return {
            'current_memory_mb': latest.memory_usage / 1024 / 1024,
            'current_cpu_percent': latest.cpu_usage,
            'current_active_instances': latest.active_instances,
            'current_pooled_instances': latest.pooled_instances,
            'average_load_time': latest.load_time_avg,
            'memory_trend': self._calculate_trend([s.memory_usage for s in recent_snapshots]),
            'cpu_trend': self._calculate_trend([s.cpu_usage for s in recent_snapshots]),
            'optimization_suggestions': self.optimization_suggestions.copy(),
            'monitoring_duration': time.time() - self.performance_history[0].timestamp if self.performance_history else 0
        }

    def get_historical_data(self, metric: str, duration_seconds: int = 300) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric"""
        cutoff_time = time.time() - duration_seconds
        
        data = []
        for snapshot in self.performance_history:
            if snapshot.timestamp >= cutoff_time:
                value = getattr(snapshot, metric, None)
                if value is not None:
                    data.append({
                        'timestamp': snapshot.timestamp,
                        'value': value
                    })
        
        return data

    def set_baseline_metrics(self) -> None:
        """Set current performance as baseline for comparison"""
        if not self.performance_history:
            return
        
        latest = self.performance_history[-1]
        self.baseline_metrics = {
            'memory_usage': latest.memory_usage,
            'cpu_usage': latest.cpu_usage,
            'load_time_avg': latest.load_time_avg,
            'active_instances': latest.active_instances
        }
        
        print("Performance baseline set")

    def compare_to_baseline(self) -> Dict[str, float]:
        """Compare current performance to baseline"""
        if not self.baseline_metrics or not self.performance_history:
            return {}
        
        latest = self.performance_history[-1]
        comparison = {}
        
        for metric, baseline_value in self.baseline_metrics.items():
            current_value = getattr(latest, metric, 0)
            if baseline_value > 0:
                change_percent = ((current_value - baseline_value) / baseline_value) * 100
                comparison[metric] = change_percent
        
        return comparison

    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report"""
        if not self.performance_history:
            return "No performance data available"
        
        summary = self.get_performance_summary()
        baseline_comparison = self.compare_to_baseline()
        
        report = "Scene Instance Performance Report\n"
        report += "=" * 40 + "\n\n"
        
        # Current metrics
        report += "Current Performance:\n"
        report += f"  Memory Usage: {summary.get('current_memory_mb', 0):.1f} MB\n"
        report += f"  CPU Usage: {summary.get('current_cpu_percent', 0):.1f}%\n"
        report += f"  Active Instances: {summary.get('current_active_instances', 0)}\n"
        report += f"  Pooled Instances: {summary.get('current_pooled_instances', 0)}\n"
        report += f"  Average Load Time: {summary.get('average_load_time', 0):.3f}s\n\n"
        
        # Trends
        report += "Performance Trends:\n"
        memory_trend = summary.get('memory_trend', 0)
        cpu_trend = summary.get('cpu_trend', 0)
        report += f"  Memory Trend: {'↑' if memory_trend > 0 else '↓' if memory_trend < 0 else '→'}\n"
        report += f"  CPU Trend: {'↑' if cpu_trend > 0 else '↓' if cpu_trend < 0 else '→'}\n\n"
        
        # Baseline comparison
        if baseline_comparison:
            report += "Comparison to Baseline:\n"
            for metric, change in baseline_comparison.items():
                direction = "↑" if change > 0 else "↓" if change < 0 else "→"
                report += f"  {metric}: {direction} {abs(change):.1f}%\n"
            report += "\n"
        
        # Optimization suggestions
        suggestions = summary.get('optimization_suggestions', [])
        if suggestions:
            report += "Optimization Suggestions:\n"
            for i, suggestion in enumerate(suggestions, 1):
                report += f"  {i}. {suggestion}\n"
        else:
            report += "No optimization suggestions at this time.\n"
        
        return report

    def export_performance_data(self, filepath: str) -> bool:
        """Export performance data to a file"""
        try:
            import json
            
            data = {
                'export_timestamp': time.time(),
                'performance_history': [
                    {
                        'timestamp': s.timestamp,
                        'memory_usage': s.memory_usage,
                        'cpu_usage': s.cpu_usage,
                        'active_instances': s.active_instances,
                        'pooled_instances': s.pooled_instances,
                        'load_time_avg': s.load_time_avg,
                        'gc_collections': s.gc_collections
                    }
                    for s in self.performance_history
                ],
                'baseline_metrics': self.baseline_metrics,
                'optimization_suggestions': self.optimization_suggestions
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error exporting performance data: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up monitoring resources"""
        self.stop_monitoring()
        self.performance_history.clear()
        self.load_times.clear()
        self.memory_samples.clear()
        self.alert_callbacks.clear()
        self.optimization_suggestions.clear()
