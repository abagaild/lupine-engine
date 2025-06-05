#!/usr/bin/env python3
"""
Integration test for the Lupine Engine Animation System
Tests integration with scene system, game engine, and editor
"""

import sys
import os
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_scene_loading():
    """Test loading a scene with AnimationPlayer"""
    print("Testing scene loading with AnimationPlayer...")

    try:
        from core.scene.scene_manager import SceneManager
        from core.project import LupineProject

        # Create a test project
        project = LupineProject(os.getcwd())
        scene_manager = SceneManager(project)
        
        # Load the test animation scene
        scene = scene_manager.load_scene("test_animation_scene.scene")
        
        if scene:
            print("✓ Scene loaded successfully")
            
            # Find the AnimationPlayer node
            animation_player = None
            for node in scene.root_nodes:
                animation_player = node.find_node("AnimationPlayer")
                if animation_player:
                    break
            
            if animation_player:
                print(f"✓ AnimationPlayer found: {animation_player.name}")
                print(f"  - Type: {animation_player.type}")
                print(f"  - Animation count: {len(animation_player.get_animation_names())}")
                
                # Test animation playback
                if animation_player.has_animation("test_animation"):
                    animation_player.play("test_animation")
                    print(f"✓ Animation playing: {animation_player.is_playing()}")
                
                return True
            else:
                print("✗ AnimationPlayer not found in scene")
                return False
        else:
            print("✗ Failed to load scene")
            return False
            
    except Exception as e:
        print(f"✗ Scene loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_game_engine_integration():
    """Test AnimationPlayer integration with scene nodes"""
    print("\nTesting scene node integration...")

    try:
        from nodes.base.AnimationPlayer import AnimationPlayer
        from core.animation import Animation
        from core.animation.animation_track import TransformTrack

        # Create a simple scene with AnimationPlayer
        from nodes.base.Node import Node
        from nodes.node2d.Sprite import Sprite

        root = Node("Root")
        sprite = Sprite("TestSprite")
        sprite.position = [100, 100]
        root.add_child(sprite)

        # Create AnimationPlayer
        anim_player = AnimationPlayer("AnimationPlayer")

        # Create animation
        animation = Animation("test_move")
        animation.length = 2.0
        animation.loop = True

        # Add position track
        track = TransformTrack("TestSprite", "position")
        track.add_keyframe(0.0, [100, 100])
        track.add_keyframe(1.0, [200, 100])
        track.add_keyframe(2.0, [100, 100])
        animation.add_track(track)

        anim_player.add_animation(animation)
        root.add_child(anim_player)

        print("✓ Scene setup successful")
        print(f"  - Root node: {root.name}")
        print(f"  - Sprite position: {sprite.position}")
        print(f"  - AnimationPlayer: {anim_player.name}")

        # Test animation update
        anim_player.play("test_move")

        # Simulate a few frames
        for i in range(5):
            delta = 0.1  # 100ms per frame
            anim_player._process(delta)
            if anim_player.current_animation:
                anim_player.current_animation.apply_to_scene(root)

        print(f"✓ Animation processed for 5 frames")
        print(f"  - Final sprite position: {sprite.position}")
        print(f"  - Animation time: {anim_player.get_current_animation_position():.2f}s")

        return True

    except Exception as e:
        print(f"✗ Scene node integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_animation_file_operations():
    """Test saving and loading animation files"""
    print("\nTesting animation file operations...")
    
    try:
        from nodes.base.AnimationPlayer import AnimationPlayer
        from core.animation import Animation
        from core.animation.animation_track import TransformTrack, ColorTrack
        import tempfile
        
        # Create AnimationPlayer with animations
        player = AnimationPlayer("TestPlayer")
        
        # Create multiple animations
        for i in range(3):
            animation = Animation(f"animation_{i}")
            animation.length = 1.0 + i
            animation.loop = i % 2 == 0
            
            # Add transform track
            pos_track = TransformTrack("Target", "position")
            pos_track.add_keyframe(0.0, [0, 0])
            pos_track.add_keyframe(animation.length, [100 * (i + 1), 50 * (i + 1)])
            animation.add_track(pos_track)
            
            # Add color track
            color_track = ColorTrack("Target", "modulate")
            color_track.add_keyframe(0.0, [1, 1, 1, 1])
            color_track.add_keyframe(animation.length, [1, 0.5, 0.5, 1])
            animation.add_track(color_track)
            
            player.add_animation(animation)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.anim', delete=False) as f:
            temp_path = f.name
        
        player.save_animation_file(temp_path)
        print(f"✓ Animations saved to {temp_path}")
        
        # Create new player and load animations
        new_player = AnimationPlayer("NewPlayer")
        new_player.load_animation_file(temp_path)
        
        print(f"✓ Animations loaded successfully")
        print(f"  - Original animation count: {len(player.get_animation_names())}")
        print(f"  - Loaded animation count: {len(new_player.get_animation_names())}")
        
        # Verify animation data
        for name in player.get_animation_names():
            loaded = new_player.get_animation(name)

            if loaded:
                print(f"  - {name}: length={loaded.length}, tracks={len(loaded.tracks)}")
            else:
                print(f"  - {name}: MISSING!")
                return False
        
        # Clean up
        os.unlink(temp_path)
        
        return True
        
    except Exception as e:
        print(f"✗ Animation file operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_animation_integration():
    """Test UI animation preset integration"""
    print("\nTesting UI animation integration...")
    
    try:
        from core.ui.ui_prefabs import get_ui_animation_presets
        from core.animation import Animation
        from core.animation.animation_track import PropertyTrack, ColorTrack
        
        # Get UI presets
        presets = get_ui_animation_presets()
        
        # Test creating animations from presets
        for preset_name, preset_data in list(presets.items())[:3]:  # Test first 3
            animation = Animation(preset_name)
            animation.length = preset_data["duration"]
            animation.loop = preset_data.get("loop", False)
            
            # Create tracks from preset data
            for prop_name, prop_data in preset_data["properties"].items():
                if prop_name in ["modulate", "color"]:
                    track = ColorTrack("UIElement", prop_name)
                else:
                    track = PropertyTrack("UIElement", prop_name)
                
                # Add keyframes
                for keyframe_data in prop_data["keyframes"]:
                    track.add_keyframe(
                        keyframe_data["time"],
                        keyframe_data["value"]
                    )
                
                animation.add_track(track)
            
            print(f"✓ Created animation from preset: {preset_name}")
            print(f"  - Duration: {animation.length}s")
            print(f"  - Tracks: {len(animation.tracks)}")
            print(f"  - Loop: {animation.loop}")
        
        return True
        
    except Exception as e:
        print(f"✗ UI animation integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sprite_frame_animation():
    """Test sprite frame animation functionality"""
    print("\nTesting sprite frame animation...")
    
    try:
        from core.animation import create_sprite_frame_animation
        from nodes.node2d.AnimatedSprite import AnimatedSprite
        from nodes.base.AnimationPlayer import AnimationPlayer
        
        # Create sprite frame animation
        frames = [0, 1, 2, 3, 2, 1]  # Walk cycle
        fps = 8.0
        
        animation = create_sprite_frame_animation("walk_cycle", "Player/Sprite", frames, fps, True)
        
        print(f"✓ Sprite frame animation created: {animation.name}")
        print(f"  - Duration: {animation.length:.2f}s")
        print(f"  - FPS: {fps}")
        print(f"  - Frames: {frames}")
        print(f"  - Loop: {animation.loop}")
        
        # Test with AnimatedSprite
        sprite = AnimatedSprite("TestSprite")
        sprite.hframes = 4
        sprite.vframes = 1
        sprite.frame = 0
        
        # Create player and add animation
        player = AnimationPlayer("SpritePlayer")
        player.add_animation(animation)
        
        # Test frame updates
        player.play("walk_cycle")
        
        # Simulate animation frames
        original_frame = sprite.frame
        for i in range(10):
            delta = 1.0 / fps  # One frame duration
            player._process(delta)
            
            # Apply animation to sprite
            if player.current_animation:
                player.current_animation.apply_to_scene(sprite.parent if sprite.parent else sprite)
        
        print(f"✓ Frame animation simulation completed")
        print(f"  - Original frame: {original_frame}")
        print(f"  - Animation time: {player.get_current_animation_position():.2f}s")
        
        return True
        
    except Exception as e:
        print(f"✗ Sprite frame animation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("=" * 70)
    print("LUPINE ENGINE ANIMATION SYSTEM INTEGRATION TEST")
    print("=" * 70)
    
    tests = [
        test_scene_loading,
        test_game_engine_integration,
        test_animation_file_operations,
        test_ui_animation_integration,
        test_sprite_frame_animation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("Integration test failed!")
        except Exception as e:
            print(f"Integration test crashed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"INTEGRATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED! Animation system is fully integrated.")
        return 0
    else:
        print("❌ Some integration tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
