/**
 * Lupine Engine - Renderer Implementation
 */

#include "renderer.h"
#include "../scene/node.h"
#include <iostream>
#include <algorithm>

#ifdef WINDOWS_ENABLED
#include <windows.h>
#include <GL/gl.h>
#endif

namespace lupine {

    //=============================================================================
    // Texture Implementation
    //=============================================================================

    Texture::Texture(uint32_t gl_id, int width, int height) 
        : gl_id_(gl_id), width_(width), height_(height) {
    }

    Texture::~Texture() {
        if (gl_id_ != 0) {
            // TODO: Delete OpenGL texture
            // glDeleteTextures(1, &gl_id_);
        }
    }

    //=============================================================================
    // Font Implementation
    //=============================================================================

    Font::Font(const String& path, int size) : path_(path), size_(size) {
        // TODO: Load font from file
        std::cout << "[Font] Font loading not yet implemented: " << path << std::endl;
        valid_ = false;
    }

    Font::~Font() {
        // TODO: Cleanup font data
    }

    Vector2 Font::get_string_size(const String& text) const {
        // TODO: Calculate text size
        return Vector2(text.length() * size_ * 0.6f, size_);
    }

    //=============================================================================
    // Renderer Implementation
    //=============================================================================

    Renderer::Renderer(const RendererConfig& config) : config_(config) {
    }

    Renderer::~Renderer() {
        cleanup();
    }

    bool Renderer::initialize() {
        if (initialized_) {
            return true;
        }

        std::cout << "[Renderer] Initializing OpenGL renderer..." << std::endl;

        // Setup OpenGL
        if (!setup_opengl()) {
            std::cerr << "[Renderer] Failed to setup OpenGL" << std::endl;
            return false;
        }

        // Create shaders
        if (!create_shaders()) {
            std::cerr << "[Renderer] Failed to create shaders" << std::endl;
            return false;
        }

        // Setup buffers
        if (!setup_buffers()) {
            std::cerr << "[Renderer] Failed to setup buffers" << std::endl;
            return false;
        }

        // Create default resources
        // TODO: Create white texture and default font

        initialized_ = true;
        std::cout << "[Renderer] Renderer initialized successfully" << std::endl;
        return true;
    }

    void Renderer::cleanup() {
        if (!initialized_) {
            return;
        }

        std::cout << "[Renderer] Cleaning up renderer..." << std::endl;

        // Clear caches
        texture_cache_.clear();
        font_cache_.clear();

        // TODO: Cleanup OpenGL resources
        if (vao_ != 0) {
            // glDeleteVertexArrays(1, &vao_);
            vao_ = 0;
        }
        if (vbo_ != 0) {
            // glDeleteBuffers(1, &vbo_);
            vbo_ = 0;
        }
        if (shader_program_ != 0) {
            // glDeleteProgram(shader_program_);
            shader_program_ = 0;
        }

        initialized_ = false;
    }

    void Renderer::begin_frame() {
        if (!initialized_) {
            return;
        }

        // Reset statistics
        draw_calls_ = 0;
        vertices_drawn_ = 0;

        // Clear render commands
        render_commands_.clear();

        // Setup viewport
        setup_viewport_and_projection();
    }

    void Renderer::end_frame() {
        if (!initialized_) {
            return;
        }

        // Sort and execute render commands
        sort_render_commands();
        flush_commands();
    }

    void Renderer::clear(const Color& color) {
        if (!initialized_) {
            return;
        }

        // TODO: OpenGL clear
        // glClearColor(color.r, color.g, color.b, color.a);
        // glClear(GL_COLOR_BUFFER_BIT);
    }

    void Renderer::present() {
        if (!initialized_) {
            return;
        }

        // TODO: Swap buffers
        // SwapBuffers() or similar platform-specific call
    }

    void Renderer::set_viewport(int x, int y, int width, int height) {
        // TODO: Set OpenGL viewport
        // glViewport(x, y, width, height);
    }

    void Renderer::setup_2d_projection() {
        // TODO: Setup 2D orthographic projection matrix
        std::cout << "[Renderer] 2D projection setup not yet implemented" << std::endl;
    }

    void Renderer::setup_camera(Camera2D* camera) {
        current_camera_ = camera;
        if (camera) {
            view_transform_ = calculate_view_transform();
        }
    }

    Ref<Texture> Renderer::load_texture(const String& path) {
        // Check cache first
        auto it = texture_cache_.find(path);
        if (it != texture_cache_.end()) {
            return it->second;
        }

        // Load new texture
        auto texture = load_texture_from_file(path);
        if (texture) {
            texture_cache_[path] = texture;
        }

        return texture;
    }

    Ref<Texture> Renderer::create_texture(int width, int height, const uint8_t* data) {
        // TODO: Create OpenGL texture from data
        std::cout << "[Renderer] Texture creation not yet implemented" << std::endl;
        return Ref<Texture>();
    }

