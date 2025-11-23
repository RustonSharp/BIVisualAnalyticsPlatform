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

.drop-zone {
    transition: all 0.3s;
}

.drop-zone:hover {
    background-color: #f8f9fa;
    border-color: #007bff !important;
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

# JavaScript拖拽功能代码
DRAG_DROP_SCRIPT = """
<script>
// 拖拽功能实现
(function() {
    let draggedElement = null;
    
    // 延迟初始化，等待Dash应用加载完成
    function initDragDrop() {
        // 处理字段拖拽开始
        document.addEventListener('dragstart', function(e) {
            const field = e.target.closest('.draggable-field');
            if (field) {
                draggedElement = field;
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', '');
                field.style.opacity = '0.5';
            }
        }, true);
        
        // 处理拖拽结束
        document.addEventListener('dragend', function(e) {
            if (draggedElement) {
                draggedElement.style.opacity = '1';
                draggedElement = null;
            }
        }, true);
        
        // 处理放置区域的拖拽悬停
        document.addEventListener('dragover', function(e) {
            const dropZone = e.target.closest('.drop-zone');
            if (dropZone && draggedElement) {
                e.preventDefault();
                e.stopPropagation();
                e.dataTransfer.dropEffect = 'move';
                dropZone.style.backgroundColor = '#e3f2fd';
                dropZone.style.borderColor = '#2196f3';
            }
        }, true);
        
        // 处理离开放置区域
        document.addEventListener('dragleave', function(e) {
            const dropZone = e.target.closest('.drop-zone');
            if (dropZone) {
                dropZone.style.backgroundColor = '';
                dropZone.style.borderColor = '';
            }
        }, true);
        
        // 处理放置事件
        document.addEventListener('drop', function(e) {
            const dropZone = e.target.closest('.drop-zone');
            if (dropZone && draggedElement) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.style.backgroundColor = '';
                dropZone.style.borderColor = '';
                
                const fieldName = draggedElement.getAttribute('data-field');
                const targetId = dropZone.id;
                
                // 更新隐藏输入框的值
                const eventData = JSON.stringify({
                    field: fieldName,
                    target: targetId
                });
                
                // 使用Dash的方式更新输入框并触发回调
                const dndInput = document.getElementById('dnd-last-event');
                if (dndInput) {
                    // 创建一个唯一的时间戳，确保Dash检测到变化
                    const timestamp = Date.now();
                    const newValue = eventData + '|' + timestamp;
                    
                    // 使用原生输入值设置器来触发React的onChange（Dash使用React）
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(dndInput, newValue);
                    
                    // 触发input事件（React会监听这个事件）
                    const inputEvent = new Event('input', { bubbles: true, cancelable: true });
                    dndInput.dispatchEvent(inputEvent);
                    
                    // 触发change事件
                    const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                    dndInput.dispatchEvent(changeEvent);
                    
                    // 尝试触发React的合成事件（如果Dash使用React）
                    const syntheticInputEvent = new Event('input', { bubbles: true });
                    Object.defineProperty(syntheticInputEvent, 'target', {
                        writable: false,
                        value: dndInput
                    });
                    dndInput.dispatchEvent(syntheticInputEvent);
                    
                    // 如果有Dash的客户端回调API，直接调用
                    if (window.dash_clientside && typeof window.dash_clientside.call_clientside_callback === 'function') {
                        try {
                            // 尝试调用客户端回调
                            window.dash_clientside.call_clientside_callback('dnd-last-event', 'value', newValue);
                        } catch (e) {
                            console.log('Could not call dash clientside callback directly');
                        }
                    }
                    
                    // 额外尝试：直接通过Dash的Props设置（如果可用）
                    if (window.dash && window.dash.setProps) {
                        try {
                            window.dash.setProps('dnd-last-event', { value: newValue });
                        } catch (e) {
                            console.log('Could not use dash.setProps');
                        }
                    }
                    
                    console.log('Drag drop event sent:', eventData);
                }
                
                draggedElement = null;
            }
        }, true);
    }
    
    // 等待DOM和Dash加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDragDrop);
    } else {
        // DOM已经加载完成，延迟一点确保Dash也加载完成
        setTimeout(initDragDrop, 100);
    }
})();
</script>
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
        {DRAG_DROP_SCRIPT}
    </body>
</html>
"""

