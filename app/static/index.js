document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();

    // DOM Elements
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");

    // Model Selector
    const modelSelect = document.getElementById("model-select");

    // Action Buttons
    const btnExportMarkdown = document.getElementById("btn-export-markdown");
    const btnCompactMemories = document.getElementById("btn-compact-memories");

    // Modal Add Memory
    const addMemoryModal = document.getElementById("add-memory-modal");
    const btnAddMemoryModal = document.getElementById("btn-add-memory-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const btnCancelMemory = document.getElementById("btn-cancel-memory");
    const btnSaveMemory = document.getElementById("btn-save-memory");

    const modalTabBtns = document.querySelectorAll(".modal-tab-btn");
    const modalTabContents = document.querySelectorAll(".modal-tab-content");

    // Form fields
    const autoMemoryContent = document.getElementById("auto-memory-content");
    const autoMemoryTtl = document.getElementById("auto-memory-ttl");
    const uploadMemoryFile = document.getElementById("upload-memory-file");
    const uploadMemoryDesc = document.getElementById("upload-memory-desc");
    const manualMemoryContent = document.getElementById("manual-memory-content");
    const manualMemoryCategory = document.getElementById("manual-memory-category");
    const manualMemoryImportance = document.getElementById("manual-memory-importance");
    const manualMemoryTags = document.getElementById("manual-memory-tags");

    // Edit Form fields
    const editMemoryModal = document.getElementById("edit-memory-modal");
    const btnCloseEditModal = document.getElementById("btn-close-edit-modal");
    const btnCancelEditMemory = document.getElementById("btn-cancel-edit-memory");
    const btnUpdateMemory = document.getElementById("btn-update-memory");
    const editMemoryId = document.getElementById("edit-memory-id");
    const editMemoryContent = document.getElementById("edit-memory-content");
    const editMemoryCategory = document.getElementById("edit-memory-category");
    const editMemoryImportance = document.getElementById("edit-memory-importance");
    const editMemoryTags = document.getElementById("edit-memory-tags");

    // Board & Graph Elements
    const memoriesContainer = document.getElementById("memories-container");
    const memorySearchInput = document.getElementById("memory-search-input");
    const graphVisualizationContainer = document.getElementById("graph-visualization-container");

    // Chat Elements
    const chatMessagesBox = document.getElementById("chat-messages-box");
    const chatQueryInput = document.getElementById("chat-query-input");
    const btnSendChat = document.getElementById("btn-send-chat");
    const retrievalBreakdownContainer = document.getElementById("retrieval-breakdown-container");

    // Stats Elements
    const statTotalMemories = document.getElementById("stat-total-memories");
    const statTotalCategories = document.getElementById("stat-total-categories");
    const statAvgImportance = document.getElementById("stat-avg-importance");
    const categoryDistributionList = document.getElementById("category-distribution-list");

    let currentAddMode = "auto";

    // Tab Navigation
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");
            
            navItems.forEach(n => n.classList.remove("active"));
            tabPanes.forEach(t => t.classList.remove("active"));
            
            item.classList.add("active");
            document.getElementById(`tab-${tabId}`).classList.add("active");

            if (tabId === "dashboard") {
                pageTitle.textContent = "Dashboard Overview";
                pageSubtitle.textContent = "Real-time memory stats and hybrid retrieval analytics.";
                loadDashboardStats();
            } else if (tabId === "memories") {
                pageTitle.textContent = "Memory Board";
                pageSubtitle.textContent = "Browse, search, edit, and organize persistent context.";
                loadMemories();
            } else if (tabId === "graph") {
                pageTitle.textContent = "Knowledge Graph";
                pageSubtitle.textContent = "Entity relationships extracted from stored context (Graph-RAG).";
                loadKnowledgeGraph();
            } else if (tabId === "chat") {
                pageTitle.textContent = "Orchestrator Chat";
                pageSubtitle.textContent = "Ask questions powered by adaptive context and real-time streaming.";
            }
        });
    });

    // Modal Tab Switching
    modalTabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const mode = btn.getAttribute("data-mode");
            modalTabBtns.forEach(b => b.classList.remove("active"));
            modalTabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(`mode-${mode}`).classList.add("active");
            currentAddMode = mode;
        });
    });

    // Open/Close Modals
    btnAddMemoryModal.addEventListener("click", () => {
        autoMemoryContent.value = "";
        autoMemoryTtl.value = "";
        uploadMemoryFile.value = "";
        uploadMemoryDesc.value = "";
        manualMemoryContent.value = "";
        manualMemoryCategory.value = "";
        manualMemoryImportance.value = "0.5";
        manualMemoryTags.value = "";
        
        addMemoryModal.classList.add("active");
    });

    const closeAddModal = () => addMemoryModal.classList.remove("active");
    btnCloseModal.addEventListener("click", closeAddModal);
    btnCancelMemory.addEventListener("click", closeAddModal);

    const closeEditModal = () => editMemoryModal.classList.remove("active");
    btnCloseEditModal.addEventListener("click", closeEditModal);
    btnCancelEditMemory.addEventListener("click", closeEditModal);

    // Export Markdown Action
    btnExportMarkdown.addEventListener("click", () => {
        window.location.href = "/api/memories/export";
    });

    // Compact Memories Action
    btnCompactMemories.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to synthesize and compact redundant memories into consolidated entries?")) {
            return;
        }
        btnCompactMemories.disabled = true;
        btnCompactMemories.textContent = "Compacting...";
        try {
            const response = await fetch("/api/memories/compact", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({})
            });
            if (response.ok) {
                alert("Memories compacted successfully!");
                loadMemories();
            } else {
                const err = await response.json();
                alert(`Compaction error: ${err.detail || "Could not compact memories"}`);
            }
        } catch (e) {
            console.error("Compaction error:", e);
        } finally {
            btnCompactMemories.disabled = false;
            btnCompactMemories.innerHTML = '<i data-lucide="zap"></i> Compact Redundant Notes';
            lucide.createIcons();
        }
    });

    // Save Memory Action
    btnSaveMemory.addEventListener("click", async () => {
        btnSaveMemory.disabled = true;
        btnSaveMemory.textContent = "Saving...";

        try {
            if (currentAddMode === "upload") {
                const file = uploadMemoryFile.files[0];
                if (!file) {
                    alert("Please select a file to upload.");
                    btnSaveMemory.disabled = false;
                    btnSaveMemory.textContent = "Save Memory";
                    return;
                }
                const formData = new FormData();
                formData.append("file", file);
                formData.append("description", uploadMemoryDesc.value.trim());

                const response = await fetch("/api/memories/upload", {
                    method: "POST",
                    body: formData
                });
                if (response.ok) {
                    closeAddModal();
                    loadMemories();
                } else {
                    const err = await response.json();
                    alert(`Error: ${err.detail || "Could not upload file memory"}`);
                }
            } else if (currentAddMode === "auto") {
                const content = autoMemoryContent.value.trim();
                const ttl = parseFloat(autoMemoryTtl.value) || null;
                if (!content) {
                    alert("Memory content cannot be empty.");
                    btnSaveMemory.disabled = false;
                    btnSaveMemory.textContent = "Save Memory";
                    return;
                }
                const response = await fetch("/api/memories/auto", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content, ttl_days: ttl })
                });
                if (response.ok) {
                    closeAddModal();
                    loadMemories();
                } else {
                    const err = await response.json();
                    alert(`Error: ${err.detail || "Could not save memory"}`);
                }
            } else {
                const content = manualMemoryContent.value.trim();
                const category = manualMemoryCategory.value.trim() || "general";
                const importance = parseFloat(manualMemoryImportance.value) || 0.5;
                const tagsText = manualMemoryTags.value.trim();
                const tags = tagsText ? tagsText.split(",").map(t => t.trim()).filter(t => t) : [];

                if (!content) {
                    alert("Memory content cannot be empty.");
                    btnSaveMemory.disabled = false;
                    btnSaveMemory.textContent = "Save Memory";
                    return;
                }
                const response = await fetch("/api/memories", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content, category, importance, tags })
                });
                if (response.ok) {
                    closeAddModal();
                    loadMemories();
                } else {
                    const err = await response.json();
                    alert(`Error: ${err.detail || "Could not save memory"}`);
                }
            }
        } catch (error) {
            console.error("Save memory error:", error);
            alert("Network error.");
        } finally {
            btnSaveMemory.disabled = false;
            btnSaveMemory.textContent = "Save Memory";
        }
    });

    // Update Memory Action
    btnUpdateMemory.addEventListener("click", async () => {
        const id = editMemoryId.value;
        const content = editMemoryContent.value.trim();
        const category = editMemoryCategory.value.trim();
        const importance = parseFloat(editMemoryImportance.value);
        const tagsText = editMemoryTags.value.trim();
        const tags = tagsText ? tagsText.split(",").map(t => t.trim()).filter(t => t) : [];

        if (!content) {
            alert("Memory content cannot be empty.");
            return;
        }

        btnUpdateMemory.disabled = true;
        btnUpdateMemory.textContent = "Updating...";

        try {
            const response = await fetch(`/api/memories/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content, category, importance, tags })
            });

            if (response.ok) {
                closeEditModal();
                loadMemories();
            } else {
                const err = await response.json();
                alert(`Error: ${err.detail || "Could not update memory"}`);
            }
        } catch (error) {
            console.error("Update memory error:", error);
            alert("Network error.");
        } finally {
            btnUpdateMemory.disabled = false;
            btnUpdateMemory.textContent = "Update Memory";
        }
    });

    // Delete Memory Action
    window.deleteMemory = async (id) => {
        if (!confirm("Are you sure you want to delete this memory? It will be permanently removed from context.")) {
            return;
        }
        try {
            const response = await fetch(`/api/memories/${id}`, { method: "DELETE" });
            if (response.ok) {
                loadMemories();
            } else {
                alert("Could not delete memory.");
            }
        } catch (error) {
            console.error("Delete error:", error);
        }
    };

    // Edit Memory Triggers
    window.triggerEditMemory = (id, content, category, importance, tagsString) => {
        editMemoryId.value = id;
        editMemoryContent.value = content;
        editMemoryCategory.value = category;
        editMemoryImportance.value = importance;
        editMemoryTags.value = tagsString;
        
        editMemoryModal.classList.add("active");
    };

    // Load Memories (Board View)
    async function loadMemories(searchQuery = "") {
        memoriesContainer.innerHTML = '<p class="empty-state">Loading memories...</p>';
        try {
            const url = searchQuery ? `/api/memories?search=${encodeURIComponent(searchQuery)}` : "/api/memories";
            const response = await fetch(url);
            const memories = await response.json();

            if (memories.length === 0) {
                memoriesContainer.innerHTML = '<p class="empty-state">No matching memories found.</p>';
                return;
            }

            memoriesContainer.innerHTML = memories.map(m => {
                const tagsList = m.tags || [];
                const tagsHtml = tagsList.map(t => `<span class="tag">#${t}</span>`).join(" ");
                const timestampText = new Date(m.timestamp * 1000).toLocaleString();
                const tagsStringEscaped = tagsList.join(", ").replace(/"/g, '&quot;');
                const contentEscaped = m.content.replace(/"/g, '&quot;').replace(/'/g, "\\'");
                const fileHtml = m.file_url ? `<div style="margin-top:8px;"><a href="${m.file_url}" target="_blank" style="color:var(--cyan); font-size:0.8rem;">📁 Attached Asset</a></div>` : "";

                return `
                    <div class="memory-card">
                        <div class="memory-card-header">
                            <span class="memory-category">${m.category}</span>
                            <span class="memory-importance">
                                <i data-lucide="award"></i> ${m.importance.toFixed(1)}
                            </span>
                        </div>
                        <div class="memory-content">${m.content}</div>
                        ${fileHtml}
                        <div class="memory-tags">${tagsHtml}</div>
                        <div class="memory-card-footer">
                            <span class="memory-time">${timestampText}</span>
                            <div class="card-actions">
                                <button class="btn-icon" onclick="triggerEditMemory(${m.id}, '${contentEscaped}', '${m.category}', ${m.importance}, '${tagsStringEscaped}')" title="Edit">
                                    <i data-lucide="edit-3" style="width: 14px; height: 14px;"></i>
                                </button>
                                <button class="btn-icon" onclick="deleteMemory(${m.id})" title="Delete" style="color: var(--error);">
                                    <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join("");

            lucide.createIcons();
        } catch (error) {
            console.error("Load memories error:", error);
            memoriesContainer.innerHTML = '<p class="empty-state" style="color: var(--error)">Could not fetch memories from API.</p>';
        }
    }

    // Load Knowledge Graph
    async function loadKnowledgeGraph() {
        graphVisualizationContainer.innerHTML = '<p class="empty-state">Loading knowledge graph...</p>';
        try {
            const response = await fetch("/api/graph");
            const data = await response.json();
            const nodes = data.nodes || [];
            const edges = data.edges || [];

            if (nodes.length === 0) {
                graphVisualizationContainer.innerHTML = '<p class="empty-state">No entity graph connections established yet.</p>';
                return;
            }

            graphVisualizationContainer.innerHTML = `
                <div class="graph-nodes-list" style="display:flex; flex-direction:column; gap:12px;">
                    ${nodes.map(n => `
                        <div style="background: rgba(255,255,255,0.03); border:1px solid var(--border-glass); padding:12px; border-radius:8px;">
                            <div style="display:flex; justify-content:space-between;">
                                <strong style="color: var(--accent);">Node #${n.id}</strong>
                                <span class="category-badge badge-default">${n.category}</span>
                            </div>
                            <p style="margin-top:4px; font-size:0.85rem; color: var(--text-muted);">${n.label}</p>
                        </div>
                    `).join("")}
                </div>
            `;
        } catch (e) {
            console.error("Load graph error:", e);
            graphVisualizationContainer.innerHTML = '<p class="empty-state" style="color: var(--error)">Could not load graph data.</p>';
        }
    }

    let searchTimeout;
    memorySearchInput.addEventListener("input", (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            loadMemories(e.target.value.trim());
        }, 300);
    });

    async function loadDashboardStats() {
        try {
            const response = await fetch("/api/stats");
            const stats = await response.json();

            statTotalMemories.textContent = stats.total_memories;
            statAvgImportance.textContent = stats.total_memories > 0 ? stats.avg_importance.toFixed(2) : "0.00";
            
            const categories = Object.keys(stats.categories || {});
            statTotalCategories.textContent = categories.length;

            if (categories.length === 0) {
                categoryDistributionList.innerHTML = '<p class="empty-state">No categories defined yet.</p>';
                return;
            }

            categoryDistributionList.innerHTML = categories.map(cat => {
                const count = stats.categories[cat];
                return `
                    <div class="category-row">
                        <span class="category-badge badge-default">${cat}</span>
                        <span class="category-count">${count} items</span>
                    </div>
                `;
            }).join("");

        } catch (error) {
            console.error("Load stats error:", error);
        }
    }

    // Real-Time Token Streaming Chat Message
    async function sendChatMessage() {
        const query = chatQueryInput.value.trim();
        const selectedModel = modelSelect.value;
        if (!query) return;

        chatQueryInput.value = "";

        const userMsgHtml = `
            <div class="message user-message">
                <div class="message-avatar">
                    <i data-lucide="user"></i>
                </div>
                <div class="message-bubble">
                    ${query}
                </div>
            </div>
        `;
        chatMessagesBox.insertAdjacentHTML("beforeend", userMsgHtml);
        chatMessagesBox.scrollTop = chatMessagesBox.scrollHeight;
        lucide.createIcons();

        // Assistant streaming bubble
        const msgId = "msg-assistant-" + Date.now();
        const assistantMsgHtml = `
            <div class="message assistant-message" id="${msgId}">
                <div class="message-avatar">
                    <i data-lucide="bot"></i>
                </div>
                <div class="message-bubble" id="${msgId}-bubble">
                    <span class="pulse-dot" style="display:inline-block; vertical-align: middle;"></span>
                    <span style="margin-left: 8px; font-size: 0.85rem; color: var(--text-muted);">Retrieving context & streaming...</span>
                </div>
            </div>
        `;
        chatMessagesBox.insertAdjacentHTML("beforeend", assistantMsgHtml);
        chatMessagesBox.scrollTop = chatMessagesBox.scrollHeight;
        lucide.createIcons();

        const bubbleEl = document.getElementById(`${msgId}-bubble`);
        let firstTokenReceived = false;

        try {
            const response = await fetch("/api/chat/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query, model_name: selectedModel })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        const jsonStr = line.replace("data: ", "").trim();
                        if (!jsonStr) continue;
                        try {
                            const parsed = JSON.parse(jsonStr);
                            if (parsed.type === "breakdown") {
                                renderRetrievalBreakdown(parsed.data);
                            } else if (parsed.type === "token") {
                                if (!firstTokenReceived) {
                                    bubbleEl.innerHTML = "";
                                    firstTokenReceived = true;
                                }
                                bubbleEl.innerHTML += parsed.data.replace(/\n/g, "<br>");
                                chatMessagesBox.scrollTop = chatMessagesBox.scrollHeight;
                            }
                        } catch (e) {
                            console.error("SSE parse error:", e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Chat Streaming API error:", error);
            bubbleEl.innerHTML = '<span style="color: var(--error)">Connection error streaming response.</span>';
        }
    }

    function renderRetrievalBreakdown(retrieved) {
        if (!retrieved || retrieved.length === 0) {
            retrievalBreakdownContainer.innerHTML = '<p class="empty-state">No context memories matched for this query.</p>';
            return;
        }

        retrievalBreakdownContainer.innerHTML = retrieved.map(item => {
            const m = item.memory;
            const b = item.breakdown || {};
            const similarity = b.similarity || 0;
            const importance = b.importance || 0;
            const recency = b.recency || 0;
            const score = item.score || 0;

            return `
                <div class="retrieval-card">
                    <div class="retrieval-card-meta">
                        <span class="memory-category" style="font-size: 0.65rem; padding: 2px 8px;">${m.category}</span>
                        <span class="retrieval-score">Score: ${score.toFixed(3)}</span>
                    </div>
                    <div class="retrieval-card-content">
                        "${m.content}"
                    </div>
                    <div class="score-bars">
                        <div class="score-bar-row">
                            <span>Similarity (50%):</span>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span>${similarity.toFixed(2)}</span>
                                <div class="score-progress"><div class="score-fill" style="width: ${similarity * 100}%; background: var(--cyan);"></div></div>
                            </div>
                        </div>
                        <div class="score-bar-row">
                            <span>Importance (30%):</span>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span>${importance.toFixed(2)}</span>
                                <div class="score-progress"><div class="score-fill" style="width: ${importance * 100}%; background: var(--primary);"></div></div>
                            </div>
                        </div>
                        <div class="score-bar-row">
                            <span>Recency (20%):</span>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span>${recency.toFixed(2)}</span>
                                <div class="score-progress"><div class="score-fill" style="width: ${recency * 100}%; background: var(--accent);"></div></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join("");
    }

    btnSendChat.addEventListener("click", sendChatMessage);
    chatQueryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            sendChatMessage();
        }
    });

    loadDashboardStats();
});
