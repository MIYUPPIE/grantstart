/**
 * GrantStar — Frontend Application Logic
 * Multi-step wizard, API integration, dynamic rendering
 */

// ── STATE ─────────────────────────────────────────────────────
let currentStep = 1;
let userProfile = {};
let vaultData = { profile: {}, credentials: [] };
let selectedGrant = null;
let searchResults = {};
let currentProposalId = null;
let currentProposalData = null; // Store full proposal for AI critique
let autoApplyResult = null;
let aiActive = false;

// ── STEP NAVIGATION ───────────────────────────────────────────
function goToStep(step) {
    // Hide current
    document.querySelector(`.step-panel.active`)?.classList.remove('active');

    // Show target
    const targetPanel = document.getElementById(`step-${step}`);
    if (targetPanel) {
        targetPanel.classList.add('active');
        // Re-trigger animation
        targetPanel.style.animation = 'none';
        targetPanel.offsetHeight; // force reflow
        targetPanel.style.animation = '';
    }

    // Update progress bar
    updateProgress(step);
    currentStep = step;

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateProgress(step) {
    document.querySelectorAll('.progress-step').forEach((el, i) => {
        const stepNum = i + 1;
        el.classList.remove('active', 'completed');
        if (stepNum === step) {
            el.classList.add('active');
        } else if (stepNum < step) {
            el.classList.add('completed');
        }
    });

    // Update lines
    document.querySelectorAll('.progress-line').forEach((line, i) => {
        if (i + 1 < step) {
            line.classList.add('active');
        } else {
            line.classList.remove('active');
        }
    });
}

// ── LOADING ───────────────────────────────────────────────────
function showLoading(text = 'Searching the cosmos for your grants...') {
    const overlay = document.getElementById('loading');
    overlay.querySelector('.loading-text').textContent = text;
    overlay.classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

// ── TOAST ─────────────────────────────────────────────────────
function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    document.getElementById('toast-message').textContent = message;
    toast.classList.remove('hidden');
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.classList.add('hidden'), 300);
    }, duration);
}

// ── ONBOARDING FORM ───────────────────────────────────────────
document.getElementById('onboarding-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const country = document.getElementById('country').value;
    const sector = document.getElementById('sector').value;
    const orgType = document.getElementById('org_type').value;
    const stage = document.getElementById('stage').value;
    const registered = document.getElementById('registered').checked;

    if (!country || !sector || !orgType || !stage) {
        showToast('Please fill in all fields');
        return;
    }

    userProfile = { country, sector, org_type: orgType, stage, registered };

    showLoading('Analyzing your profile and searching for matching grants...');

    try {
        // Search for grants
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userProfile),
        });

        const data = await response.json();
        searchResults = data;

        // Render results
        renderGrantResults(data);

        hideLoading();
        goToStep(2);
        showToast(`Found ${data.total} matching grants for ${country}!`);

    } catch (err) {
        hideLoading();
        showToast('Error searching for grants. Please try again.');
        console.error(err);
    }
});

// ── RENDER GRANT RESULTS ──────────────────────────────────────
function renderGrantResults(data) {
    document.getElementById('results-subtitle').textContent =
        `${data.total} grants found for ${userProfile.country} — ranked by ease of application.`;

    renderGrantList('global-grants', data.global_grants);
    renderGrantList('local-grants', data.local_grants);
}

function renderGrantList(containerId, grants) {
    const container = document.getElementById(containerId);

    if (!grants || grants.length === 0) {
        container.innerHTML = `
            <div class="compliance-card">
                <p style="color: var(--text-muted); text-align: center; padding: 1rem;">
                    No grants found in this category. Try adjusting your profile.
                </p>
            </div>`;
        return;
    }

    container.innerHTML = grants.map(grant => createGrantCard(grant)).join('');
}

