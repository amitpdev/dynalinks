CREATE TABLE dynamic_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    short_code VARCHAR(10) UNIQUE NOT NULL,
    ios_url TEXT,
    android_url TEXT,
    fallback_url TEXT NOT NULL,
    desktop_url TEXT,
    title VARCHAR(255),
    description TEXT,
    image_url TEXT,
    social_title VARCHAR(255),
    social_description TEXT,
    social_image_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    creator_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    custom_parameters JSONB
);

CREATE TABLE link_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id UUID NOT NULL,
    short_code VARCHAR(10) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    referer TEXT,
    platform VARCHAR(50),
    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100),
    country VARCHAR(2),
    region VARCHAR(100),
    city VARCHAR(100),
    redirected_to TEXT,
    redirect_type VARCHAR(20),
    clicked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    custom_data JSONB
);

CREATE INDEX idx_dynamic_links_short_code ON dynamic_links(short_code);
CREATE INDEX idx_link_analytics_link_id ON link_analytics(link_id);
CREATE INDEX idx_link_analytics_short_code ON link_analytics(short_code);
