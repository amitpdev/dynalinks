from user_agents import parse
from typing import Optional, Tuple, Dict, Any
import geoip2.database
import geoip2.errors
from app.config import settings


def detect_platform_and_device(user_agent_string: str) -> Tuple[str, str, str, str]:
    """
    Detect platform, device type, browser, and OS from user agent.
    Returns: (platform, device_type, browser, os)
    """
    user_agent = parse(user_agent_string)
    
    # Determine platform
    if user_agent.is_mobile:
        if 'iPhone' in user_agent_string or 'iPad' in user_agent_string:
            platform = 'iOS'
        elif 'Android' in user_agent_string:
            platform = 'Android'
        else:
            platform = 'Mobile'
    else:
        platform = 'Desktop'
    
    # Determine device type
    if user_agent.is_mobile:
        device_type = 'Mobile'
    elif user_agent.is_tablet:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'
    
    # Get browser and OS
    browser = f"{user_agent.browser.family} {user_agent.browser.version_string}"
    os = f"{user_agent.os.family} {user_agent.os.version_string}"
    
    return platform, device_type, browser, os


def get_location_from_ip(ip_address: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get country, region, and city from IP address using GeoIP2.
    Returns: (country_code, region, city)
    """
    if not settings.geoip_db_path:
        return None, None, None
    
    try:
        with geoip2.database.Reader(settings.geoip_db_path) as reader:
            response = reader.city(ip_address)
            country = response.country.iso_code
            region = response.subdivisions.most_specific.name
            city = response.city.name
            return country, region, city
    except (geoip2.errors.AddressNotFoundError, FileNotFoundError, Exception):
        return None, None, None


def get_client_ip(request) -> str:
    """Extract client IP address from request headers."""
    # Check for forwarded headers (when behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    # Check other common headers
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host


def should_redirect_to_app_store(platform: str, ios_url: Optional[str], android_url: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Determine if we should redirect to app store based on platform and available URLs.
    Returns: (should_redirect_to_store, store_url)
    """
    if platform == 'iOS' and not ios_url:
        # Redirect to App Store if no iOS URL provided
        return True, "https://apps.apple.com"
    elif platform == 'Android' and not android_url:
        # Redirect to Play Store if no Android URL provided
        return True, "https://play.google.com"
    
    return False, None


def build_redirect_url(base_url: str, parameters: Optional[Dict[str, Any]] = None) -> str:
    """Build redirect URL with optional parameters."""
    if not parameters:
        return base_url
    
    # Add parameters to URL
    param_string = "&".join([f"{k}={v}" for k, v in parameters.items() if v is not None])
    separator = "&" if "?" in base_url else "?"
    
    return f"{base_url}{separator}{param_string}" if param_string else base_url
