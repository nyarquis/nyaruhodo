(function() {
    const saved = localStorage.getItem("theme") || "light";
    const link  = document.getElementById("current-theme");
    if (saved === "night" && link) {
        link.href = link.href.replace("light-mode", "night-mode");
    }
})();

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

    const PASSWORD_TOGGLE_ICONS = {
        show: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12C2 12 5.5 5 12 5C18.5 5 22 12 22 12C22 12 18.5 19 12 19C5.5 19 2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></svg>',
        hide: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="3" x2="21" y2="21" /><path d="M10.5 6.2C11 6.07 11.49 6 12 6C18.5 6 22 12 22 12C22 12 21.06 13.76 19.5 15.24" /><path d="M4.56 9.3C3.07 10.65 2 12 2 12C2 12 5.5 18 12 18C13.81 18 15.41 17.47 16.77 16.67" /><path d="M9.18 9.18A3 3 0 0 0 14.82 14.82" /></svg>'
    };

    document.addEventListener("click", function(event) {
        const toggle = event.target.closest(".password-toggle");
        if (!toggle) return;
        const input = toggle.closest(".password-field").querySelector("input");
        if (!input) return;
        const showing = input.type === "text";
        input.type = showing ? "password" : "text";
        toggle.setAttribute("aria-label", showing ? "Show password" : "Hide password");
        toggle.innerHTML = showing ? PASSWORD_TOGGLE_ICONS.show : PASSWORD_TOGGLE_ICONS.hide;
    });

    const apiKeyInput        = document.getElementById("apiKeyInput");
    const apiKeySaveButton   = document.getElementById("apiKeySaveButton");
    const apiKeyRemoveButton = document.getElementById("apiKeyRemoveButton");

    if (apiKeyInput && apiKeySaveButton && apiKeyRemoveButton) {

        function updateApiKeyButtons() {
            const hasKey = apiKeyInput.value.trim().length > 0;
            apiKeySaveButton.classList.toggle("is-hidden", hasKey);
            apiKeyRemoveButton.classList.toggle("is-hidden", !hasKey);
        }

        updateApiKeyButtons();

        apiKeyInput.addEventListener("input", updateApiKeyButtons);

        apiKeyRemoveButton.addEventListener("click", function() {
            apiKeyInput.value = "";
            apiKeyInput.type  = "password";
            const toggle = apiKeyInput.closest(".password-field").querySelector(".password-toggle");
            if (toggle) {
                toggle.innerHTML   = PASSWORD_TOGGLE_ICONS.show;
                toggle.setAttribute("aria-label", "Show API key");
            }
            document.getElementById("apiKeyForm").submit();
        });
    }

    const uploadForm = document.getElementById("uploadForm");

    if (uploadForm) {
        const fileInput        = document.getElementById("fileInput");
        const dropZone         = document.getElementById("dropZone");
        const fileNameDisplay  = document.getElementById("fileNameDisplay");
        const loadingIndicator = document.getElementById("loadingIndicator");
        const resultsContainer = document.getElementById("resultsContainer");
        const resultContent    = document.getElementById("resultContent");
        const submitButton     = document.getElementById("submitButton");

        fileInput.addEventListener("change", function() {
            if (this.files && this.files[0]) {
                fileNameDisplay.textContent      = this.files[0].name;
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
                const transfer     = event.dataTransfer;
                const droppedFiles = transfer.files;
                if (droppedFiles && droppedFiles[0]) {
                    fileInput.files                  = droppedFiles;
                    fileNameDisplay.textContent      = droppedFiles[0].name;
                    fileNameDisplay.style.fontWeight = "bold";
                }
            });
        }

        uploadForm.addEventListener("submit", function(event) {
            event.preventDefault();

            submitButton.disabled    = true;
            submitButton.textContent = "Analysing...";
            resultsContainer.classList.add("is-hidden");
            loadingIndicator.classList.remove("is-hidden");

            fetch("/analyse", {
                method: "POST",
                body: new FormData(uploadForm)
            })
            .then(response => response.json())
            .then(result => {
                loadingIndicator.classList.add("is-hidden");
                submitButton.disabled    = false;
                submitButton.textContent = "Analyse File";
                if (result.error) {
                    displayError(result.error);
                } else {
                    displayResults(result);
                }
            })
            .catch(error => {
                loadingIndicator.classList.add("is-hidden");
                submitButton.disabled    = false;
                submitButton.textContent = "Analyse File";
                displayError("A connection error occurred. Please check your network and try again.");
                console.error("Error:", error);
            });
        });
    }

    const deleteAccountButton    = document.getElementById("deleteAccountButton");
    const deleteAccountModal  = document.getElementById("deleteAccountModal");
    const cancelDeleteAccount = document.getElementById("cancelDeleteAccount");

    if (deleteAccountButton && deleteAccountModal) {
        deleteAccountButton.addEventListener("click", () => {
            deleteAccountModal.classList.remove("is-hidden");
        });

        cancelDeleteAccount.addEventListener("click", () => {
            deleteAccountModal.classList.add("is-hidden");
        });

        deleteAccountModal.addEventListener("click", (event) => {
            if (event.target === deleteAccountModal) {
                deleteAccountModal.classList.add("is-hidden");
            }
        });

        if (deleteAccountModal && deleteAccountModal.getAttribute("data-open") === "true") {
            deleteAccountModal.classList.remove("is-hidden");
        }
    }

    const themeStylesheet    = document.getElementById("current-theme");
    const themeToggleNav     = document.getElementById("theme-toggle-link");
    const themeToggleFooter  = document.getElementById("theme-toggle-link-footer");
    const themeToggles       = [themeToggleNav, themeToggleFooter].filter(Boolean);

    function applyThemeLabel(isNight) {
        const label = isNight ? "Switch to Light Mode" : "Switch to Night Mode";
        themeToggles.forEach(button => { button.textContent = label; });
    }

    if (themeStylesheet && themeToggles.length) {
        const isNight = themeStylesheet.getAttribute("href").includes("night-mode.css");
        applyThemeLabel(isNight);

        themeToggles.forEach(button => {
            button.addEventListener("click", (event) => {
                event.preventDefault();
                const currentlyNight = themeStylesheet.getAttribute("href").includes("night-mode.css");
                if (currentlyNight) {
                    themeStylesheet.href = themeStylesheet.href.replace("night-mode", "light-mode");
                    localStorage.setItem("theme", "light");
                    applyThemeLabel(false);
                } else {
                    themeStylesheet.href = themeStylesheet.href.replace("light-mode", "night-mode");
                    localStorage.setItem("theme", "night");
                    applyThemeLabel(true);
                }
            });
        });
    }

    document.querySelectorAll("td[data-ts], span[data-ts]").forEach(function(cell) {
        var raw = cell.getAttribute("data-ts");
        if (raw) {
            var date = new Date(raw.replace(" ", "T") + "Z");
            cell.textContent = new Intl.DateTimeFormat(undefined, {
                dateStyle: "medium",
                timeStyle: "short"
            }).format(date);
        }
    });

    function displayResults(result) {
        const container = document.getElementById("resultsContainer");
        const content   = document.getElementById("resultContent");
        if (!container || !content) return;

        let statusClass;
        let title;

        if (result.unknown) {
            statusClass = "unknown";
            title       = "Unknown File Type";
        } else if (result.mismatch) {
            statusClass = "mismatch";
            title       = "Extension Mismatch";
        } else {
            statusClass = "match";
            title       = "Extension Match";
        }

        let markup = `
            <div class="result-box ${statusClass}">
                <h3 class="result-title">${title}</h3>
                <div class="result-summary">
                    <div class="result-field">
                        <span class="result-field-label">File Name</span>
                        <span class="result-field-value">${escapeHtml(result.filename)}</span>
                    </div>
                    <div class="result-field">
                        <span class="result-field-label">Declared Extension</span>
                        <span class="result-field-value">${escapeHtml(result.original_filetype)}</span>
                    </div>
                    <div class="result-field">
                        <span class="result-field-label">Detected File Type</span>
                        <span class="result-field-value">${escapeHtml(result.detected_filetype)}</span>
                    </div>
                    <div class="result-field">
                        <span class="result-field-label">Description</span>
                        <span class="result-field-value">${escapeHtml(result.description)}</span>
                    </div>
                </div>
                <div class="result-analysis">
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
        container.classList.remove("is-hidden");
    }

    function formatMetadata(metadata) {
        const rows = Object.entries(metadata)
            .map(([label, value]) => `
                <tr>
                    <td class="metadata-label">${escapeHtml(label)}</td>
                    <td class="metadata-value">${escapeHtml(value)}</td>
                </tr>`)
            .join("");

        return `
            <div class="result-box result-box-primary">
                <h4 class="result-section-heading">File Metadata</h4>
                <div class="table-scroll">
                    <table class="metadata-table">
                        <tbody>${rows}</tbody>
                    </table>
                </div>
            </div>`;
    }

    function formatVirusTotal(virustotal) {
        if (virustotal.error) {
            return `<div class="result-box mismatch result-box-spaced"><h4>VirusTotal Error</h4><p>${escapeHtml(virustotal.message || virustotal.details || "An error occurred during the VirusTotal query.")}</p></div>`;
        }
        if (virustotal.message && !virustotal.virustotal_malicious && virustotal.virustotal_malicious !== 0) {
            return `<div class="result-box unknown result-box-spaced"><h4>VirusTotal</h4><p>${escapeHtml(virustotal.message)} <a href="${escapeHtml(virustotal.link)}" target="_blank">Submit for analysis.</a></p></div>`;
        }
        const isClean   = virustotal.virustotal_malicious === 0 && virustotal.virustotal_suspicious === 0;
        const statusClass = isClean ? "match" : "mismatch";

        return `
            <div class="result-box ${statusClass} result-box-spaced">
                <h4 class="result-section-heading">Scan Results</h4>
                <div class="result-virustotal-counts">
                    <span class="virustotal-count virustotal-malicious">Malicious: ${virustotal.virustotal_malicious}</span>
                    <span class="virustotal-count virustotal-suspicious">Suspicious: ${virustotal.virustotal_suspicious}</span>
                    <span class="virustotal-count virustotal-harmless">Harmless: ${virustotal.virustotal_harmless}</span>
                </div>
                <a href="${escapeHtml(virustotal.link)}" target="_blank" class="button result-virustotal-link">View Full Report on VirusTotal</a>
            </div>
        `;
    }

    function displayError(message) {
        const container = document.getElementById("resultsContainer");
        const content   = document.getElementById("resultContent");
        if (container && content) {
            content.innerHTML = `<div class="result-box mismatch"><h3>Analysis Error</h3><p>${escapeHtml(message)}</p></div>`;
            container.classList.remove("is-hidden");
        }
    }

    function escapeHtml(text) {
        if (!text) return "";
        const temp = document.createElement("div");
        temp.textContent = text;
        return temp.innerHTML;
    }
});