function createGrantCard(grant) {
    const scoreClass = grant.match_score >= 60 ? 'high' : grant.match_score >= 35 ? 'medium' : 'low';
    const scoreLabel = grant.match_score >= 60 ? 'Strong Match' : grant.match_score >= 35 ? 'Good Fit' : 'Possible';

    const amountStr = grant.amount_usd
        ? `$${grant.amount_usd.min.toLocaleString()} — $${grant.amount_usd.max.toLocaleString()}`
        : 'Varies';

    const difficulty = '●'.repeat(grant.difficulty) + '○'.repeat(10 - grant.difficulty);

    const reasons = (grant.match_reasons || [])
        .map(r => `<li>${r}</li>`)
        .join('');

    const warnings = (grant.warnings || [])
        .filter(w => w) // remove empty
        .map(w => `<li>${w}</li>`)
        .join('');

    const tags = (grant.tags || [])
        .map(t => `<span class="tag">${t}</span>`)
        .join('');

    return `
            <div class="grant-card-header">
                <div class="grant-title-group">
                    <span class="grant-name">${grant.name}</span>
                    <span class="grant-score ${scoreClass}">${scoreLabel}</span>
                </div>
                <div class="deadline-pill-container" data-deadline="${grant.deadline}">
                    <!-- Populated by JS -->
                </div>
            </div>
            <div class="grant-funder">${grant.funder}</div>
            <p class="grant-description">${grant.description}</p>
            <div class="grant-meta">
                <span class="grant-meta-item"><span class="icon">💰</span> ${amountStr}</span>
                <span class="grant-meta-item"><span class="icon">📅</span> Deadline: ${grant.deadline}</span>
                <span class="grant-meta-item"><span class="icon">📊</span> Difficulty: ${difficulty}</span>
            </div>
            <div class="grant-tags">${tags}</div>
            ${reasons ? `<ul class="grant-reasons">${reasons}</ul>` : ''}
            ${warnings ? `<ul class="grant-warnings">${warnings}</ul>` : ''}
            <div class="grant-card-actions">
                <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); selectGrant('${grant.id}')">
                    <span class="btn-text">Check Compliance</span>
                    <span class="btn-icon">→</span>
                </button>
                <a href="${grant.url}" target="_blank" class="btn btn-outline btn-sm" onclick="event.stopPropagation();">
                    🔗 Funder Portal
                </a>
            </div>
        </div>
    `;
}

// ── SELECT GRANT & COMPLIANCE ─────────────────────────────────
async function selectGrant(grantId) {
    selectedGrant = grantId;
    showLoading('Checking compliance requirements...');

    try {
        const response = await fetch('/api/compliance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ grant_id: grantId, country: userProfile.country }),
        });

        const data = await response.json();
        renderCompliance(data);

        hideLoading();
        goToStep(3);

    } catch (err) {
        hideLoading();
        showToast('Error loading compliance data.');
        console.error(err);
    }
}

function renderCompliance(data) {
    document.getElementById('compliance-subtitle').textContent =
        `Documents needed for "${data.grant_name}" in ${data.country}`;

    const container = document.getElementById('compliance-content');

    const generalDocs = (data.general_documents || [])
        .map(doc => `<li><span class="doc-icon">📄</span> ${doc}</li>`)
        .join('');

    const countryDocs = (data.country_specific_documents || [])
        .map(doc => `<li><span class="doc-icon">🏛️</span> ${doc}</li>`)
        .join('');

    const knowledge = data.country_knowledge || {};
    const additionalDocs = (knowledge.additional_docs || [])
        .map(doc => `<li><span class="doc-icon">📋</span> ${doc}</li>`)
        .join('');

    const tips = (data.tips || [])
        .map(tip => `<p>${tip}</p>`)
        .join('');

    container.innerHTML = `
        <div class="compliance-card">
            <h3>📑 General Requirements</h3>
            <ul class="doc-list">${generalDocs || '<li>No general documents listed.</li>'}</ul>
        </div>

        <div class="compliance-card">
            <h3>🏛️ ${data.country}-Specific Documents</h3>
            <ul class="doc-list">${countryDocs || '<li>No country-specific documents listed.</li>'}</ul>
            <div style="margin-top: 1rem;">
                <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                    <strong>Tax ID:</strong> ${knowledge.tax_id_info || '—'}
                </p>
                <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                    <strong>Registration:</strong> ${knowledge.registration_info || '—'}
                </p>
                <p style="font-size: 0.82rem; color: var(--text-muted);">
                    <strong>Compliance:</strong> ${knowledge.compliance_info || '—'}
                </p>
            </div>
        </div>

        ${additionalDocs ? `
        <div class="compliance-card">
            <h3>📋 Additional Documents to Prepare</h3>
            <ul class="doc-list">${additionalDocs}</ul>
        </div>` : ''}

        ${tips ? `
        <div class="compliance-card">
            <h3>💡 GrantStar Tips</h3>
            <div class="tip-card">${tips}</div>
        </div>` : ''}
    `;
}

