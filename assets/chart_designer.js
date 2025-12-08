(function () {
    const HIDDEN_INPUT_ID = "dnd-last-event";
    const FIELD_CONTAINER_ID = "field-list";

    function notifyDrop(targetId, fieldName) {
        if (!fieldName) {
            console.warn("拖拽通知失败: fieldName为空");
            return;
        }
        
        const eventData = {
            field: fieldName,
            target: targetId,
            timestamp: Date.now()
        };
        const eventJson = JSON.stringify(eventData);
        
        console.log("准备发送拖拽事件:", eventData);
        
        const triggerButton = document.getElementById("dnd-event-trigger");
        
        if (!triggerButton) {
            console.error("找不到dnd-event-trigger按钮");
            return;
        }
        
        try {
            // 将事件数据存储到全局变量
            window._dndEventData = eventJson;
            console.log("事件数据已存储到全局变量:", eventJson);
            
            // 触发按钮点击，ClientsideCallback会读取全局变量
            setTimeout(function() {
                triggerButton.click();
                console.log("已触发按钮点击，ClientsideCallback应该会读取全局变量");
            }, 10);
        } catch (e) {
            console.error("发送拖拽事件失败:", e);
        }
    }

    function getDropZoneId(element) {
        // 优先使用ID属性
        if (element.id) {
            let id = element.id;
            
            // 处理Dash的动态ID格式：{"type":"drop-table-col","index":1}
            // 将其转换为Python代码期望的格式：drop-table-col-1
            try {
                // 尝试解析JSON格式的ID
                if (id.startsWith('{') && id.includes('"type"')) {
                    const parsed = JSON.parse(id);
                    if (parsed.type === "drop-table-col" && parsed.index !== undefined) {
                        return `drop-table-col-${parsed.index}`;
                    } else if (parsed.type === "drop-table-row" && parsed.index !== undefined) {
                        return `drop-table-row-${parsed.index}`;
                    }
                }
            } catch (e) {
                // 不是JSON格式，继续使用原始ID
            }
            
            return id;
        }
        // 如果没有ID，尝试从data属性获取
        if (element.dataset && element.dataset.targetId) {
            return element.dataset.targetId;
        }
        // 如果都没有，返回null
        return null;
    }

    function setupDragSources() {
        const container = document.getElementById(FIELD_CONTAINER_ID);
        if (!container) {
            return;
        }
        container.querySelectorAll(".draggable-field").forEach(function (element) {
            if (element.dataset.initialized === "true") {
                return;
            }
            element.setAttribute("draggable", "true");
            element.addEventListener("dragstart", function (event) {
                const fieldName = element.getAttribute("data-field");
                console.log("开始拖拽字段:", fieldName);
                event.dataTransfer.setData("text/plain", fieldName);
                event.dataTransfer.effectAllowed = "move";
            });
            element.dataset.initialized = "true";
        });
    }

    function setupDropZones() {
        // 查找所有带有 drop-zone class 的元素
        const dropZones = document.querySelectorAll(".drop-zone");
        dropZones.forEach(function (zone) {
            // 如果已经初始化过，跳过
            if (zone.dataset.initialized === "true") {
                return;
            }
            
            // 获取拖拽区域的ID
            const zoneId = getDropZoneId(zone);
            if (!zoneId) {
                // 如果没有ID，跳过这个区域
                return;
            }

            // 创建事件处理函数（使用闭包保存zoneId）
            const handleDragOver = function (event) {
                event.preventDefault();
                event.dataTransfer.dropEffect = "move";
            };
            
            const handleDragEnter = function (event) {
                event.preventDefault();
                zone.classList.add("drop-zone-active");
            };
            
            const handleDragLeave = function (event) {
                // 只有当鼠标真正离开拖拽区域时才移除高亮
                if (!zone.contains(event.relatedTarget)) {
                    zone.classList.remove("drop-zone-active");
                }
            };
            
            const handleDrop = function (event) {
                event.preventDefault();
                event.stopPropagation();
                zone.classList.remove("drop-zone-active");
                const field = event.dataTransfer.getData("text/plain");
                console.log("拖拽放置事件:", { zoneId: zoneId, field: field });
                if (field) {
                    notifyDrop(zoneId, field);
                } else {
                    console.warn("拖拽事件中没有字段数据");
                }
            };
            
            // 绑定事件监听器
            zone.addEventListener("dragover", handleDragOver);
            zone.addEventListener("dragenter", handleDragEnter);
            zone.addEventListener("dragleave", handleDragLeave);
            zone.addEventListener("drop", handleDrop);
            
            // 标记为已初始化
            zone.dataset.initialized = "true";
        });
    }

    function initDragAndDrop() {
        setupDragSources();
        setupDropZones();
    }

    // 使用防抖来避免频繁调用
    let initTimeout = null;
    function debouncedInit() {
        if (initTimeout) {
            clearTimeout(initTimeout);
        }
        initTimeout = setTimeout(function () {
            initDragAndDrop();
        }, 100);
    }

    const observer = new MutationObserver(function (mutations) {
        // 检查是否有新的拖拽区域或字段被添加
        let shouldInit = false;
        mutations.forEach(function (mutation) {
            if (mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.classList && (
                            node.classList.contains("drop-zone") ||
                            node.classList.contains("draggable-field") ||
                            node.querySelector(".drop-zone") ||
                            node.querySelector(".draggable-field")
                        )) {
                            shouldInit = true;
                        }
                    }
                });
            }
        });
        if (shouldInit) {
            debouncedInit();
        }
    });

    // 添加错误边界：监听focus事件，记录可能触发扩展错误的元素
    function setupErrorBoundary() {
        document.addEventListener("focusin", function(event) {
            const target = event.target;
            if (target && (target.tagName === "INPUT" || target.tagName === "SELECT" || target.tagName === "TEXTAREA")) {
                // 检查元素是否有正确的结构
                const hasId = target.id && target.id !== "";
                const hasName = target.name && target.name !== "";
                const hasLabel = target.labels && target.labels.length > 0;
                
                // 如果元素缺少关键属性，记录警告（但不阻止默认行为）
                if (!hasId || !hasName) {
                    console.debug("输入字段缺少属性:", {
                        id: target.id,
                        name: target.name,
                        tagName: target.tagName,
                        hasLabel: hasLabel
                    });
                }
            }
        }, true); // 使用捕获阶段以便更早捕获事件
    }

    // 页面加载完成后初始化
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            initDragAndDrop();
            setupErrorBoundary();
            observer.observe(document.body, { childList: true, subtree: true });
        });
    } else {
        // DOM已经加载完成
        initDragAndDrop();
        setupErrorBoundary();
        observer.observe(document.body, { childList: true, subtree: true });
    }
})();
