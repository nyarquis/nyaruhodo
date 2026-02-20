document.addEventListener("DOMContentLoaded", function() {
    
    const menuToggle = document.querySelector(".menu-toggle");

    if (menuToggle) {
        menuToggle.addEventListener("click", (event) => {
            event.stopPropagation();
            document.body.classList.toggle("menu-open");
        });

        document.addEventListener("click", (event) => {
            if (document.body.classList.contains("menu-open")) {
                const navLinks = document.querySelector(".nav-links");
                if (navLinks && !navLinks.contains(event.target) && !menuToggle.contains(event.target)) {
                    document.body.classList.remove("menu-open");
                }
            }
        });
    }

    const uploadForm = document.getElementById("uploadForm");
    
    if (uploadForm) {
        const fileInput = document.getElementById("fileInput");
        const dropZone = document.getElementById("dropZone");
        const fileNameDisplay = document.getElementById("fileNameDisplay");
        const loadingIndicator = document.getElementById("loadingIndicator");
        const resultsContainer = document.getElementById("resultsContainer");
        const resultContent = document.getElementById("resultContent");

        fileInput.addEventListener("change", function() {
            if (this.files && this.files[0]) {
                fileNameDisplay.textContent = this.files[0].name;
                fileNameDisplay.style.fontWeight = "bold";
            } else {
                fileNameDisplay.innerHTML = "<strong>Click to upload</strong> or drag and drop";
            }
        });

        if (dropZone) {
            dropZone.addEventListener("click", (event) => {
                if (event.target === dropZone) {
                    fileInput.click();
                }
            });

            ["dragenter", "dragover"].forEach(eventName => {
                dropZone.addEventListener(eventName, (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    dropZone.classList.add("dragover");
                }, false);
            });

            ["dragleave", "drop"].forEach(eventName => {
                dropZone.addEventListener(eventName, (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    dropZone.classList.remove("dragover");
                }, false);
            });

            dropZone.addEventListener("drop", (event) => {
                const transfer = event.dataTransfer;
                const droppedFiles = transfer.files;
                if (droppedFiles && droppedFiles[0]) {
                    fileInput.files = droppedFiles;
                    fileNameDisplay.textContent = droppedFiles[0].name;
                    fileNameDisplay.style.fontWeight = "bold";
                }
            });
        }

        uploadForm.addEventListener("submit", function(event) {
            event.preventDefault();
            
            resultsContainer.style.display = "none";
            loadingIndicator.style.display = "block";

            const formData = new FormData(uploadForm);

            fetch("/dashboard/scan", {
                method: "POST",
                body: formData
            })
            .then(response => response.json())
            .then(result => {
                loadingIndicator.style.display = "none";
                if (result.error) {
                    displayError(result.error);
                } else {
                    displayResults(result);
                }
            })
            .catch(error => {
                loadingIndicator.style.display = "none";
                displayError("An error occurred while connecting to the server.");
                console.error("Error:", error);
            });
        });
    }

    const themeToggleBtn = document.getElementById("theme-toggle-link");
    const themeStylesheet = document.getElementById("current-theme");

    if (themeToggleBtn && themeStylesheet) {
        const savedTheme = localStorage.getItem("theme") || "light";
        applyTheme(savedTheme);

        themeToggleBtn.addEventListener("click", (event) => {
            event.preventDefault();
            const isLight = themeStylesheet.getAttribute("href").includes("light-mode.css");
            const newTheme = isLight ? "night" : "light";
            applyTheme(newTheme);
            localStorage.setItem("theme", newTheme);
        });

        function applyTheme(theme) {
            if (theme === "night") {
                if (themeStylesheet.href.includes("light-mode")) {
                    themeStylesheet.href = themeStylesheet.href.replace("light-mode", "night-mode");
                }
                themeToggleBtn.textContent = "Switch to Light Mode";
            } else {
                if (themeStylesheet.href.includes("night-mode")) {
                    themeStylesheet.href = themeStylesheet.href.replace("night-mode", "light-mode");
                }
                themeToggleBtn.textContent = "Switch to Night Mode";
            }
        }
    }

    function displayResults(result) {
        const container = document.getElementById("resultsContainer");
        const content = document.getElementById("resultContent");
        if (!container || !content) return;

        container.style.display = "block";
        
        let statusClass, title;
        if (result.filetype === "UNKNOWN") {
            statusClass = "unknown";
            title = "Unknown File Type";
        } else if (result.mismatch) {
            statusClass = "mismatch";
            title = "Mismatch Detected";
        } else {
            statusClass = "match";
            title = "Extension Matches";
        }
            
        let markup = `
            <div class="result-box ${statusClass}">
                <h3 style="margin-bottom: 1rem;">${title}</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
                    <div><strong>File Name:</strong><br><span style="color: #4c4f69;">${escapeHtml(result.filename)}</span></div>
                    <div><strong>Claimed:</strong><br><span style="color: #4c4f69;">${escapeHtml(result.extension)}</span></div>
                    <div><strong>Detected:</strong><br><span style="color: #4c4f69;">${escapeHtml(result.filetype)}</span></div>
                    <div><strong>Type:</strong><br><span style="color: #4c4f69;">${escapeHtml(result.description)}</span></div>
                </div>
                <div style="margin-top: 1rem; border-top: 1px solid #e6e9ef; padding-top: 1rem;">
                    <strong>Analysis:</strong> ${escapeHtml(result.message)}
                </div>
            </div>
        `;

        if (result.metadata && Object.keys(result.metadata).length > 0) {
            markup += formatMetadata(result.metadata);
        }

        if (result.virustotal) {
            markup += formatVirusTotal(result.virustotal);
        }

        content.innerHTML = markup;
    }

    function formatMetadata(metadata) {
        const rows = Object.entries(metadata)
            .map(([label, value]) => `
                <tr>
                    <td style="font-weight: 600; white-space: nowrap; padding-right: 1.5rem; color: var(--text-muted-light);">${escapeHtml(label)}</td>
                    <td style="word-break: break-all;">${escapeHtml(value)}</td>
                </tr>`)
            .join("");

        return `
            <div class="result-box" style="margin-top: 1rem; border-color: var(--primary);">
                <h4 style="margin-bottom: 1rem;">File Metadata</h4>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; min-width: unset;">
                        <tbody>${rows}</tbody>
                    </table>
                </div>
            </div>`;
    }

    function formatVirusTotal(virustotal) {
        if (virustotal.error) {
            return `<div class="result-box mismatch" style="margin-top: 1rem;"><h4>VirusTotal Error</h4><p>${escapeHtml(virustotal.message)}</p></div>`;
        }
        const isClean = virustotal.malicious === 0 && virustotal.suspicious === 0;
        const statusClass = isClean ? "match" : "mismatch";
        
        return `
            <div class="result-box ${statusClass}" style="margin-top: 1rem;">
                <h4 style="margin-bottom: 0.5rem;">VirusTotal Scan</h4>
                <div style="display: flex; gap: 15px; margin-bottom: 10px;">
                    <span style="font-weight: bold; color: #d20f39;">Malicious: ${virustotal.malicious}</span>
                    <span style="font-weight: bold; color: #df8e1d;">Suspicious: ${virustotal.suspicious}</span>
                    <span style="font-weight: bold; color: #40a02b;">Harmless: ${virustotal.harmless}</span>
                </div>
                <a href="${virustotal.permalink}" target="_blank" class="btn" style="font-size: 0.9rem; padding: 0.5rem 1rem;">View Full Report</a>
            </div>
        `;
    }

    function displayError(message) {
        const container = document.getElementById("resultsContainer");
        const content = document.getElementById("resultContent");
        if (container && content) {
            container.style.display = "block";
            content.innerHTML = `<div class="result-box mismatch"><h3>Error</h3><p>${escapeHtml(message)}</p></div>`;
        }
    }

    function escapeHtml(text) {
        if (!text) return "";
        const temp = document.createElement("div");
        temp.textContent = text;
        return temp.innerHTML;
    }
});