// ── PROPOSAL DRAFTER ──────────────────────────────────────────
document.getElementById('proposal-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const projectName = document.getElementById('project_name').value;
    const problem = document.getElementById('problem').value;
    const solution = document.getElementById('solution').value;
    const impact = document.getElementById('impact').value;
    const beneficiaries = document.getElementById('beneficiaries').value;
    const budgetUsd = parseFloat(document.getElementById('budget_usd').value) || 0;

    if (!projectName || !problem || !solution || !impact) {
        showToast('Please fill in the required fields.');
        return;
    }

    showLoading('Drafting your proposal using the Problem-Solution-Impact framework...');

    try {
        const response = await fetch('/api/draft', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grant_id: selectedGrant,
                project_name: projectName,
                problem,
                solution,
                impact,
                beneficiaries,
                budget_usd: budgetUsd,
                country: userProfile.country,
                sector: userProfile.sector,
            }),
        });

        const data = await response.json();
        currentProposalData = data;
        renderProposal(data);

        hideLoading();
        showToast('Proposal generated successfully! 🎉');

    } catch (err) {
        hideLoading();
        showToast('Error generating proposal. Please try again.');
        console.error(err);
    }
});

function renderProposal(data) {
    const output = document.getElementById('proposal-output');
    output.classList.remove('hidden');

    document.getElementById('proposal-title').textContent =
        `📝 ${data.project_title} — Proposal for ${data.grant_name}`;

    // Render sections
    const sections = data.sections || {};
    let bodyHtml = '';

    if (sections.executive_summary) {
        bodyHtml += `<h2>Executive Summary</h2><p>${formatMarkdown(sections.executive_summary)}</p>`;
    }
    if (sections.problem_statement) {
        bodyHtml += formatMarkdown(sections.problem_statement);
    }
    if (sections.proposed_solution) {
        bodyHtml += formatMarkdown(sections.proposed_solution);
    }
    if (sections.impact_and_outcomes) {
        bodyHtml += formatMarkdown(sections.impact_and_outcomes);
    }
    if (sections.sustainability_plan) {
        bodyHtml += formatMarkdown(sections.sustainability_plan);
    }
    if (sections.budget_justification) {
        bodyHtml += formatMarkdown(sections.budget_justification);
    }

    document.getElementById('proposal-body').innerHTML = bodyHtml;

    // SDG tags
    const sdgTags = (data.sdg_alignment || [])
        .map(sdg => `<span class="tag">${sdg}</span>`)
        .join('');
    document.getElementById('sdg-tags').innerHTML = sdgTags;

    // Word count
    document.getElementById('word-count').textContent =
        `📝 Approximately ${data.word_count} words`;

    // Scroll to proposal
    setTimeout(() => {
        output.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}

function formatMarkdown(text) {
    if (!text) return '';

    return text
        // Headers
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^### (.*$)/gm, '<h3 style="font-size: 0.95rem; color: var(--gold-primary); margin-top: 1rem; margin-bottom: 0.5rem;">$1</h3>')
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Lists
        .replace(/^- (.*$)/gm, '<li style="margin-left: 1rem; list-style: disc; margin-bottom: 0.3rem;">$1</li>')
        .replace(/^(\d+)\. (.*$)/gm, '<li style="margin-left: 1rem; list-style: decimal; margin-bottom: 0.3rem;">$2</li>')
        // Table (basic support)
        .replace(/\|(.+)\|/g, (match) => {
            const cells = match.split('|').filter(c => c.trim());
            if (cells.every(c => c.trim().match(/^-+$/))) return ''; // skip separator
            const tag = match.includes('---') ? 'th' : 'td';
            const row = cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('');
            return `<tr>${row}</tr>`;
        })
        // Paragraphs
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}

// ── COPY TO CLIPBOARD ─────────────────────────────────────────
function copyProposal() {
    const proposalBody = document.getElementById('proposal-body');
    const text = proposalBody.innerText;

    navigator.clipboard.writeText(text).then(() => {
        showToast('Proposal copied to clipboard! 📋');
    }).catch(() => {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Proposal copied to clipboard! 📋');
    });
}

// ── LOGOUT ────────────────────────────────────────────────────
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch (e) { /* ignore */ }
    window.location.href = '/login';
}

// ── AI STRATEGIST ─────────────────────────────────────────────
async function checkAIStatus() {
    try {
        const resp = await fetch('/api/ai/status');
        const data = await resp.json();
        aiActive = data.active;

        const badge = document.getElementById('ai-status-badge');
        const text = badge.querySelector('.badge-text');

        if (aiActive) {
            badge.classList.remove('offline');
            badge.classList.add('active');
            text.textContent = data.model
                ? `AI Strategist: ${data.model}`
                : 'AI Strategist: Active';
        } else {
            badge.classList.remove('active');
            badge.classList.add('offline');
            text.textContent = 'AI Strategist: Offline';
        }
    } catch (e) {
        console.error('AI Status check failed:', e);
    }
}

async function critiqueProposal() {
    if (!aiActive) {
        showToast('AI Strategist is offline. Add an LLM key to .env to activate.');
        return;
    }

    if (!currentProposalData) {
        showToast('No proposal to critique. Draft one first.');
        return;
    }

    showLoading('Senior Strategist is reviewing your proposal for weaknesses...');

    try {
        const resp = await fetch('/api/ai/critique', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                proposal: JSON.stringify(currentProposalData.sections),
                grant_id: selectedGrant
            })
        });

        const data = await resp.json();
        hideLoading();

        if (data.error) {
            showToast(data.error);
            return;
        }

        // Show critique in a modal-like alert or append to proposal
        const critiqueHtml = `<div class="compliance-card ai-critique" style="border-left: 4px solid var(--gold-primary); background: rgba(212, 175, 55, 0.05); margin-top: 2rem;">
            <h3 style="color: var(--gold-primary);">🛡️ AI Strategic Critique (Red Team)</h3>
            <div style="font-size: 0.9rem; line-height: 1.6;">${formatMarkdown(data.critique)}</div>
        </div>`;

        const body = document.getElementById('proposal-body');
        const existing = document.querySelector('.ai-critique');
        if (existing) existing.remove();

        body.insertAdjacentHTML('beforeend', critiqueHtml);
        showToast('Strategic critique added to your proposal! 🛡️');

        // Scroll to critique
        document.querySelector('.ai-critique').scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
        hideLoading();
        showToast('Error during AI critique');
        console.error(err);
    }
}

