/**
 * Lupine Engine - Windows Platform OpenGL Setup
 * 
 * OpenGL context creation and management for Windows platform.
 */

#ifdef WINDOWS_ENABLED

#include "platform_windows.h"
#include <iostream>
#include <GL/gl.h>

namespace lupine {

    bool PlatformWindows::setup_pixel_format() {
        PIXELFORMATDESCRIPTOR pfd = {};
        pfd.nSize = sizeof(PIXELFORMATDESCRIPTOR);
        pfd.nVersion = 1;
        pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER;
        pfd.iPixelType = PFD_TYPE_RGBA;
        pfd.cColorBits = 32;
        pfd.cDepthBits = 24;
        pfd.cStencilBits = 8;
        pfd.iLayerType = PFD_MAIN_PLANE;

        int pixel_format = ChoosePixelFormat(hdc_, &pfd);
        if (pixel_format == 0) {
            std::cerr << "[Platform] Failed to choose pixel format" << std::endl;
            return false;
        }

        if (!SetPixelFormat(hdc_, pixel_format, &pfd)) {
            std::cerr << "[Platform] Failed to set pixel format" << std::endl;
            return false;
        }

        return true;
    }

    bool PlatformWindows::create_opengl_context_core() {
        if (!wglCreateContextAttribsARB) {
            return false;
        }

        // OpenGL 3.3 Core Profile attributes
        int attribs[] = {
            WGL_CONTEXT_MAJOR_VERSION_ARB, 3,
            WGL_CONTEXT_MINOR_VERSION_ARB, 3,
            WGL_CONTEXT_PROFILE_MASK_ARB, WGL_CONTEXT_CORE_PROFILE_BIT_ARB,
            WGL_CONTEXT_FLAGS_ARB, WGL_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB,
            0
        };

        hglrc_ = wglCreateContextAttribsARB(hdc_, nullptr, attribs);
        if (!hglrc_) {
            std::cerr << "[Platform] Failed to create OpenGL 3.3 core context" << std::endl;
            return false;
        }

        return true;
    }

    bool PlatformWindows::load_wgl_extensions() {
        // Load WGL extension functions
        wglSwapIntervalEXT = reinterpret_cast<PFNWGLSWAPINTERVALEXTPROC>(
            wglGetProcAddress("wglSwapIntervalEXT"));
        
        wglGetSwapIntervalEXT = reinterpret_cast<PFNWGLGETSWAPINTERVALEXTPROC>(
            wglGetProcAddress("wglGetSwapIntervalEXT"));
        
        wglCreateContextAttribsARB = reinterpret_cast<PFNWGLCREATECONTEXTATTRIBSARBPROC>(
            wglGetProcAddress("wglCreateContextAttribsARB"));

        // Check if we have the essential extensions
        const char* extensions = reinterpret_cast<const char*>(glGetString(GL_EXTENSIONS));
        if (!extensions) {
            std::cerr << "[Platform] Failed to get OpenGL extensions" << std::endl;
            return false;
        }

        // Log available extensions for debugging
        std::cout << "[Platform] OpenGL Extensions loaded successfully" << std::endl;
        
        return true;
    }

} // namespace lupine

#endif // WINDOWS_ENABLED
