def header_block(icon, title, subtitle=""):
    """Generate header HTML"""
    return f"""
    <div style="margin: 20px 0;">
        <h1>{icon} {title}</h1>
        {f'<p style="color: #94a3b8;">{subtitle}</p>' if subtitle else ''}
    </div>
    """

def card(title, content):
    """Generate card HTML"""
    return f"""
    <div style="padding: 16px; background: rgba(51, 65, 85, 0.5); 
                border-radius: 12px; margin-bottom: 12px;">
        <h3>{title}</h3>
        <div>{content}</div>
    </div>
    """

def chip(text, color="primary"):
    """Generate chip/badge HTML"""
    colors = {
        "primary": "#6366f1",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444"
    }
    return f'<span style="background: {colors.get(color, colors["primary"])}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">{text}</span>'

def push_browser_notification(title, body):
    """Push browser notification"""
    # Requires JavaScript integration
    pass

def chat_theme_colors(theme_name):
    """Get chat theme colors"""
    themes = {
        "Indigo": {"primary": "#6366f1", "secondary": "#8b5cf6"},
        "Green": {"primary": "#10b981", "secondary": "#059669"}
    }
    return themes.get(theme_name, themes["Indigo"])

def avatar_for(user_name):
    """Generate avatar"""
    return user_name[0].upper() if user_name else "?"

def stat_card(label, value, subtitle=""):
    """Generate stat card"""
    return f"""
    <div style="padding: 16px; background: rgba(51, 65, 85, 0.5); 
                border-radius: 12px; text-align: center;">
        <div style="font-size: 28px; font-weight: 800; color: #6366f1;">{value}</div>
        <div style="font-size: 13px; opacity: 0.8;">{label}</div>
        {f'<div style="font-size: 11px; opacity: 0.6; margin-top: 4px;">{subtitle}</div>' if subtitle else ''}
    </div>
    """