// ── VAULT MANAGEMENT ──────────────────────────────────────────
async function refreshVaultData() {
    try {
        const pResp = await fetch('/api/vault/profile');
        const cResp = await fetch('/api/vault/credentials');

        vaultData.profile = await pResp.json();
        vaultData.credentials = await cResp.json();

        updateVaultUI();
    } catch (err) {
        console.error('Error refreshing vault:', err);
    }
}

function updateVaultUI() {
    // Update completion text
    const pct = vaultData.profile._completion || 0;
    document.getElementById('vault-completion-text').textContent = `Profile: ${pct}% complete`;

    // Update profile form fields (id="v-...")
    Object.keys(vaultData.profile).forEach(key => {
        const el = document.getElementById(`v-${key}`);
        if (el) el.value = vaultData.profile[key] || '';
    });

    // Update credentials list
    const list = document.getElementById('creds-list');
    if (vaultData.credentials.length === 0) {
        list.innerHTML = '<p class="text-muted">No portal logins saved yet.</p>';
    } else {
        list.innerHTML = vaultData.credentials.map(c => `
            <div class="cred-item">
                <div class="cred-info">
                    <h5>${c.portal_name}</h5>
                    <p>${c.email}</p>
                </div>
                <button class="btn btn-sm btn-outline" onclick="deleteCred('${c.portal_name}')">🗑️</button>
            </div>
        `).join('');
    }
}

function toggleVault() {
    document.getElementById('vault-modal').classList.toggle('hidden');
    if (!document.getElementById('vault-modal').classList.contains('hidden')) {
        refreshVaultData();
    }
}

