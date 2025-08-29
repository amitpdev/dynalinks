from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.db_pg import PostgresDB, get_db_instance
from app.schemas import LinkAnalyticsResponse
from app.analytics import (
    detect_platform_and_device, 
    get_location_from_ip, 
    get_client_ip,
    should_redirect_to_app_store,
    build_redirect_url
)
from app.cache import cache
from app.config import settings
from app.utils import hash_ip_address
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Redirect & Analytics"])

def generate_redirect_html(
    ios_url: Optional[str],
    android_url: Optional[str],
    fallback_url: str,
    social_title: Optional[str] = None,
    social_description: Optional[str] = None,
    social_image_url: Optional[str] = None,
) -> str:
    """Generates an HTML page with JavaScript for mobile redirection."""

    ios_deep_link = ios_url or ""
    android_deep_link = android_url or ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{social_title or 'Redirecting...'}</title>
        <meta property="og:title" content="{social_title or ''}" />
        <meta property="og:description" content="{social_description or ''}" />
        <meta property="og:image" content="{social_image_url or ''}" />
        <script type="text/javascript">
            function redirect() {{
                var userAgent = navigator.userAgent || navigator.vendor || window.opera;
                var fallback = '{fallback_url}';
                var deepLink;
                var storeUrl;

                if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {{
                    deepLink = '{ios_deep_link}';
                    storeUrl = fallback; 
                }} else if (/android/i.test(userAgent)) {{
                    deepLink = '{android_deep_link}';
                    storeUrl = fallback;
                }} else {{
                    window.location = fallback;
                    return;
                }}

                if (!deepLink) {{
                    window.location = storeUrl;
                    return;
                }}

                window.location = deepLink;

                var timeout = setTimeout(function() {{
                    window.location = storeUrl;
                }}, 1500);

                function onVisibilityChange() {{
                    if (document.hidden || document.webkitHidden) {{
                        clearTimeout(timeout);
                    }}
                }}

                document.addEventListener("visibilitychange", onVisibilityChange, false);
                document.addEventListener("webkitvisibilitychange", onVisibilityChange, false);
            }}
            window.onload = redirect;
        </script>
    </head>
    <body>
        <p>If you are not redirected automatically, <a href="{fallback_url}">click here</a>.</p>
    </body>
    </html>
    """


@router.get("/{short_code}")
async def redirect_dynamic_link(
    short_code: str,
    request: Request,
    db: PostgresDB = Depends(get_db_instance)
):
    """Handle dynamic link redirect with analytics tracking."""

    # Get link from cache or database
    cache_key = f"link:{short_code}"
    cached_link = await cache.get(cache_key)

    if cached_link:
        db_link_data = json.loads(cached_link)
    else:
        query = "SELECT * FROM dynamic_links WHERE short_code = $1 AND is_active = TRUE;"
        db_link = await db.fetchrow(query, short_code)

        if not db_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found or inactive"
            )

        # Check if expired
        if db_link['expires_at'] and db_link['expires_at'] < datetime.utcnow().replace(tzinfo=None):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Link has expired"
            )

        db_link_data = dict(db_link)
        # Cache for future requests
        await cache.set(cache_key, json.dumps(db_link_data, default=str), expire=3600)

    # Extract request information
    user_agent_string = request.headers.get("User-Agent", "")
    client_ip = get_client_ip(request)
    referer = request.headers.get("Referer")

    # Detect platform and device
    platform, device_type, browser, os = detect_platform_and_device(user_agent_string)

    # Get location (if GeoIP is enabled)
    country, region, city = get_location_from_ip(client_ip)

    # Determine redirect URL
    redirect_url = None
    redirect_type = None
    is_mobile = platform in ['iOS', 'Android']

    if not is_mobile:
        if platform == 'Desktop' and db_link_data.get('desktop_url'):
            redirect_url = db_link_data['desktop_url']
            redirect_type = 'desktop'
        else:
            redirect_url = db_link_data['fallback_url']
            redirect_type = 'fallback'
        
        # Add custom parameters for server-side redirects
        if db_link_data.get('custom_parameters'):
            redirect_url = build_redirect_url(redirect_url, db_link_data['custom_parameters'])
    else:
        # For mobile, the final URL is determined client-side.
        # We'll set a placeholder for logging purposes.
        redirect_url = f"html-redirect-for-{platform.lower()}"
        redirect_type = platform.lower()

    # Track analytics (if enabled)
    if settings.enable_analytics:
        query = """
            INSERT INTO link_analytics (
                link_id, short_code, ip_address, user_agent, referer, platform,
                device_type, browser, os, country, region, city, redirected_to, redirect_type
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14);
        """
        await db.execute(
            query,
            db_link_data['id'],
            short_code,
            hash_ip_address(client_ip),  # Hash for privacy
            user_agent_string[:500],  # Truncate if too long
            referer[:500] if referer else None,
            platform,
            device_type,
            browser[:100],
            os[:100],
            country,
            region,
            city,
            redirect_url,
            redirect_type
        )

        # Update click counter in cache
        click_key = f"clicks:{short_code}"
        await cache.increment(click_key)

    if is_mobile:
        html_content = generate_redirect_html(
            ios_url=db_link_data.get('ios_url'),
            android_url=db_link_data.get('android_url'),
            fallback_url=db_link_data.get('fallback_url'),
            social_title=db_link_data.get('social_title'),
            social_description=db_link_data.get('social_description'),
            social_image_url=db_link_data.get('social_image_url')
        )
        return HTMLResponse(content=html_content)
    else:
        # Perform server-side redirect for desktop/other
        return Response(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": redirect_url}
        )


@router.get("/api/v1/analytics/{short_code}", response_model=LinkAnalyticsResponse)
async def get_link_analytics(
    short_code: str,
    days: int = 30,
    db: PostgresDB = Depends(get_db_instance)
):
    """Get analytics for a specific dynamic link."""
    
    # Verify link exists
    link_query = "SELECT 1 FROM dynamic_links WHERE short_code = $1;"
    if not await db.fetchrow(link_query, short_code):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dynamic link not found"
        )

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Total clicks
    total_clicks_query = "SELECT COUNT(*) FROM link_analytics WHERE short_code = $1 AND clicked_at >= $2;"
    total_clicks_result = await db.fetchrow(total_clicks_query, short_code, start_date)
    total_clicks = total_clicks_result['count'] if total_clicks_result else 0

    # Unique clicks (based on hashed IP)
    unique_clicks_query = "SELECT COUNT(DISTINCT ip_address) FROM link_analytics WHERE short_code = $1 AND clicked_at >= $2;"
    unique_clicks_result = await db.fetchrow(unique_clicks_query, short_code, start_date)
    unique_clicks = unique_clicks_result['count'] if unique_clicks_result else 0

    # Clicks by platform
    platform_stats_query = """
        SELECT platform, COUNT(*) as count FROM link_analytics
        WHERE short_code = $1 AND clicked_at >= $2 AND platform IS NOT NULL
        GROUP BY platform;
    """
    platform_stats = await db.fetch(platform_stats_query, short_code, start_date)
    clicks_by_platform = {row['platform']: row['count'] for row in platform_stats}

    # Clicks by country
    country_stats_query = """
        SELECT country, COUNT(*) as count FROM link_analytics
        WHERE short_code = $1 AND clicked_at >= $2 AND country IS NOT NULL
        GROUP BY country ORDER BY count DESC LIMIT 10;
    """
    country_stats = await db.fetch(country_stats_query, short_code, start_date)
    clicks_by_country = {row['country']: row['count'] for row in country_stats}

    # Clicks by date
    date_stats_query = """
        SELECT DATE(clicked_at) as date, COUNT(*) as count FROM link_analytics
        WHERE short_code = $1 AND clicked_at >= $2
        GROUP BY DATE(clicked_at) ORDER BY date;
    """
    date_stats = await db.fetch(date_stats_query, short_code, start_date)
    clicks_by_date = {str(row['date']): row['count'] for row in date_stats}

    # Top referrers
    referrer_stats_query = """
        SELECT referer, COUNT(*) as count FROM link_analytics
        WHERE short_code = $1 AND clicked_at >= $2 AND referer IS NOT NULL
        GROUP BY referer ORDER BY count DESC LIMIT 10;
    """
    referrer_stats = await db.fetch(referrer_stats_query, short_code, start_date)
    top_referrers = {row['referer']: row['count'] for row in referrer_stats}

    return LinkAnalyticsResponse(
        total_clicks=total_clicks,
        unique_clicks=unique_clicks,
        clicks_by_platform=clicks_by_platform,
        clicks_by_country=clicks_by_country,
        clicks_by_date=clicks_by_date,
        top_referrers=top_referrers
    )