    void Renderer::unload_texture(const String& path) {
        texture_cache_.erase(path);
    }

    Ref<Font> Renderer::load_font(const String& path, int size) {
        String cache_key = path + "_" + std::to_string(size);
        
        // Check cache first
        auto it = font_cache_.find(cache_key);
        if (it != font_cache_.end()) {
            return it->second;
        }

        // Load new font
        auto font = std::make_shared<Font>(path, size);
        if (font->is_valid()) {
            font_cache_[cache_key] = font;
            return Ref<Font>(font);
        }

        return Ref<Font>();
    }

    void Renderer::draw_sprite(Ref<Texture> texture, const Vector2& position, 
                              const Vector2& scale, real_t rotation, 
                              const Color& modulate) {
        if (!texture || !texture->is_valid()) {
            return;
        }

        RenderCommand cmd;
        cmd.type = RenderCommand::SPRITE;
        cmd.texture = texture;
        cmd.transform = Transform2D(rotation, position);
        cmd.transform.set_scale(scale);
        cmd.modulate = modulate;
        cmd.dst_rect = Rect2(position, texture->get_size());

        submit_command(cmd);
    }

    void Renderer::draw_texture_rect(Ref<Texture> texture, const Rect2& rect,
                                    const String& stretch_mode,
                                    bool flip_h, bool flip_v,
                                    const Color& modulate,
                                    const Vector2& uv_offset,
                                    const Vector2& uv_scale,
                                    real_t rotation,
                                    const Rect2& region_rect) {
        if (!texture || !texture->is_valid()) {
            return;
        }

        RenderCommand cmd;
        cmd.type = RenderCommand::TEXTURE_RECT;
        cmd.texture = texture;
        cmd.dst_rect = rect;
        cmd.stretch_mode = stretch_mode;
        cmd.flip_h = flip_h;
        cmd.flip_v = flip_v;
        cmd.modulate = modulate;
        cmd.transform = Transform2D(rotation, rect.position);

        if (region_rect.size.x > 0 && region_rect.size.y > 0) {
            cmd.src_rect = region_rect;
        } else {
            cmd.src_rect = Rect2(Vector2::ZERO, texture->get_size());
        }

        submit_command(cmd);
    }

    void Renderer::draw_rectangle(const Rect2& rect, const Color& color, bool filled) {
        RenderCommand cmd;
        cmd.type = RenderCommand::RECTANGLE;
        cmd.dst_rect = rect;
        cmd.modulate = color;
        cmd.filled = filled;

        submit_command(cmd);
    }

    void Renderer::draw_circle(const Vector2& center, real_t radius, const Color& color, bool filled) {
        RenderCommand cmd;
        cmd.type = RenderCommand::CIRCLE;
        cmd.transform.origin = center;
        cmd.radius = radius;
        cmd.modulate = color;
        cmd.filled = filled;

        submit_command(cmd);
    }

    void Renderer::draw_line(const Vector2& from, const Vector2& to, const Color& color, real_t width) {
        RenderCommand cmd;
        cmd.type = RenderCommand::LINE;
        cmd.from = from;
        cmd.to = to;
        cmd.modulate = color;
        cmd.width = width;

        submit_command(cmd);
    }

    void Renderer::draw_text(const String& text, const Vector2& position, Ref<Font> font,
                            const Color& color, const String& align) {
        if (!font || !font->is_valid()) {
            font = default_font_;
        }

        if (!font || !font->is_valid()) {
            return;
        }

        RenderCommand cmd;
        cmd.type = RenderCommand::TEXT;
        cmd.text = text;
        cmd.transform.origin = position;
        cmd.font = font;
        cmd.modulate = color;
        cmd.align = align;

        submit_command(cmd);
    }

    void Renderer::submit_command(const RenderCommand& command) {
        render_commands_.push_back(command);
    }

    void Renderer::flush_commands() {
        for (const auto& command : render_commands_) {
            execute_render_command(command);
        }
        render_commands_.clear();
    }

    void Renderer::set_config(const RendererConfig& config) {
        config_ = config;
        // TODO: Update renderer state based on new config
    }

    bool Renderer::setup_opengl() {
        // TODO: Initialize OpenGL context and extensions
        std::cout << "[Renderer] OpenGL setup not yet implemented" << std::endl;
        return true;
    }

    bool Renderer::create_shaders() {
        // TODO: Create and compile shaders
        std::cout << "[Renderer] Shader creation not yet implemented" << std::endl;
        return true;
    }

    bool Renderer::setup_buffers() {
        // TODO: Create vertex array objects and buffers
        std::cout << "[Renderer] Buffer setup not yet implemented" << std::endl;
        return true;
    }

