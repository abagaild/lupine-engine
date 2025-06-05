"""
Advanced Scene Instance Manager for Lupine Engine
Provides comprehensive management of scene instances with optimization and monitoring
"""

import time
import threading
from typing import Dict, Any, List, Optional, Set, Callable
from pathlib import Path
from .scene_instance import SceneInstance
from .base_node import Node


class SceneInstanceManager:
    """
    Advanced manager for scene instances with features like:
    - Instance pooling and reuse
    - Batch operations
    - Performance monitoring
    - Memory optimization
    - Dependency tracking
    - Auto-reload on file changes
    """
    
    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        
        # Instance tracking
        self.active_instances: Dict[str, SceneInstance] = {}  # instance_id -> instance
        self.instances_by_scene: Dict[str, Set[str]] = {}  # scene_path -> set of instance_ids
        self.instance_pools: Dict[str, List[SceneInstance]] = {}  # scene_path -> pooled instances
        
        # Performance monitoring
        self.performance_metrics: Dict[str, Any] = {}
        self.memory_usage: Dict[str, Any] = {}
        self.load_times: Dict[str, float] = {}
        
        # File watching for auto-reload
        self.file_watchers: Dict[str, Any] = {}
        self.auto_reload_enabled: bool = True
        
        # Batch operation queue
        self.batch_queue: List[Dict[str, Any]] = []
        self.batch_processing: bool = False
        
        # Event callbacks
        self.instance_created_callbacks: List[Callable] = []
        self.instance_destroyed_callbacks: List[Callable] = []
        self.scene_reloaded_callbacks: List[Callable] = []

    # ========== INSTANCE LIFECYCLE MANAGEMENT ==========
    
    def create_instance(self, scene_path: str, instance_name: Optional[str] = None, 
                       use_pool: bool = True) -> Optional[SceneInstance]:
        """Create a new scene instance with advanced options"""
        start_time = time.time()
        
        try:
            # Try to get from pool first if enabled
            if use_pool and scene_path in self.instance_pools and self.instance_pools[scene_path]:
                instance = self.instance_pools[scene_path].pop()
                instance._is_active = True
                if instance_name:
                    instance.name = instance_name
                
                # Update tracking
                self._register_instance(instance)
                
                # Record performance
                self.load_times[instance.instance_id] = time.time() - start_time
                
                return instance
            
            # Create new instance
            instance = self.scene_manager.instantiate_scene(scene_path, instance_name)
            if not instance:
                return None
            
            # Register and track
            self._register_instance(instance)
            
            # Record performance
            self.load_times[instance.instance_id] = time.time() - start_time
            
            # Notify callbacks
            for callback in self.instance_created_callbacks:
                try:
                    callback(instance)
                except Exception as e:
                    print(f"Error in instance created callback: {e}")
            
            return instance
            
        except Exception as e:
            print(f"Error creating scene instance for {scene_path}: {e}")
            return None

    def destroy_instance(self, instance: SceneInstance, return_to_pool: bool = True) -> bool:
        """Destroy a scene instance with pooling option"""
        try:
            instance_id = instance.instance_id
            scene_path = instance.scene_path
            
            # Try to return to pool if enabled and instance supports it
            if (return_to_pool and hasattr(instance, '_is_pooled') and 
                instance._is_pooled and scene_path):
                
                # Reset instance state
                instance.reset_to_default_state()
                instance._is_active = False
                
                # Return to pool
                if scene_path not in self.instance_pools:
                    self.instance_pools[scene_path] = []
                
                # Limit pool size
                if len(self.instance_pools[scene_path]) < 10:
                    self.instance_pools[scene_path].append(instance)
                    self._unregister_instance(instance)
                    return True
            
            # Actually destroy the instance
            self._unregister_instance(instance)
            
            # Notify callbacks
            for callback in self.instance_destroyed_callbacks:
                try:
                    callback(instance)
                except Exception as e:
                    print(f"Error in instance destroyed callback: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error destroying scene instance: {e}")
            return False

    def _register_instance(self, instance: SceneInstance) -> None:
        """Register an instance for tracking"""
        instance_id = instance.instance_id
        scene_path = instance.scene_path
        
        # Add to active instances
        self.active_instances[instance_id] = instance
        
        # Add to scene tracking
        if scene_path not in self.instances_by_scene:
            self.instances_by_scene[scene_path] = set()
        self.instances_by_scene[scene_path].add(instance_id)
        
        # Initialize performance tracking
        if scene_path not in self.performance_metrics:
            self.performance_metrics[scene_path] = {
                'total_created': 0,
                'currently_active': 0,
                'average_load_time': 0.0,
                'memory_usage': 0
            }
        
        self.performance_metrics[scene_path]['total_created'] += 1
        self.performance_metrics[scene_path]['currently_active'] += 1

    def _unregister_instance(self, instance: SceneInstance) -> None:
        """Unregister an instance from tracking"""
        instance_id = instance.instance_id
        scene_path = instance.scene_path
        
        # Remove from active instances
        if instance_id in self.active_instances:
            del self.active_instances[instance_id]
        
        # Remove from scene tracking
        if scene_path in self.instances_by_scene:
            self.instances_by_scene[scene_path].discard(instance_id)
            if not self.instances_by_scene[scene_path]:
                del self.instances_by_scene[scene_path]
        
        # Update performance metrics
        if scene_path in self.performance_metrics:
            self.performance_metrics[scene_path]['currently_active'] -= 1

    # ========== BATCH OPERATIONS ==========
    
    def batch_create_instances(self, requests: List[Dict[str, Any]]) -> List[Optional[SceneInstance]]:
        """Create multiple instances efficiently in batch"""
        results = []
        
        # Group by scene path for optimization
        grouped = {}
        for i, request in enumerate(requests):
            scene_path = request['scene_path']
            if scene_path not in grouped:
                grouped[scene_path] = []
            grouped[scene_path].append((i, request))
        
        # Pre-allocate results
        results = [None] * len(requests)
        
        # Process each scene type
        for scene_path, scene_requests in grouped.items():
            # Preload scene once
            scene = self.scene_manager.load_scene(scene_path)
            if not scene:
                continue
            
            # Create instances
            for original_index, request in scene_requests:
                instance_name = request.get('instance_name')
                use_pool = request.get('use_pool', True)
                
                instance = self.create_instance(scene_path, instance_name, use_pool)
                results[original_index] = instance
        
        return results

    def batch_destroy_instances(self, instances: List[SceneInstance], 
                              return_to_pool: bool = True) -> int:
        """Destroy multiple instances efficiently"""
        destroyed_count = 0
        
        for instance in instances:
            if self.destroy_instance(instance, return_to_pool):
                destroyed_count += 1
        
        return destroyed_count

    # ========== POOL MANAGEMENT ==========
    
    def create_instance_pool(self, scene_path: str, pool_size: int = 5) -> bool:
        """Create a pool of pre-instantiated instances"""
        try:
            if scene_path not in self.instance_pools:
                self.instance_pools[scene_path] = []
            
            # Create pooled instances
            for i in range(pool_size):
                instance = self.scene_manager.instantiate_scene(
                    scene_path, f"pooled_{scene_path}_{i}"
                )
                if instance:
                    instance._is_pooled = True
                    instance._is_active = False
                    self.instance_pools[scene_path].append(instance)
            
            return True
            
        except Exception as e:
            print(f"Error creating instance pool for {scene_path}: {e}")
            return False

    def warm_up_pools(self, scene_priorities: Dict[str, int]) -> None:
        """Warm up instance pools based on priority"""
        for scene_path, priority in sorted(scene_priorities.items(), 
                                         key=lambda x: x[1], reverse=True):
            pool_size = max(2, min(priority // 10, 10))  # 2-10 instances based on priority
            self.create_instance_pool(scene_path, pool_size)

    def optimize_pools(self) -> Dict[str, Any]:
        """Optimize instance pools by removing unused instances"""
        optimization_report = {
            'pools_optimized': 0,
            'instances_removed': 0,
            'memory_freed': 0
        }
        
        for scene_path, pool in list(self.instance_pools.items()):
            # Remove excess instances (keep max 5 per pool)
            if len(pool) > 5:
                excess = pool[5:]
                self.instance_pools[scene_path] = pool[:5]
                optimization_report['instances_removed'] += len(excess)
            
            # Remove empty pools
            if not self.instance_pools[scene_path]:
                del self.instance_pools[scene_path]
                optimization_report['pools_optimized'] += 1
        
        return optimization_report

    # ========== MONITORING AND STATISTICS ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about scene instances"""
        stats = {
            'total_active_instances': len(self.active_instances),
            'total_pooled_instances': sum(len(pool) for pool in self.instance_pools.values()),
            'scenes_with_instances': len(self.instances_by_scene),
            'performance_metrics': self.performance_metrics.copy(),
            'memory_usage': self._calculate_memory_usage(),
            'pool_statistics': self._get_pool_statistics()
        }
        
        return stats

    def _calculate_memory_usage(self) -> Dict[str, Any]:
        """Calculate memory usage of all instances"""
        import sys
        
        total_memory = 0
        scene_memory = {}
        
        for instance in self.active_instances.values():
            instance_memory = sys.getsizeof(instance)
            total_memory += instance_memory
            
            scene_path = instance.scene_path
            if scene_path not in scene_memory:
                scene_memory[scene_path] = 0
            scene_memory[scene_path] += instance_memory
        
        return {
            'total_memory_bytes': total_memory,
            'memory_by_scene': scene_memory,
            'average_instance_memory': total_memory / max(len(self.active_instances), 1)
        }

    def _get_pool_statistics(self) -> Dict[str, Any]:
        """Get statistics about instance pools"""
        pool_stats = {}
        
        for scene_path, pool in self.instance_pools.items():
            pool_stats[scene_path] = {
                'pool_size': len(pool),
                'active_instances': len(self.instances_by_scene.get(scene_path, set())),
                'total_created': self.performance_metrics.get(scene_path, {}).get('total_created', 0)
            }
        
        return pool_stats

    # ========== EVENT SYSTEM ==========
    
    def add_instance_created_callback(self, callback: Callable) -> None:
        """Add callback for when instances are created"""
        self.instance_created_callbacks.append(callback)

    def add_instance_destroyed_callback(self, callback: Callable) -> None:
        """Add callback for when instances are destroyed"""
        self.instance_destroyed_callbacks.append(callback)

    def add_scene_reloaded_callback(self, callback: Callable) -> None:
        """Add callback for when scenes are reloaded"""
        self.scene_reloaded_callbacks.append(callback)

    # ========== UTILITY METHODS ==========
    
    def find_instances_by_scene(self, scene_path: str) -> List[SceneInstance]:
        """Find all active instances of a specific scene"""
        if scene_path not in self.instances_by_scene:
            return []
        
        instances = []
        for instance_id in self.instances_by_scene[scene_path]:
            if instance_id in self.active_instances:
                instances.append(self.active_instances[instance_id])
        
        return instances

    def get_instance_by_id(self, instance_id: str) -> Optional[SceneInstance]:
        """Get an instance by its ID"""
        return self.active_instances.get(instance_id)

    def cleanup_all(self) -> None:
        """Clean up all instances and pools"""
        # Destroy all active instances
        for instance in list(self.active_instances.values()):
            self.destroy_instance(instance, return_to_pool=False)
        
        # Clear pools
        self.instance_pools.clear()
        
        # Clear tracking
        self.instances_by_scene.clear()
        self.performance_metrics.clear()
        self.memory_usage.clear()
        self.load_times.clear()