function switchVaultTab(tab) {
    document.querySelectorAll('.vault-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.vault-tab-panel').forEach(p => p.classList.remove('active'));

    document.querySelector(`.vault-tab[onclick*="${tab}"]`).classList.add('active');
    document.getElementById(`vault-${tab}-tab`).classList.add('active');
}

// Save Profile to Vault
document.getElementById('vault-profile-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {};
    const fields = ['full_name', 'email', 'phone', 'address', 'city', 'country', 'bio', 'org_name', 'tax_id', 'org_reg', 'org_year', 'org_web'];
    fields.forEach(f => {
        data[f] = document.getElementById(`v-${f}`).value;
    });

    try {
        const resp = await fetch('/api/vault/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (resp.ok) {
            showToast('Vault Profile saved! 🔒');
            refreshVaultData();
        }
    } catch (err) {
        showToast('Error saving vault profile');
    }
});

// Add Credential to Vault
document.getElementById('vault-creds-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const portal_name = document.getElementById('c-portal_name').value;
    const email = document.getElementById('c-email').value;
    const password = document.getElementById('c-password').value;

    try {
        const resp = await fetch('/api/vault/credentials', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ portal_name, email, password })
        });
        if (resp.ok) {
            showToast('Credential added to Vault! 🔑');
            document.getElementById('vault-creds-form').reset();
            refreshVaultData();
        }
    } catch (err) {
        showToast('Error saving credential');
    }
});

// Delete Credential
async function deleteCred(portalName) {
    if (!confirm(`Delete login for ${portalName}?`)) return;
    try {
        await fetch(`/api/vault/credentials?portal_name=${encodeURIComponent(portalName)}`, {
            method: 'DELETE'
        });
        refreshVaultData();
    } catch (err) {
        showToast('Error deleting credential');
    }
}

// ── AUTO-APPLY ENGINE (STEP 5) ────────────────────────────────
async function prepareAutoApply() {
    if (!selectedGrant) return;

    showLoading('Analyzing form structure and preparing Vault data...');

    try {
        const resp = await fetch('/api/apply/prepare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grant_id: selectedGrant,
                proposal_id: currentProposalId // Not fully implemented yet, will use latest session
            })
        });

        const data = await resp.json();
        autoApplyResult = data;

        renderAutoApply(data);
        hideLoading();
        goToStep(5);

    } catch (err) {
        hideLoading();
        showToast('Error preparing auto-apply');
        console.error(err);
    }
}

function renderAutoApply(data) {
    document.getElementById('portal-name-display').textContent = data.portal_name;
    document.getElementById('overall-completion-pct').textContent = `${data.readiness_score}%`;

    // Portal Link
    const portalBtn = document.getElementById('btn-open-portal');
    portalBtn.onclick = () => window.open(data.portal_url, '_blank');

    // Registration Helper
    const regCard = document.getElementById('registration-helper');
    if (data.workflow_type === 'generic') {
        regCard.classList.add('hidden');
    } else {
        regCard.classList.remove('hidden');
        document.getElementById('reg-note').textContent = `Required for ${data.portal_name}. We have custom steps for this!`;
        document.getElementById('btn-portal-reg').onclick = () => openRegistrationHelper(data.grant_id);
    }

    // Form Sections
    const container = document.getElementById('form-sections');
    container.innerHTML = data.form_preview.map(section => `
        <div class="form-section-card">
            <div class="section-header">
                <h3>${section.section_name}</h3>
                <span class="section-badge">${section.fields.length} fields</span>
            </div>
            <div class="fields-grid">
                ${section.fields.map(field => createFieldCard(field)).join('')}
            </div>
        </div>
    `).join('');
}

