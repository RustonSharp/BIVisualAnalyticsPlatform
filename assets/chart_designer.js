(function () {
    const HIDDEN_INPUT_ID = "dnd-last-event";
    const FIELD_CONTAINER_ID = "field-list";
    const DROP_ZONES = ["drop-x-axis", "drop-y-axis", "drop-group"];

    function getHiddenInput() {
        return document.getElementById(HIDDEN_INPUT_ID);
    }

    function notifyDrop(targetId, fieldName) {
        const hiddenInput = getHiddenInput();
        if (!hiddenInput || !fieldName) {
            return;
        }
        hiddenInput.value = JSON.stringify({
            field: fieldName,
            target: targetId,
            timestamp: Date.now()
        });
        hiddenInput.dispatchEvent(new Event("input", { bubbles: true }));
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
                event.dataTransfer.setData("text/plain", element.getAttribute("data-field"));
                event.dataTransfer.effectAllowed = "move";
            });
            element.dataset.initialized = "true";
        });
    }

    function setupDropZones() {
        DROP_ZONES.forEach(function (zoneId) {
            const zone = document.getElementById(zoneId);
            if (!zone || zone.dataset.initialized === "true") {
                return;
            }
            zone.addEventListener("dragover", function (event) {
                event.preventDefault();
                event.dataTransfer.dropEffect = "move";
            });
            zone.addEventListener("dragenter", function () {
                zone.classList.add("drop-zone-active");
            });
            zone.addEventListener("dragleave", function (event) {
                if (!zone.contains(event.relatedTarget)) {
                    zone.classList.remove("drop-zone-active");
                }
            });
            zone.addEventListener("drop", function (event) {
                event.preventDefault();
                zone.classList.remove("drop-zone-active");
                const field = event.dataTransfer.getData("text/plain");
                notifyDrop(zoneId, field);
            });
            zone.dataset.initialized = "true";
        });
    }

    function initDragAndDrop() {
        setupDragSources();
        setupDropZones();
    }

    const observer = new MutationObserver(function () {
        initDragAndDrop();
    });

    document.addEventListener("DOMContentLoaded", function () {
        initDragAndDrop();
        observer.observe(document.body, { childList: true, subtree: true });
    });
})();
