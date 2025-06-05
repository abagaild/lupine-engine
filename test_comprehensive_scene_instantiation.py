"""
Comprehensive test suite for the enhanced scene instantiation system
Tests all advanced features including performance monitoring, instance management, and optimization
"""

import time
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.project import LupineProject, set_current_project
from core.node_registry import DynamicNodeRegistry
from nodes.base.SceneInstance import SceneInstance
from core.scene.scene_instance_manager import SceneInstanceManager
from core.scene.scene_instance_monitor import SceneInstanceMonitor


def test_comprehensive_scene_instantiation():
    """Test the comprehensive scene instantiation system"""
    print("Testing Comprehensive Scene Instantiation System")
    print("=" * 60)
    
    # Setup project
    project_path = Path(__file__).parent
    project = LupineProject(str(project_path))
    project.load_project()
    set_current_project(project)
    
    # Initialize components
    registry = DynamicNodeRegistry()
    registry.set_project_path(project_path)
    
    scene_manager = project.scene_manager
    instance_manager = SceneInstanceManager(scene_manager)
    monitor = SceneInstanceMonitor(instance_manager)
    
    print("\n1. Testing Basic Scene Instance Creation...")
    test_basic_instance_creation(instance_manager)
    
    print("\n2. Testing Instance Pooling...")
    test_instance_pooling(instance_manager)
    
    print("\n3. Testing Batch Operations...")
    test_batch_operations(instance_manager)
    
    print("\n4. Testing Performance Monitoring...")
    test_performance_monitoring(monitor, instance_manager)
    
    print("\n5. Testing Advanced Scene Features...")
    test_advanced_scene_features(scene_manager)
    
    print("\n6. Testing Memory Optimization...")
    test_memory_optimization(instance_manager, monitor)
    
    print("\n7. Testing Instance Variants...")
    test_instance_variants(instance_manager)
    
    print("\n8. Testing Dependency Management...")
    test_dependency_management(scene_manager)
    
    # Cleanup
    monitor.cleanup()
    instance_manager.cleanup_all()
    
    print("\n" + "=" * 60)
    print("Comprehensive scene instantiation test completed!")


def test_basic_instance_creation(instance_manager):
    """Test basic instance creation with the enhanced manager"""
    print("   Creating scene instances...")
    
    # Create instances
    instance1 = instance_manager.create_instance("scenes/TestPlayer.scene", "Player1")
    instance2 = instance_manager.create_instance("scenes/TestPlayer.scene", "Player2")
    
    if instance1 and instance2:
        print(f"   ✓ Created instances: {instance1.name}, {instance2.name}")
        print(f"   ✓ Instance IDs: {instance1.instance_id[:8]}..., {instance2.instance_id[:8]}...")
        
        # Test instance tracking
        stats = instance_manager.get_statistics()
        print(f"   ✓ Active instances: {stats['total_active_instances']}")
        print(f"   ✓ Scenes with instances: {stats['scenes_with_instances']}")
    else:
        print("   ✗ Failed to create instances")


def test_instance_pooling(instance_manager):
    """Test instance pooling functionality"""
    print("   Testing instance pooling...")
    
    # Create instance pool
    scene_path = "scenes/TestPlayer.scene"
    success = instance_manager.create_instance_pool(scene_path, 3)
    
    if success:
        print("   ✓ Created instance pool")
        
        # Get instances from pool
        pooled1 = instance_manager.create_instance(scene_path, "PooledPlayer1", use_pool=True)
        pooled2 = instance_manager.create_instance(scene_path, "PooledPlayer2", use_pool=True)
        
        if pooled1 and pooled2:
            print(f"   ✓ Retrieved pooled instances: {pooled1.name}, {pooled2.name}")
            
            # Return to pool
            instance_manager.destroy_instance(pooled1, return_to_pool=True)
            print("   ✓ Returned instance to pool")
            
            # Get pool statistics
            stats = instance_manager.get_statistics()
            pool_stats = stats.get('pool_statistics', {})
            if scene_path in pool_stats:
                print(f"   ✓ Pool size: {pool_stats[scene_path]['pool_size']}")
        else:
            print("   ✗ Failed to get pooled instances")
    else:
        print("   ✗ Failed to create instance pool")


def test_batch_operations(instance_manager):
    """Test batch instance operations"""
    print("   Testing batch operations...")
    
    # Prepare batch requests
    requests = [
        {"scene_path": "scenes/TestPlayer.scene", "instance_name": "BatchPlayer1"},
        {"scene_path": "scenes/TestPlayer.scene", "instance_name": "BatchPlayer2"},
        {"scene_path": "scenes/AudioTest.scene", "instance_name": "BatchAudio1"},
    ]
    
    # Create instances in batch
    start_time = time.time()
    instances = instance_manager.batch_create_instances(requests)
    batch_time = time.time() - start_time
    
    successful_instances = [inst for inst in instances if inst is not None]
    print(f"   ✓ Batch created {len(successful_instances)}/{len(requests)} instances in {batch_time:.3f}s")
    
    if successful_instances:
        # Batch destroy
        destroyed_count = instance_manager.batch_destroy_instances(successful_instances)
        print(f"   ✓ Batch destroyed {destroyed_count} instances")