function createFieldCard(field) {
    const isEmpty = !field.value;
    const isOver = field.char_limit && field.value && field.value.length > field.char_limit;
    const isNear = field.char_limit && field.value && field.value.length > (field.char_limit * 0.9);

    const limitClass = isOver ? 'over' : (isNear ? 'near' : '');
    const charInfo = field.char_limit ? `
        <span class="char-limit ${limitClass}">
            ${field.value ? field.value.length : 0} / ${field.char_limit} chars
        </span>
    ` : '';

    return `
        <div class="field-card ${isEmpty ? 'empty' : ''}">
            <div class="field-label-row">
                <span class="field-label">${field.label} ${field.required ? '<span class="field-required">*</span>' : ''}</span>
                ${charInfo}
            </div>
            <div class="field-input-group">
                <div class="field-preview" title="${field.value || 'Field empty in Vault'}">
                    ${field.value || 'No data found in Vault'}
                </div>
                <button class="btn-copy-field" onclick="copyField('${field.field_id}', this)" ${isEmpty ? 'disabled' : ''}>
                    📋
                </button>
            </div>
            <div class="field-meta">
                <span>Selector: <code>${field.selector}</code></span>
            </div>
        </div>
    `;
}

function copyField(fieldId, btn) {
    // Find value in autoApplyResult
    let value = '';
    autoApplyResult.form_preview.forEach(s => {
        const f = s.fields.find(field => field.field_id === fieldId);
        if (f) value = f.value;
    });

    if (!value) return;

    navigator.clipboard.writeText(value).then(() => {
        const originalText = btn.textContent;
        btn.textContent = '✅';
        setTimeout(() => btn.textContent = originalText, 1500);
    });
}

async function openRegistrationHelper(grantId) {
    showLoading('Loading registration guide...');
    try {
        const resp = await fetch(`/api/apply/registration?grant_id=${grantId}`);
        const data = await resp.json();

        // Use a simple alert for now or a new modal
        let guide = `Registration Guide for ${data.portal_name}:\n\n`;
        data.registration_steps.forEach((s, i) => {
            guide += `${i + 1}. ${s.step_name}: ${s.action}\n`;
            if (s.help_text) guide += `   Tip: ${s.help_text}\n`;
        });

        hideLoading();
        alert(guide);
        window.open(data.portal_url, '_blank');

    } catch (err) {
        hideLoading();
        showToast('Error loading registration helper');
    }
}

// ── PRE-FILL FROM USER PROFILE ────────────────────────────────
function prefillFromProfile() {
    const userData = document.getElementById('user-data');
    if (!userData) return;

    const country = userData.dataset.country;
    const sector = userData.dataset.sector;
    const orgType = userData.dataset.orgType;
    const stage = userData.dataset.stage;
    const registered = userData.dataset.registered === 'true';

    if (country) document.getElementById('country').value = country;
    if (sector) document.getElementById('sector').value = sector;
    if (orgType) document.getElementById('org_type').value = orgType;
    if (stage) document.getElementById('stage').value = stage;
    document.getElementById('registered').checked = registered;
}

// ── DEADLINE COUNTDOWN ────────────────────────────────────────
let countdownInterval = null;

function startCountdownInterval() {
    if (countdownInterval) clearInterval(countdownInterval);

    const update = () => {
        document.querySelectorAll('.deadline-pill-container').forEach(container => {
            const deadlineStr = container.dataset.deadline;
            if (!deadlineStr) return;

            const deadline = new Date(deadlineStr + 'T23:59:59');
            const now = new Date();
            const diff = deadline - now;

            if (diff <= 0) {
                container.innerHTML = `<div class="deadline-pill passed">CLOSED</div>`;
                return;
            }

            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

            let urgencyClass = 'normal';
            if (days < 3) urgencyClass = 'urgent'; // Less than 3 days
            else if (days < 14) urgencyClass = 'warning'; // Less than 2 weeks

            // Structured professional display
            container.innerHTML = `
                <div class="deadline-pill ${urgencyClass}">
                    <span class="pill-icon">⏳</span>
                    <div class="time-block">
                        <span class="val">${days}</span><span class="lbl">d</span>
                    </div>
                    <div class="time-block">
                        <span class="val">${hours}</span><span class="lbl">h</span>
                    </div>
                    <div class="time-block">
                        <span class="val">${mins}</span><span class="lbl">m</span>
                    </div>
                </div>
            `;
        });
    };

    update();
    countdownInterval = setInterval(update, 60000); // Update every minute
}

// ── INIT ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    goToStep(1);
    prefillFromProfile();
    refreshVaultData();
    checkAIStatus();
    startCountdownInterval();
});

