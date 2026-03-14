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
        show: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12.002 15.577c1.133 0 2.096-.397 2.887-1.19.792-.793 1.188-1.756 1.188-2.89 0-1.132-.397-2.095-1.19-2.886-.793-.792-1.756-1.188-2.89-1.188-1.132 0-2.095.397-2.886 1.19-.792.793-1.188 1.756-1.188 2.89 0 1.132.397 2.095 1.19 2.886.793.792 1.756 1.188 2.89 1.188ZM12 14.2c-.75 0-1.387-.262-1.912-.787A2.604 2.604 0 0 1 9.3 11.5c0-.75.262-1.387.787-1.912A2.604 2.604 0 0 1 12 8.8c.75 0 1.387.262 1.912.787.525.526.788 1.163.788 1.913s-.262 1.387-.787 1.912A2.604 2.604 0 0 1 12 14.2Zm.001 4.3c-2.3 0-4.395-.634-6.286-1.903-1.89-1.269-3.283-2.968-4.177-5.097.894-2.13 2.286-3.829 4.176-5.097C7.604 5.134 9.699 4.5 11.999 4.5c2.3 0 4.394.634 6.286 1.903 1.89 1.268 3.283 2.968 4.177 5.097-.894 2.13-2.286 3.829-4.176 5.097C16.396 17.866 14.3 18.5 12 18.5ZM12 17a9.544 9.544 0 0 0 5.188-1.488A9.774 9.774 0 0 0 20.8 11.5a9.773 9.773 0 0 0-3.613-4.013A9.545 9.545 0 0 0 12 6a9.545 9.545 0 0 0-5.188 1.487A9.773 9.773 0 0 0 3.2 11.5a9.773 9.773 0 0 0 3.612 4.012A9.544 9.544 0 0 0 12 17Z"></svg>',
        hide: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15.773 12.973 14.65 11.85c.15-.828-.086-1.573-.709-2.234-.622-.66-1.386-.916-2.29-.766l-1.124-1.123A3.453 3.453 0 0 1 12 7.423c1.135 0 2.098.396 2.89 1.188.791.791 1.187 1.754 1.187 2.889 0 .282-.025.545-.076.788-.05.244-.127.472-.228.685Zm3.18 3.112L17.85 15.05a10.951 10.951 0 0 0 1.688-1.588A8.901 8.901 0 0 0 20.8 11.5a9.848 9.848 0 0 0-3.587-4.013C15.654 6.497 13.917 6 12 6c-.483 0-.958.033-1.425.1a9.622 9.622 0 0 0-1.375.3L8.035 5.235a10.096 10.096 0 0 1 1.936-.556c.66-.12 1.335-.179 2.03-.179 2.343 0 4.456.646 6.34 1.938 1.883 1.293 3.256 2.98 4.12 5.062a11.29 11.29 0 0 1-1.435 2.502 11.083 11.083 0 0 1-2.072 2.083Zm.809 5.784-4.046-4.015a10.85 10.85 0 0 1-1.705.465A10.6 10.6 0 0 1 12 18.5c-2.35 0-4.464-.646-6.341-1.939-1.877-1.292-3.25-2.979-4.121-5.061a11.11 11.11 0 0 1 1.43-2.472A11.367 11.367 0 0 1 4.9 7.038l-2.77-2.8 1.055-1.053 17.63 17.63-1.053 1.054ZM5.954 8.092c-.528.42-1.042.926-1.541 1.517-.5.59-.904 1.22-1.213 1.891a9.834 9.834 0 0 0 3.588 4.012C8.346 16.505 10.083 17 12 17a8.08 8.08 0 0 0 1.36-.115c.451-.077.834-.157 1.148-.239l-1.266-1.296a3.606 3.606 0 0 1-1.242.227c-1.134 0-2.098-.396-2.89-1.188-.791-.791-1.187-1.754-1.187-2.889 0-.203.02-.414.062-.636.04-.22.096-.423.165-.606L5.954 8.092Z"></svg>'
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
            const form   = document.getElementById("apiKeyForm");
            const hasKey = form.getAttribute("data-has-key") === "true";
            apiKeySaveButton.classList.toggle("is-hidden", hasKey);
            apiKeyRemoveButton.classList.toggle("is-hidden", !hasKey);
        }

        updateApiKeyButtons();

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

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    }

    const uploadForm = document.getElementById("uploadForm");

    if (uploadForm) {
        const fileInput        = document.getElementById("fileInput");
        const dropZone         = document.getElementById("dropZone");
        const fileNameDisplay  = document.getElementById("fileNameDisplay");
        const loadingIndicator = document.getElementById("loadingIndicator");
        const submitButton     = document.getElementById("submitButton");
        const resultsContainer = document.getElementById("resultsContainer");

        if (fileInput && fileNameDisplay) {
            fileInput.addEventListener("change", function() {
                if (fileInput.files[0]) {
                    fileNameDisplay.textContent      = fileInput.files[0].name + " [ " + formatFileSize(fileInput.files[0].size) + " ]";
                    fileNameDisplay.style.fontWeight = "bold";
                } else {
                    fileNameDisplay.textContent      = "No file chosen";
                    fileNameDisplay.style.fontWeight = "normal";
                }
            });
        }

        if (dropZone && fileInput) {
            dropZone.addEventListener("dragover", (event) => {
                event.preventDefault();
                dropZone.classList.add("drag-over");
            });

            dropZone.addEventListener("dragleave", () => {
                dropZone.classList.remove("drag-over");
            });

            dropZone.addEventListener("drop", (event) => {
                event.preventDefault();
                dropZone.classList.remove("drag-over");
                const transfer     = event.dataTransfer;
                const droppedFiles = transfer.files;
                
                if (droppedFiles && droppedFiles[0]) {
                    fileInput.files                  = droppedFiles;
                    fileNameDisplay.textContent      = droppedFiles[0].name + " [ " + formatFileSize(droppedFiles[0].size) + " ]";
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

    const deleteAccountButton = document.getElementById("deleteAccountButton");
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

    const forgotPasswordLink  = document.getElementById("forgotPasswordLink");
    const forgotPasswordModal = document.getElementById("forgotPasswordModal");
    const cancelForgotPassword = document.getElementById("cancelForgotPassword");

    if (forgotPasswordLink && forgotPasswordModal) {
        forgotPasswordLink.addEventListener("click", (event) => {
            event.preventDefault();
            forgotPasswordModal.classList.remove("is-hidden");
        });

        cancelForgotPassword.addEventListener("click", () => {
            forgotPasswordModal.classList.add("is-hidden");
        });

        forgotPasswordModal.addEventListener("click", (event) => {
            if (event.target === forgotPasswordModal) {
                forgotPasswordModal.classList.add("is-hidden");
            }
        });
    }

    const generatePasswordLink = document.getElementById("generatePasswordLink");

    if (generatePasswordLink) {
        generatePasswordLink.addEventListener("click", (event) => {
            event.preventDefault();

            const charset  = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}";
            const length   = 20;
            const array    = new Uint32Array(length);
            crypto.getRandomValues(array);
            const password = Array.from(array, (n) => charset[n % charset.length]).join("");

            const input  = document.getElementById("password");
            const toggle = input.closest(".password-field").querySelector(".password-toggle");

            input.value = password;
            input.type  = "text";

            if (toggle) {
                toggle.innerHTML = PASSWORD_TOGGLE_ICONS.hide;
                toggle.setAttribute("aria-label", "Hide password");
            }
        });
    }

    const themeStylesheet   = document.getElementById("current-theme");
    const themeToggleNav    = document.getElementById("theme-toggle-link");
    const themeToggleFooter = document.getElementById("theme-toggle-link-footer");
    const themeToggles      = [themeToggleNav, themeToggleFooter].filter(Boolean);

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

    function setInputError(input, message) {
        input.classList.add("form-input--error");
        let hint = input.parentElement.querySelector(".form-hint--error");
        if (!hint) {
            hint           = document.createElement("span");
            hint.className = "form-hint form-hint--error";
            input.parentElement.appendChild(hint);
        }
        hint.textContent = message;
    }

    function clearInputError(input) {
        input.classList.remove("form-input--error");
        const hint = input.parentElement.querySelector(".form-hint--error");
        if (hint) hint.remove();
    }

    document.querySelectorAll('input[name="username"]').forEach(function(input) {
        input.addEventListener("input", function() {
            if (input.value.includes(" ")) {
                input.value = input.value.replace(/ /g, "");
            }
            clearInputError(input);
        });
        input.addEventListener("blur", function() {
            if (!input.value.trim()) {
                setInputError(input, "Username is required.");
            }
        });
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
                </div>`;

        if (result.virustotal) {
            markup += buildVirusTotalMarkup(result.virustotal);
        }

        markup += `</div>`;

        if (result.metadata && Object.keys(result.metadata).length > 0) {
            markup += `<div class="card result-metadata-card"><h4 class="result-section-heading">Metadata</h4><div class="table-container"><table class="metadata-table"><tbody>`;
            for (const [key, value] of Object.entries(result.metadata)) {
                markup += `<tr><td class="metadata-label">${escapeHtml(key)}</td><td class="metadata-value">${escapeHtml(String(value))}</td></tr>`;
            }
            markup += `</tbody></table></div></div>`;
        }

        markup += `<div class="result-reset-row"><button type="button" class="button-outline analyse-another-btn">Analyse another file</button></div>`;

        content.innerHTML = markup;

        const metaToggle = content.querySelector(".metadata-toggle-btn");
        if (metaToggle) {
            metaToggle.addEventListener("click", function() {
                const expanded = metaToggle.getAttribute("aria-expanded") === "true";
                const body     = content.querySelector(".metadata-collapsible");
                if (expanded) {
                    body.classList.add("is-hidden");
                    metaToggle.setAttribute("aria-expanded", "false");
                    metaToggle.innerHTML = "&#9660; Show";
                } else {
                    body.classList.remove("is-hidden");
                    metaToggle.setAttribute("aria-expanded", "true");
                    metaToggle.innerHTML = "&#9650; Hide";
                }
            });
        }

        const resetBtn = content.querySelector(".analyse-another-btn");
        if (resetBtn) {
            resetBtn.addEventListener("click", function() {
                uploadForm.reset();
                fileNameDisplay.innerHTML        = "<strong>Click to upload</strong> or drag and drop a file.";
                fileNameDisplay.style.fontWeight = "";
                container.classList.add("is-hidden");
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
        }

        container.classList.remove("is-hidden");
    }

    function buildVirusTotalMarkup(virustotal) {
        if (virustotal.error) {
            return `<div class="result-box unknown result-box-spaced"><h4>VirusTotal</h4><p>${escapeHtml(virustotal.error)}</p></div>`;
        }
        if (virustotal.message && !virustotal.virustotal_malicious && virustotal.virustotal_malicious !== 0) {
            return `<div class="result-box unknown result-box-spaced"><h4>VirusTotal</h4><p>${escapeHtml(virustotal.message)} <a href="${escapeHtml(virustotal.link)}" target="_blank">Submit for analysis.</a></p></div>`;
        }
        const isClean     = virustotal.virustotal_malicious === 0 && virustotal.virustotal_suspicious === 0;
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