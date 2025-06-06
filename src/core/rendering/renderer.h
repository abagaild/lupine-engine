#pragma once

/**
 * Lupine Engine - Rendering System
 * 
 * OpenGL-based renderer for 2D graphics.
 * This is the C++ equivalent of the Python SharedRenderer class.
 */

#include "../core_types.h"
#include <memory>
#include <unordered_map>
#include <vector>

namespace lupine {

    // Forward declarations
    class Texture;
    class Font;
    class Camera2D;
    class Node2D;

    /**
     * Texture resource
     */
    class Texture {
    public:
        Texture(uint32_t gl_id, int width, int height);
        ~Texture();

        uint32_t get_gl_id() const { return gl_id_; }
        int get_width() const { return width_; }
        int get_height() const { return height_; }
        Vector2 get_size() const { return Vector2(static_cast<real_t>(width_), static_cast<real_t>(height_)); }

        bool is_valid() const { return gl_id_ != 0; }

    private:
        uint32_t gl_id_;
        int width_;
        int height_;
    };

    /**
     * Font resource for text rendering
     */
    class Font {
    public:
        Font(const String& path, int size);
        ~Font();

        const String& get_path() const { return path_; }
        int get_size() const { return size_; }
        bool is_valid() const { return valid_; }

        Vector2 get_string_size(const String& text) const;

    private:
        String path_;
        int size_;
        bool valid_ = false;
        void* font_data_ = nullptr;  // Platform-specific font data
    };

    /**
     * Render command for batching
     */
    struct RenderCommand {
        enum Type {
            SPRITE,
            TEXTURE_RECT,
            RECTANGLE,
            CIRCLE,
            TEXT,
            LINE
        };

        Type type;
        int z_index = 0;
        Transform2D transform;
        Color modulate = Color::WHITE;
        
        // Sprite/Texture data
        Ref<Texture> texture;
        Rect2 src_rect;
        Rect2 dst_rect;
        String stretch_mode = "stretch";
        bool flip_h = false;
        bool flip_v = false;
        
        // Shape data
        Vector2 size;
        real_t radius = 0.0f;
        bool filled = true;
        
        // Text data
        String text;
        Ref<Font> font;
        String align = "left";
        String valign = "top";
        
        // Line data
        Vector2 from;
        Vector2 to;
        real_t width = 1.0f;
    };

    /**
     * Rendering configuration
     */
    struct RendererConfig {
        int window_width = 1280;
        int window_height = 720;
        int game_bounds_width = 1920;
        int game_bounds_height = 1080;
        String scaling_mode = "stretch";  // stretch, letterbox, crop
        String scaling_filter = "linear"; // linear, nearest
        bool vsync = true;
        Color clear_color = Color(0.1f, 0.1f, 0.15f, 1.0f);
    };

    /**
     * Main renderer class
     */
    class Renderer {
    public:
        explicit Renderer(const RendererConfig& config);
        ~Renderer();

        // Initialization
        bool initialize();
        void cleanup();

        // Frame management
        void begin_frame();
        void end_frame();
        void clear(const Color& color = Color());
        void present();

        // Viewport and projection
        void set_viewport(int x, int y, int width, int height);
        void setup_2d_projection();
        void setup_camera(Camera2D* camera);

        // Texture management
        Ref<Texture> load_texture(const String& path);
        Ref<Texture> create_texture(int width, int height, const uint8_t* data);
        void unload_texture(const String& path);

        // Font management
        Ref<Font> load_font(const String& path, int size);
        Ref<Font> get_default_font() const { return default_font_; }

        // Immediate mode rendering
        void draw_sprite(Ref<Texture> texture, const Vector2& position, 
                        const Vector2& scale = Vector2::ONE, real_t rotation = 0.0f, 
                        const Color& modulate = Color::WHITE);
        
        void draw_texture_rect(Ref<Texture> texture, const Rect2& rect,
                              const String& stretch_mode = "stretch",
                              bool flip_h = false, bool flip_v = false,
                              const Color& modulate = Color::WHITE,
                              const Vector2& uv_offset = Vector2::ZERO,
                              const Vector2& uv_scale = Vector2::ONE,
                              real_t rotation = 0.0f,
                              const Rect2& region_rect = Rect2());

        void draw_rectangle(const Rect2& rect, const Color& color, bool filled = true);
        void draw_circle(const Vector2& center, real_t radius, const Color& color, bool filled = true);
        void draw_line(const Vector2& from, const Vector2& to, const Color& color, real_t width = 1.0f);
        
