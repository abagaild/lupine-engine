/**
 * Lupine Engine - Audio System Implementation
 */

#include "audio_system.h"
#include <iostream>

namespace lupine {

    //=============================================================================
    // AudioBuffer Implementation
    //=============================================================================

    AudioBuffer::AudioBuffer(const String& path) : path_(path) {
        load_from_file(path);
    }

    AudioBuffer::~AudioBuffer() {
        if (buffer_id_ != 0) {
            // TODO: Delete OpenAL buffer
            // alDeleteBuffers(1, &buffer_id_);
        }
    }

    bool AudioBuffer::load_from_file(const String& path) {
        // TODO: Load audio file using audio library (e.g., libsndfile, dr_wav)
        std::cout << "[AudioBuffer] Audio loading not yet implemented: " << path << std::endl;
        valid_ = false;
        return false;
    }

    //=============================================================================
    // AudioSource Implementation
    //=============================================================================

    AudioSource::AudioSource() {
        // TODO: Create OpenAL source
        // alGenSources(1, &source_id_);
        std::cout << "[AudioSource] Audio source creation not yet implemented" << std::endl;
        valid_ = false;
    }

    AudioSource::~AudioSource() {
        if (source_id_ != 0) {
            // TODO: Delete OpenAL source
            // alDeleteSources(1, &source_id_);
        }
    }

    void AudioSource::set_buffer(Ref<AudioBuffer> buffer) {
        buffer_ = buffer;
        if (buffer && buffer->is_valid() && source_id_ != 0) {
            // TODO: Attach buffer to source
            // alSourcei(source_id_, AL_BUFFER, buffer->get_buffer_id());
        }
    }

    void AudioSource::play() {
        if (source_id_ != 0) {
            // TODO: Play source
            // alSourcePlay(source_id_);
        }
    }

    void AudioSource::stop() {
        if (source_id_ != 0) {
            // TODO: Stop source
            // alSourceStop(source_id_);
        }
    }

    void AudioSource::pause() {
        if (source_id_ != 0) {
            // TODO: Pause source
            // alSourcePause(source_id_);
        }
    }

    bool AudioSource::is_playing() const {
        if (source_id_ != 0) {
            // TODO: Check if source is playing
            // ALint state;
            // alGetSourcei(source_id_, AL_SOURCE_STATE, &state);
            // return state == AL_PLAYING;
        }
        return false;
    }

    void AudioSource::set_position(const Vector2& position) {
        position_ = position;
        if (source_id_ != 0) {
            // TODO: Set 3D position (Z=0 for 2D)
            // alSource3f(source_id_, AL_POSITION, position.x, position.y, 0.0f);
        }
    }

    void AudioSource::set_volume(real_t volume) {
        volume_ = volume;
        if (source_id_ != 0) {
            // TODO: Set source gain
            // alSourcef(source_id_, AL_GAIN, volume);
        }
    }

    void AudioSource::set_pitch(real_t pitch) {
        pitch_ = pitch;
        if (source_id_ != 0) {
            // TODO: Set source pitch
            // alSourcef(source_id_, AL_PITCH, pitch);
        }
    }

    void AudioSource::set_looping(bool looping) {
        looping_ = looping;
        if (source_id_ != 0) {
            // TODO: Set source looping
            // alSourcei(source_id_, AL_LOOPING, looping ? AL_TRUE : AL_FALSE);
        }
    }

    //=============================================================================
    // AudioSystem Implementation
    //=============================================================================

    AudioSystem::AudioSystem(const AudioConfig& config) : config_(config) {
    }

    AudioSystem::~AudioSystem() {
        cleanup();
    }

    bool AudioSystem::initialize() {
        if (initialized_) {
            return true;
        }

        std::cout << "[AudioSystem] Initializing OpenAL audio system..." << std::endl;

        if (!setup_openal()) {
            std::cerr << "[AudioSystem] Failed to setup OpenAL" << std::endl;
            return false;
        }

        initialized_ = true;
        std::cout << "[AudioSystem] Audio system initialized successfully" << std::endl;
        return true;
    }

    void AudioSystem::cleanup() {
        if (!initialized_) {
            return;
        }

        std::cout << "[AudioSystem] Cleaning up audio system..." << std::endl;

        // Clear caches
        active_sources_.clear();
        buffer_cache_.clear();

        // Cleanup OpenAL
        cleanup_openal();

        initialized_ = false;
    }

    void AudioSystem::update() {
        if (!initialized_) {
            return;
        }

        // Update listener
        update_listener();

        // Clean up finished sources
        active_sources_.erase(
            std::remove_if(active_sources_.begin(), active_sources_.end(),
                          [](const Ref<AudioSource>& source) {
                              return !source || !source->is_playing();
                          }),
            active_sources_.end());
    }

    Ref<AudioBuffer> AudioSystem::load_buffer(const String& path) {
        // Check cache first
        auto it = buffer_cache_.find(path);
        if (it != buffer_cache_.end()) {
            return it->second;
        }

        // Load new buffer
        auto buffer = std::make_shared<AudioBuffer>(path);
        if (buffer->is_valid()) {
            buffer_cache_[path] = buffer;
            return Ref<AudioBuffer>(buffer);
        }

        return Ref<AudioBuffer>();
    }

    void AudioSystem::unload_buffer(const String& path) {
        buffer_cache_.erase(path);
    }

    Ref<AudioSource> AudioSystem::create_source() {
        auto source = std::make_shared<AudioSource>();
        active_sources_.push_back(Ref<AudioSource>(source));
        return Ref<AudioSource>(source);
    }

    void AudioSystem::destroy_source(Ref<AudioSource> source) {
        if (!source) {
            return;
        }

        source->stop();
        active_sources_.erase(
            std::remove_if(active_sources_.begin(), active_sources_.end(),
                          [&source](const Ref<AudioSource>& s) {
                              return s.get() == source.get();
                          }),
            active_sources_.end());
    }

    void AudioSystem::set_master_volume(real_t volume) {
        config_.master_volume = volume;
        // TODO: Set OpenAL listener gain
        // alListenerf(AL_GAIN, volume);
    }

    void AudioSystem::set_listener_position(const Vector2& position) {
        listener_position_ = position;
    }

    void AudioSystem::set_listener_velocity(const Vector2& velocity) {
        listener_velocity_ = velocity;
    }

    int AudioSystem::get_active_sources() const {
        return static_cast<int>(active_sources_.size());
    }

    bool AudioSystem::setup_openal() {
        // TODO: Initialize OpenAL device and context
        std::cout << "[AudioSystem] OpenAL setup not yet implemented" << std::endl;
        return true;
    }

    void AudioSystem::cleanup_openal() {
        // TODO: Cleanup OpenAL context and device
    }

    void AudioSystem::update_listener() {
        // TODO: Update OpenAL listener position and velocity
        // alListener3f(AL_POSITION, listener_position_.x, listener_position_.y, 0.0f);
        // alListener3f(AL_VELOCITY, listener_velocity_.x, listener_velocity_.y, 0.0f);
    }

} // namespace lupine
