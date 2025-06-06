/**
 * Lupine Engine - Platform Factory Implementation
 * 
 * Platform-specific factory for creating platform instances.
 */

#include "platform.h"

// Include platform-specific implementations
#ifdef WINDOWS_ENABLED
#include "../../platform/windows/platform_windows.h"
#endif

#ifdef LINUX_ENABLED
#include "../../platform/linux/platform_linux.h"
#endif

#ifdef MACOS_ENABLED
#include "../../platform/macos/platform_macos.h"
#endif

namespace lupine {

    std::unique_ptr<Platform> Platform::create() {
#ifdef WINDOWS_ENABLED
        return std::make_unique<PlatformWindows>();
#elif defined(LINUX_ENABLED)
        return std::make_unique<PlatformLinux>();
#elif defined(MACOS_ENABLED)
        return std::make_unique<PlatformMacOS>();
#else
        #error "No platform implementation available"
        return nullptr;
#endif
    }

} // namespace lupine