        void draw_text(const String& text, const Vector2& position, Ref<Font> font,
                      const Color& color = Color::WHITE, const String& align = "left");

        // Batched rendering
        void submit_command(const RenderCommand& command);
        void flush_commands();

        // Configuration
        const RendererConfig& get_config() const { return config_; }
        void set_config(const RendererConfig& config);
        
        void set_scaling_mode(const String& mode) { config_.scaling_mode = mode; }
        void set_scaling_filter(const String& filter) { config_.scaling_filter = filter; }

        // State
        bool is_initialized() const { return initialized_; }
        Vector2 get_window_size() const { return Vector2(config_.window_width, config_.window_height); }
        Vector2 get_game_bounds() const { return Vector2(config_.game_bounds_width, config_.game_bounds_height); }

        // Statistics
        int get_draw_calls() const { return draw_calls_; }
        int get_vertices_drawn() const { return vertices_drawn_; }
        void reset_stats() { draw_calls_ = 0; vertices_drawn_ = 0; }

    private:
        RendererConfig config_;
        bool initialized_ = false;
        
        // OpenGL state
        uint32_t vao_ = 0;
        uint32_t vbo_ = 0;
        uint32_t shader_program_ = 0;
        
        // Resource caches
        std::unordered_map<String, Ref<Texture>> texture_cache_;
        std::unordered_map<String, Ref<Font>> font_cache_;
        
        // Default resources
        Ref<Font> default_font_;
        Ref<Texture> white_texture_;
        
        // Render commands
        std::vector<RenderCommand> render_commands_;
        
        // Current state
        Camera2D* current_camera_ = nullptr;
        Transform2D view_transform_;
        
        // Statistics
        int draw_calls_ = 0;
        int vertices_drawn_ = 0;
        
        // Internal methods
        bool setup_opengl();
        bool create_shaders();
        bool setup_buffers();
        
        Ref<Texture> load_texture_from_file(const String& path);
        void calculate_uv_coordinates(const String& stretch_mode, const Vector2& size,
                                    const Vector2& texture_size, bool flip_h, bool flip_v,
                                    const Vector2& uv_offset, const Vector2& uv_scale,
                                    const Rect2& region_rect, Vector2& uv1, Vector2& uv2);
        
        void sort_render_commands();
        void execute_render_command(const RenderCommand& command);
        
        void setup_viewport_and_projection();
        Transform2D calculate_view_transform() const;
    };

    /**
     * Sprite node for rendering textures
     */
    class Sprite : public Node2D {
    public:
        Sprite(const String& name = "Sprite");
        virtual ~Sprite() = default;

        // Texture
        Ref<Texture> get_texture() const { return texture_; }
        void set_texture(Ref<Texture> texture) { texture_ = texture; }
        void set_texture_path(const String& path);

        // Rendering properties
        const Color& get_modulate() const { return modulate_; }
        void set_modulate(const Color& modulate) { modulate_ = modulate; }
        
        bool is_centered() const { return centered_; }
        void set_centered(bool centered) { centered_ = centered; }
        
        const Vector2& get_offset() const { return offset_; }
        void set_offset(const Vector2& offset) { offset_ = offset; }
        
        bool is_flip_h() const { return flip_h_; }
        void set_flip_h(bool flip) { flip_h_ = flip; }
        
        bool is_flip_v() const { return flip_v_; }
        void set_flip_v(bool flip) { flip_v_ = flip; }

        // Region
        bool is_region_enabled() const { return region_enabled_; }
        void set_region_enabled(bool enabled) { region_enabled_ = enabled; }
        
        const Rect2& get_region_rect() const { return region_rect_; }
        void set_region_rect(const Rect2& rect) { region_rect_ = rect; }

        // Rendering
        void _draw() override;

        // Serialization
        void save_to_dict(std::unordered_map<String, Variant>& dict) const override;
        void load_from_dict(const std::unordered_map<String, Variant>& dict) override;

    private:
        Ref<Texture> texture_;
        String texture_path_;
        Color modulate_ = Color::WHITE;
        bool centered_ = true;
        Vector2 offset_ = Vector2::ZERO;
        bool flip_h_ = false;
        bool flip_v_ = false;
        bool region_enabled_ = false;
        Rect2 region_rect_;
    };

} // namespace lupine
