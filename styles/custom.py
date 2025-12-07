"""自定义样式和脚本"""
CUSTOM_CSS = """
.nav-link-custom {
    padding: 0.75rem 1rem;
    margin-bottom: 0.25rem;
    border-radius: 0.25rem;
    color: #495057;
    transition: all 0.2s;
}

.nav-link-custom:hover {
    background-color: #e9ecef;
    color: #007bff;
}

.nav-link-custom.active {
    background-color: #007bff;
    color: white;
}


.card {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border: none;
}

.card-header {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    font-weight: 600;
}

.badge {
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
}

body {
    background-color: #ffffff;
}
"""



def get_index_string():
    """获取 Dash 应用的 index_string"""
    return f"""
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            {CUSTOM_CSS}
        </style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
"""

