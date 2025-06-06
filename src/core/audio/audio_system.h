#pragma once

/**
 * Lupine Engine - Audio System
 * 
 * OpenAL-based audio system for 2D positional audio.
 * This is the C++ equivalent of the Python OpenALAudio class.
 */

#include "../core_types.h"
#include <memory>
#include <unordered_map>
#include <vector>

namespace lupine {

    // Forward declarations
    class AudioBuffer;
    class AudioSource;

    /**
     * Audio buffer for storing audio data
     */
    class AudioBuffer {
    public:
        AudioBuffer(const String& path);
        ~AudioBuffer();

        bool load_from_file(const String& path);
        bool is_valid() const { return valid_; }
        const String& get_path() const { return path_; }
        uint32_t get_buffer_id() const { return buffer_id_; }

    private:
        String path_;
        uint32_t buffer_id_ = 0;
        bool valid_ = false;
    };

    /**
     * Audio source for playing audio
     */
    class AudioSource {
    public:
        AudioSource();
        ~AudioSource();

        void set_buffer(Ref<AudioBuffer> buffer);
        Ref<AudioBuffer> get_buffer() const { return buffer_; }

        void play();
        void stop();
        void pause();
        bool is_playing() const;

        void set_position(const Vector2& position);
        Vector2 get_position() const { return position_; }

        void set_volume(real_t volume);
        real_t get_volume() const { return volume_; }

        void set_pitch(real_t pitch);
        real_t get_pitch() const { return pitch_; }

        void set_looping(bool looping);
        bool is_looping() const { return looping_; }

        uint32_t get_source_id() const { return source_id_; }

    private:
        uint32_t source_id_ = 0;
        Ref<AudioBuffer> buffer_;
        Vector2 position_ = Vector2::ZERO;
        real_t volume_ = 1.0f;
        real_t pitch_ = 1.0f;
        bool looping_ = false;
        bool valid_ = false;
    };

    /**
     * Audio system configuration
     */
    struct AudioConfig {
        String device_name = "";  // Empty for default device
        int max_sources = 32;
        real_t master_volume = 1.0f;
        real_t doppler_factor = 1.0f;
        real_t speed_of_sound = 343.3f;
    };

    /**
     * Main audio system class
     */
    class AudioSystem {
    public:
        explicit AudioSystem(const AudioConfig& config = AudioConfig());
        ~AudioSystem();

        // Initialization
        bool initialize();
        void cleanup();
        void update();

        // Buffer management
        Ref<AudioBuffer> load_buffer(const String& path);
        void unload_buffer(const String& path);

        // Source management
        Ref<AudioSource> create_source();
        void destroy_source(Ref<AudioSource> source);

        // Global settings
        void set_master_volume(real_t volume);
        real_t get_master_volume() const { return config_.master_volume; }

        void set_listener_position(const Vector2& position);
        Vector2 get_listener_position() const { return listener_position_; }

        void set_listener_velocity(const Vector2& velocity);
        Vector2 get_listener_velocity() const { return listener_velocity_; }

        // Configuration
        const AudioConfig& get_config() const { return config_; }
        bool is_initialized() const { return initialized_; }

        // Statistics
        int get_active_sources() const;
        int get_loaded_buffers() const { return static_cast<int>(buffer_cache_.size()); }

    private:
        AudioConfig config_;
        bool initialized_ = false;

        // OpenAL context
        void* device_ = nullptr;   // ALCdevice*
        void* context_ = nullptr;  // ALCcontext*

        // Resource caches
        std::unordered_map<String, Ref<AudioBuffer>> buffer_cache_;
        std::vector<Ref<AudioSource>> active_sources_;

        // Listener state
        Vector2 listener_position_ = Vector2::ZERO;
        Vector2 listener_velocity_ = Vector2::ZERO;

        // Internal methods
        bool setup_openal();
        void cleanup_openal();
        void update_listener();
    };

} // namespace lupine
