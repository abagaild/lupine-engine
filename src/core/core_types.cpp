/**
 * Lupine Engine - Core Types Implementation
 */

#include "core_types.h"
#include <algorithm>
#include <sstream>
#include <cctype>

namespace lupine {

    //=============================================================================
    // Vector2 Constants
    //=============================================================================
    
    const Vector2 Vector2::ZERO(0.0f, 0.0f);
    const Vector2 Vector2::ONE(1.0f, 1.0f);
    const Vector2 Vector2::UP(0.0f, -1.0f);
    const Vector2 Vector2::DOWN(0.0f, 1.0f);
    const Vector2 Vector2::LEFT(-1.0f, 0.0f);
    const Vector2 Vector2::RIGHT(1.0f, 0.0f);

    //=============================================================================
    // Color Constants
    //=============================================================================
    
    const Color Color::WHITE(1.0f, 1.0f, 1.0f, 1.0f);
    const Color Color::BLACK(0.0f, 0.0f, 0.0f, 1.0f);
    const Color Color::RED(1.0f, 0.0f, 0.0f, 1.0f);
    const Color Color::GREEN(0.0f, 1.0f, 0.0f, 1.0f);
    const Color Color::BLUE(0.0f, 0.0f, 1.0f, 1.0f);
    const Color Color::TRANSPARENT(0.0f, 0.0f, 0.0f, 0.0f);

    //=============================================================================
    // Transform2D Implementation
    //=============================================================================
    
    const Transform2D Transform2D::IDENTITY;

    Transform2D::Transform2D(real_t rotation, const Vector2& position) {
        set_rotation(rotation);
        origin = position;
    }

    Transform2D::Transform2D(real_t rotation, const Vector2& scale, real_t skew, const Vector2& position) {
        real_t cr = std::cos(rotation);
        real_t sr = std::sin(rotation);
        real_t cs = std::cos(skew);
        real_t ss = std::sin(skew);
        
        x.x = cr * scale.x;
        x.y = sr * scale.x;
        y.x = -sr * cs * scale.y + ss * cr * scale.y;
        y.y = cr * cs * scale.y + ss * sr * scale.y;
        origin = position;
    }

    Transform2D Transform2D::operator*(const Transform2D& other) const {
        Transform2D result;
        result.x = Vector2(x.dot(other.x), y.dot(other.x));
        result.y = Vector2(x.dot(other.y), y.dot(other.y));
        result.origin = transform_point(other.origin);
        return result;
    }

    Transform2D Transform2D::inverse() const {
        Transform2D inv;
        real_t det = x.x * y.y - x.y * y.x;
        
        if (Math::abs(det) < 1e-6f) {
            return Transform2D();  // Return identity if not invertible
        }
        
        real_t idet = 1.0f / det;
        
        inv.x.x = y.y * idet;
        inv.x.y = -x.y * idet;
        inv.y.x = -y.x * idet;
        inv.y.y = x.x * idet;
        
        inv.origin = Vector2(-inv.x.dot(origin), -inv.y.dot(origin));
        
        return inv;
    }

    void Transform2D::set_rotation(real_t rotation) {
        real_t cr = std::cos(rotation);
        real_t sr = std::sin(rotation);
        x.x = cr;
        x.y = sr;
        y.x = -sr;
        y.y = cr;
    }

    real_t Transform2D::get_rotation() const {
        return std::atan2(x.y, x.x);
    }

    void Transform2D::set_scale(const Vector2& scale) {
        real_t rotation = get_rotation();
        set_rotation(rotation);
        x *= scale.x;
        y *= scale.y;
    }

    Vector2 Transform2D::get_scale() const {
        return Vector2(x.length(), y.length());
    }

    //=============================================================================
    // String Utilities Implementation
    //=============================================================================
    
    namespace StringUtils {
        
        std::vector<String> split(const String& str, const String& delimiter) {
            std::vector<String> result;
            size_t start = 0;
            size_t end = str.find(delimiter);
            
            while (end != String::npos) {
                result.push_back(str.substr(start, end - start));
                start = end + delimiter.length();
                end = str.find(delimiter, start);
            }
            
            result.push_back(str.substr(start));
            return result;
        }

        String join(const std::vector<String>& parts, const String& separator) {
            if (parts.empty()) {
                return "";
            }
            
            std::ostringstream result;
            result << parts[0];
            
            for (size_t i = 1; i < parts.size(); ++i) {
                result << separator << parts[i];
            }
            
            return result.str();
        }

        String to_lower(const String& str) {
            String result = str;
            std::transform(result.begin(), result.end(), result.begin(), 
                          [](unsigned char c) { return std::tolower(c); });
            return result;
        }

        String to_upper(const String& str) {
            String result = str;
            std::transform(result.begin(), result.end(), result.begin(), 
                          [](unsigned char c) { return std::toupper(c); });
            return result;
        }

        bool starts_with(const String& str, const String& prefix) {
            if (prefix.length() > str.length()) {
                return false;
            }
            return str.substr(0, prefix.length()) == prefix;
        }

        bool ends_with(const String& str, const String& suffix) {
            if (suffix.length() > str.length()) {
                return false;
            }
            return str.substr(str.length() - suffix.length()) == suffix;
        }

        String trim(const String& str) {
            size_t start = str.find_first_not_of(" \t\n\r\f\v");
            if (start == String::npos) {
                return "";
            }
            
            size_t end = str.find_last_not_of(" \t\n\r\f\v");
            return str.substr(start, end - start + 1);
        }
        
    } // namespace StringUtils

} // namespace lupine