    Ref<Texture> Renderer::load_texture_from_file(const String& path) {
        // TODO: Load texture from file using image loading library
        std::cout << "[Renderer] Texture loading not yet implemented: " << path << std::endl;
        return Ref<Texture>();
    }

    void Renderer::calculate_uv_coordinates(const String& stretch_mode, const Vector2& size,
                                          const Vector2& texture_size, bool flip_h, bool flip_v,
                                          const Vector2& uv_offset, const Vector2& uv_scale,
                                          const Rect2& region_rect, Vector2& uv1, Vector2& uv2) {
        // TODO: Calculate UV coordinates based on stretch mode and parameters
        uv1 = Vector2(0.0f, 0.0f);
        uv2 = Vector2(1.0f, 1.0f);
    }

    void Renderer::sort_render_commands() {
        // Sort by z-index
        std::sort(render_commands_.begin(), render_commands_.end(),
                 [](const RenderCommand& a, const RenderCommand& b) {
                     return a.z_index < b.z_index;
                 });
    }

    void Renderer::execute_render_command(const RenderCommand& command) {
        // TODO: Execute individual render command
        draw_calls_++;
        vertices_drawn_ += 4; // Assuming quad rendering
    }

    void Renderer::setup_viewport_and_projection() {
        // TODO: Setup viewport and projection matrix
        set_viewport(0, 0, config_.window_width, config_.window_height);
        setup_2d_projection();
    }

    Transform2D Renderer::calculate_view_transform() const {
        if (!current_camera_) {
            return Transform2D::IDENTITY;
        }

        // TODO: Calculate view transform based on camera
        Transform2D view = current_camera_->get_global_transform().inverse();
        return view;
    }

    //=============================================================================
    // Sprite Implementation
    //=============================================================================

    Sprite::Sprite(const String& name) : Node2D(name) {
        type_ = "Sprite";
    }

    void Sprite::set_texture_path(const String& path) {
        texture_path_ = path;
        // TODO: Load texture from path
        auto* engine = get_engine();
        if (engine && engine->get_systems() && engine->get_systems()->get_renderer()) {
            texture_ = engine->get_systems()->get_renderer()->load_texture(path);
        }
    }

    void Sprite::_draw() {
        if (!texture_ || !texture_->is_valid()) {
            return;
        }

        auto* engine = get_engine();
        if (!engine || !engine->get_systems() || !engine->get_systems()->get_renderer()) {
            return;
        }

        auto* renderer = engine->get_systems()->get_renderer();

        // Calculate destination rectangle
        Vector2 texture_size = texture_->get_size();
        Vector2 draw_size = texture_size;
        Vector2 draw_position = get_global_position();

        if (centered_) {
            draw_position -= draw_size * 0.5f;
        }
        draw_position += offset_;

        Rect2 dst_rect(draw_position, draw_size);
        Rect2 src_rect = region_enabled_ ? region_rect_ : Rect2(Vector2::ZERO, texture_size);

        renderer->draw_texture_rect(texture_, dst_rect, "stretch", flip_h_, flip_v_, modulate_,
                                   Vector2::ZERO, Vector2::ONE, get_global_rotation(), src_rect);
    }

    void Sprite::save_to_dict(std::unordered_map<String, Variant>& dict) const {
        Node2D::save_to_dict(dict);
        dict["texture_path"] = Variant(texture_path_);
        dict["modulate"] = Variant(modulate_);
        dict["centered"] = Variant(centered_);
        dict["offset"] = Variant(offset_);
        dict["flip_h"] = Variant(flip_h_);
        dict["flip_v"] = Variant(flip_v_);
        dict["region_enabled"] = Variant(region_enabled_);
        dict["region_rect"] = Variant(region_rect_);
    }

    void Sprite::load_from_dict(const std::unordered_map<String, Variant>& dict) {
        Node2D::load_from_dict(dict);

        auto it = dict.find("texture_path");
        if (it != dict.end()) {
            set_texture_path(it->second.as_string());
        }

        it = dict.find("modulate");
        if (it != dict.end()) {
            modulate_ = it->second.as_color();
        }

        it = dict.find("centered");
        if (it != dict.end()) {
            centered_ = it->second.as_bool();
        }

        it = dict.find("offset");
        if (it != dict.end()) {
            offset_ = it->second.as_vector2();
        }

        it = dict.find("flip_h");
        if (it != dict.end()) {
            flip_h_ = it->second.as_bool();
        }

        it = dict.find("flip_v");
        if (it != dict.end()) {
            flip_v_ = it->second.as_bool();
        }

        it = dict.find("region_enabled");
        if (it != dict.end()) {
            region_enabled_ = it->second.as_bool();
        }

        it = dict.find("region_rect");
        if (it != dict.end()) {
            region_rect_ = it->second.as_rect2();
        }
    }

} // namespace lupine
