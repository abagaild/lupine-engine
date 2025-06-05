#!/usr/bin/env python3
"""
Test script for the Lupine Engine Animation System
Verifies that all components work correctly
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all animation system imports work correctly"""
    print("Testing animation system imports...")
    
    try:
        # Test core animation imports
        from core.animation import Animation, AnimationLibrary
        print("✓ Animation and AnimationLibrary imported successfully")
        
        from core.animation import AnimationTrack, PropertyTrack, TransformTrack, ColorTrack, SpriteFrameTrack
        print("✓ Animation track classes imported successfully")
        
        from core.animation import Tween, TweenType, EaseType
        print("✓ Tween system imported successfully")
        
        from core.animation import (
            create_simple_tween_animation, create_fade_animation, create_move_animation,
            create_scale_animation, create_rotation_animation, create_sprite_frame_animation,
            create_bounce_animation, create_pulse_animation, get_preset_animation,
            get_preset_animation_names
        )
        print("✓ Animation utility functions imported successfully")
        
        # Test AnimationPlayer node
        from nodes.base.AnimationPlayer import AnimationPlayer
        print("✓ AnimationPlayer node imported successfully")
        
        # Test UI animation presets
        from core.ui.ui_prefabs import get_ui_animation_presets, get_ui_animation_preset_names
        print("✓ UI animation presets imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False


def test_animation_creation():
    """Test creating and manipulating animations"""
    print("\nTesting animation creation...")
    
    try:
        from core.animation import Animation, AnimationLibrary
        from core.animation.animation_track import PropertyTrack, TransformTrack
        from core.animation.tween import TweenType, EaseType
        
        # Create a simple animation
        animation = Animation("test_animation")
        animation.length = 2.0
        animation.loop = True
        
        # Add a transform track
        position_track = TransformTrack("TestSprite", "position")
        position_track.add_keyframe(0.0, [0, 0], TweenType.LINEAR, EaseType.IN_OUT)
        position_track.add_keyframe(1.0, [100, 100], TweenType.SMOOTH, EaseType.IN_OUT)
        position_track.add_keyframe(2.0, [0, 0], TweenType.LINEAR, EaseType.IN_OUT)
        
        animation.add_track(position_track)
        
        # Test animation library
        library = AnimationLibrary()
        library.add_animation(animation)
        
        # Test serialization
        anim_dict = animation.to_dict()
        restored_animation = Animation.from_dict(anim_dict)
        
        print("✓ Animation creation and serialization successful")
        print(f"  - Animation name: {restored_animation.name}")
        print(f"  - Animation length: {restored_animation.length}")
        print(f"  - Number of tracks: {len(restored_animation.tracks)}")
        print(f"  - Track keyframes: {len(restored_animation.tracks[0].keyframes)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Animation creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preset_animations():
    """Test preset animation creation"""
    print("\nTesting preset animations...")
    
    try:
        from core.animation import (
            create_fade_animation, create_move_animation, create_bounce_animation,
            get_preset_animation_names
        )
        
        # Test fade animation
        fade_anim = create_fade_animation("fade_in", "TestSprite", True, 1.0)
        print(f"✓ Fade animation created: {fade_anim.name}")
        
        # Test move animation
        move_anim = create_move_animation("move", "TestSprite", [0, 0], [100, 100], 2.0)
        print(f"✓ Move animation created: {move_anim.name}")
        
        # Test bounce animation
        bounce_anim = create_bounce_animation("bounce", "TestSprite")
        print(f"✓ Bounce animation created: {bounce_anim.name}")
        
        # Test preset names
        preset_names = get_preset_animation_names()
        print(f"✓ Available presets: {', '.join(preset_names)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Preset animation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_animation_player():
    """Test AnimationPlayer node functionality"""
    print("\nTesting AnimationPlayer node...")
    
    try:
        from nodes.base.AnimationPlayer import AnimationPlayer
        from core.animation import Animation
        from core.animation.animation_track import TransformTrack
        
        # Create animation player
        player = AnimationPlayer("TestPlayer")
        
        # Create a test animation
        animation = Animation("test_move")
        animation.length = 1.0
        
        track = TransformTrack("TestSprite", "position")
        track.add_keyframe(0.0, [0, 0])
        track.add_keyframe(1.0, [100, 0])
        animation.add_track(track)
        
        # Add animation to player
        player.add_animation(animation)
        
        # Test playback methods
        player.play("test_move")
        print(f"✓ Animation playing: {player.is_playing()}")
        print(f"✓ Current animation: {player.get_current_animation_name()}")
        
        player.pause()
        player.resume()
        player.stop()
        
        # Test serialization
        player_dict = player.to_dict()
        restored_player = AnimationPlayer.from_dict(player_dict)
        
        print("✓ AnimationPlayer functionality test successful")
        print(f"  - Player name: {restored_player.name}")
        print(f"  - Animation count: {len(restored_player.get_animation_names())}")
        
        return True
        
    except Exception as e:
        print(f"✗ AnimationPlayer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_animation_presets():
    """Test UI animation presets"""
    print("\nTesting UI animation presets...")
    
    try:
        from core.ui.ui_prefabs import get_ui_animation_presets, get_ui_animation_preset_names
        
        # Get all presets
        presets = get_ui_animation_presets()
        preset_names = get_ui_animation_preset_names()
        
        print(f"✓ Found {len(presets)} UI animation presets")
        print(f"✓ Preset names: {', '.join(preset_names[:5])}...")  # Show first 5
        
        # Test a specific preset
        bounce_preset = presets.get("bounce")
        if bounce_preset:
            print(f"✓ Bounce preset: {bounce_preset['description']}")
            print(f"  - Duration: {bounce_preset['duration']}s")
            print(f"  - Properties: {list(bounce_preset['properties'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"✗ UI animation presets test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tween_system():
    """Test the tween interpolation system"""
    print("\nTesting tween system...")
    
    try:
        from core.animation.tween import Tween, TweenType, EaseType
        
        # Test basic interpolation
        result = Tween.interpolate(0.0, 100.0, 0.5, TweenType.LINEAR, EaseType.IN_OUT)
        print(f"✓ Linear interpolation (0.5): {result}")
        
        # Test vector interpolation
        start_pos = [0, 0]
        end_pos = [100, 200]
        result_pos = Tween.interpolate(start_pos, end_pos, 0.5, TweenType.SMOOTH, EaseType.IN_OUT)
        print(f"✓ Vector interpolation (0.5): {result_pos}")
        
        # Test color interpolation
        start_color = [1.0, 0.0, 0.0, 1.0]  # Red
        end_color = [0.0, 1.0, 0.0, 1.0]    # Green
        result_color = Tween.interpolate(start_color, end_color, 0.5, TweenType.LINEAR, EaseType.IN_OUT)
        print(f"✓ Color interpolation (0.5): {result_color}")
        
        # Test different tween types
        for tween_type in [TweenType.LINEAR, TweenType.SMOOTH, TweenType.BOUNCE]:
            result = Tween.interpolate(0.0, 1.0, 0.5, tween_type, EaseType.IN_OUT)
            print(f"✓ {tween_type.value} interpolation: {result:.3f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Tween system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all animation system tests"""
    print("=" * 60)
    print("LUPINE ENGINE ANIMATION SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_tween_system,
        test_animation_creation,
        test_preset_animations,
        test_animation_player,
        test_ui_animation_presets
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("Test failed!")
        except Exception as e:
            print(f"Test crashed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Animation system is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
