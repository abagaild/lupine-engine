#!/usr/bin/env python3
"""
Test script for the Animation Editor
Verifies that the animation editor can be opened and used
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_animation_editor_import():
    """Test that the animation editor can be imported"""
    print("Testing animation editor import...")
    
    try:
        from editor.animation_editor import AnimationEditorWindow, AnimationEditor
        from core.project import LupineProject
        
        print("✓ Animation editor classes imported successfully")
        
        # Test creating project
        project = LupineProject(os.getcwd())
        print("✓ Project created successfully")
        
        # Test creating animation editor (without showing window)
        editor = AnimationEditor(project)
        print("✓ Animation editor widget created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Animation editor import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timeline_widget():
    """Test the timeline widget functionality"""
    print("\nTesting timeline widget...")
    
    try:
        from editor.animation_editor import TimelineWidget
        
        # Create timeline widget
        timeline = TimelineWidget()
        
        # Test basic functionality
        timeline.set_duration(5.0)
        timeline.set_current_time(2.5)
        timeline.set_zoom(150.0)
        
        # Test time/pixel conversion
        pixel_pos = timeline.time_to_pixel(2.5)
        time_pos = timeline.pixel_to_time(pixel_pos)
        
        print(f"✓ Timeline widget created and tested")
        print(f"  - Duration: {timeline.duration}s")
        print(f"  - Current time: {timeline.current_time}s")
        print(f"  - Zoom: {timeline.zoom} px/s")
        print(f"  - Time->Pixel->Time: {time_pos:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"✗ Timeline widget test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_track_widget():
    """Test the track widget functionality"""
    print("\nTesting track widget...")
    
    try:
        from editor.animation_editor import TrackWidget, TimelineWidget
        from core.animation.animation_track import TransformTrack
        
        # Create timeline and track
        timeline = TimelineWidget()
        timeline.set_duration(3.0)
        
        track = TransformTrack("TestNode", "position")
        track.add_keyframe(0.0, [0, 0])
        track.add_keyframe(1.5, [100, 50])
        track.add_keyframe(3.0, [200, 100])
        
        # Create track widget
        track_widget = TrackWidget(track, timeline)
        
        print(f"✓ Track widget created successfully")
        print(f"  - Track: {track.target_path}.{track.property_name}")
        print(f"  - Keyframes: {len(track.keyframes)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Track widget test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_animation_editor_functionality():
    """Test animation editor core functionality"""
    print("\nTesting animation editor functionality...")
    
    try:
        from editor.animation_editor import AnimationEditor
        from core.project import LupineProject
        from core.animation import Animation
        from core.animation.animation_track import TransformTrack
        
        # Create project and editor
        project = LupineProject(os.getcwd())
        editor = AnimationEditor(project)
        
        # Create test animation
        animation = Animation("test_animation")
        animation.length = 2.0
        animation.loop = True
        
        # Add track
        track = TransformTrack("TestSprite", "position")
        track.add_keyframe(0.0, [0, 0])
        track.add_keyframe(2.0, [100, 100])
        animation.add_track(track)
        
        # Set current animation
        editor.current_animation = animation
        editor.update_ui()
        
        print(f"✓ Animation editor functionality tested")
        print(f"  - Animation: {animation.name}")
        print(f"  - Length: {animation.length}s")
        print(f"  - Tracks: {len(animation.tracks)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Animation editor functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preset_integration():
    """Test UI animation preset integration"""
    print("\nTesting preset integration...")
    
    try:
        from core.ui.ui_prefabs import get_ui_animation_presets
        from core.animation import Animation
        from core.animation.animation_track import PropertyTrack
        
        # Get presets
        presets = get_ui_animation_presets()
        
        # Test creating animation from bounce preset
        bounce_preset = presets["bounce"]
        animation = Animation("bounce_test")
        animation.length = bounce_preset["duration"]
        
        # Create track from preset
        for prop_name, prop_data in bounce_preset["properties"].items():
            track = PropertyTrack("UIElement", prop_name)
            
            for keyframe_data in prop_data["keyframes"]:
                track.add_keyframe(
                    keyframe_data["time"],
                    keyframe_data["value"]
                )
            
            animation.add_track(track)
        
        print(f"✓ Preset integration tested")
        print(f"  - Preset: bounce")
        print(f"  - Animation: {animation.name}")
        print(f"  - Duration: {animation.length}s")
        print(f"  - Tracks: {len(animation.tracks)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Preset integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all animation editor tests"""
    print("=" * 60)
    print("LUPINE ENGINE ANIMATION EDITOR TEST")
    print("=" * 60)
    
    tests = [
        test_animation_editor_import,
        test_timeline_widget,
        test_track_widget,
        test_animation_editor_functionality,
        test_preset_integration
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
        print("🎉 ALL ANIMATION EDITOR TESTS PASSED!")
        return 0
    else:
        print("❌ Some animation editor tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