def test_performance_monitoring(monitor, instance_manager):
    """Test performance monitoring functionality"""
    print("   Testing performance monitoring...")
    
    # Start monitoring
    monitor.start_monitoring()
    print("   ✓ Started performance monitoring")
    
    # Create some load
    instances = []
    for i in range(5):
        instance = instance_manager.create_instance("scenes/TestPlayer.scene", f"PerfTest{i}")
        if instance:
            instances.append(instance)
    
    # Wait for monitoring data
    time.sleep(2)
    
    # Get performance summary
    summary = monitor.get_performance_summary()
    if summary:
        print(f"   ✓ Memory usage: {summary.get('current_memory_mb', 0):.1f} MB")
        print(f"   ✓ Active instances: {summary.get('current_active_instances', 0)}")
        print(f"   ✓ Monitoring duration: {summary.get('monitoring_duration', 0):.1f}s")
        
        # Check for optimization suggestions
        suggestions = summary.get('optimization_suggestions', [])
        if suggestions:
            print(f"   ✓ Got {len(suggestions)} optimization suggestions")
    
    # Set baseline and compare
    monitor.set_baseline_metrics()
    time.sleep(1)
    
    comparison = monitor.compare_to_baseline()
    if comparison:
        print("   ✓ Baseline comparison available")
    
    # Generate performance report
    report = monitor.generate_performance_report()
    if report:
        print("   ✓ Generated performance report")
    
    # Cleanup test instances
    for instance in instances:
        instance_manager.destroy_instance(instance)
    
    monitor.stop_monitoring()
    print("   ✓ Stopped performance monitoring")


def test_advanced_scene_features(scene_manager):
    """Test advanced scene management features"""
    print("   Testing advanced scene features...")
    
    # Test scene preloading
    success = scene_manager.preload_scene("scenes/TestPlayer.scene")
    if success:
        print("   ✓ Scene preloading works")
    
    # Test scene metadata loading
    metadata = scene_manager._load_scene_metadata("scenes/TestPlayer.scene")
    if metadata:
        print(f"   ✓ Scene metadata: {metadata.get('node_count', 0)} nodes, complexity {metadata.get('complexity_score', 0)}")
    
    # Test dependency graph building
    scene_manager.build_dependency_graph()
    print("   ✓ Built dependency graph")
    
    # Test dependency validation
    issues = scene_manager.validate_scene_dependencies()
    print(f"   ✓ Dependency validation: {len(issues)} issues found")
    
    # Test available scenes
    available_scenes = scene_manager.get_available_scenes()
    print(f"   ✓ Found {len(available_scenes)} available scenes")


def test_memory_optimization(instance_manager, monitor):
    """Test memory optimization features"""
    print("   Testing memory optimization...")
    
    # Create many instances to trigger optimization
    instances = []
    for i in range(10):
        instance = instance_manager.create_instance("scenes/TestPlayer.scene", f"OptTest{i}")
        if instance:
            instances.append(instance)
    
    # Get initial memory stats
    initial_stats = instance_manager.get_statistics()
    initial_memory = initial_stats.get('memory_usage', {}).get('total_memory_bytes', 0)
    
    # Run optimization
    optimization_report = instance_manager.optimize_pools()
    print(f"   ✓ Pool optimization: {optimization_report}")
    
    # Test scene manager optimization
    scene_optimization = instance_manager.scene_manager.optimize_memory_usage()
    print(f"   ✓ Scene optimization: {scene_optimization}")
    
    # Cleanup
    for instance in instances:
        instance_manager.destroy_instance(instance)


def test_instance_variants(instance_manager):
    """Test scene instance variants"""
    print("   Testing instance variants...")
    
    # Create base instance
    base_instance = instance_manager.create_instance("scenes/TestPlayer.scene", "BasePlayer")
    
    if base_instance:
        # Add some property overrides
        base_instance.property_overrides["Player/position"] = [100, 200]
        base_instance.property_overrides["Player/scale"] = [2.0, 2.0]
        
        # Create variant
        variant = base_instance.create_variant("VariantPlayer")
        
        if variant:
            print(f"   ✓ Created variant: {variant.name}")
            print(f"   ✓ Variant has {len(variant.property_overrides)} overrides")
            
            # Test override diff
            diff = variant.get_override_diff()
            print(f"   ✓ Override diff has {len(diff)} node differences")
            
            # Test integrity validation
            issues = variant.validate_integrity()
            print(f"   ✓ Variant validation: {len(issues)} issues")
        
        # Cleanup
        instance_manager.destroy_instance(base_instance)
        if variant:
            instance_manager.destroy_instance(variant)


def test_dependency_management(scene_manager):
    """Test scene dependency management"""
    print("   Testing dependency management...")
    
    # Get available scenes
    scenes = scene_manager.get_available_scenes()
    
    if scenes:
        test_scene = scenes[0]
        
        # Get scene dependencies
        dependencies = scene_manager.dependency_graph.get(test_scene, set())
        print(f"   ✓ Scene {test_scene} has {len(dependencies)} dependencies")
        
        # Get dependents
        dependents = scene_manager.get_scene_dependents(test_scene)
        print(f"   ✓ Scene {test_scene} has {len(dependents)} dependents")
        
        # Test circular dependency detection
        has_circular = scene_manager._has_circular_dependency(test_scene)
        print(f"   ✓ Circular dependency check: {'Found' if has_circular else 'None'}")


if __name__ == "__main__":
    test_comprehensive_scene_instantiation()
