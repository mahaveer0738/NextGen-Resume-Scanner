/**
 * ============================================================
 *  assets/js/results.js  —  V2.0 Dashboard Logic
 *  Renders the Bento Box UI with data from LangGraph
 * ============================================================
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Get the data passed from the main page upload
    const resultData = sessionStorage.getItem('resumeAnalysisResults');
    
    if (!resultData) {
        alert("No analysis data found! Please upload a resume first.");
        window.location.href = '../index.html';
        return;
    }

    try {
        const data = JSON.parse(resultData);
        
        // 2. Hide loading screen, show dashboard
        document.getElementById('loadingOverlay').style.opacity = '0';
        setTimeout(() => {
            document.getElementById('loadingOverlay').style.display = 'none';
            document.getElementById('dashboard').style.display = 'flex';
            
            // 3. Populate all Bento Box widgets
            // The API returns { success: true, data: { ats: {}, ... } }
            // So we must pass data.data to the populator!
            populateDashboard(data.data || data);
        }, 500);

    } catch (e) {
        console.error("Failed to parse results:", e);
        alert("Error loading results.");
    }
});

function populateDashboard(data) {
    // ==========================================
    // 1. TOP BANNER (ATS & Verdict)
    // ==========================================
    const ats = data.ats || {};
    document.getElementById('detectedRole').textContent = data.keywords?.detected_role || 'Candidate';
    document.getElementById('atsSummary').textContent = ats.summary || "Your resume has been analyzed successfully.";
    
    const score = ats.overall_score || 0;
    document.getElementById('atsScore').textContent = score;
    document.getElementById('atsLabel').textContent = ats.label || (score > 70 ? 'Good' : 'Needs Work');
    
    // Set the CSS variable for the circular gauge (value between 0 and 100)
    document.querySelector('.score-ring').style.setProperty('--score', score);
    
    // Change gauge color based on score
    if (score < 50) {
        document.querySelector('.score-ring').style.setProperty('--color-mint', 'var(--color-red)');
        document.querySelector('.score-ring').style.setProperty('--color-mint-glow', 'rgba(239, 68, 68, 0.2)');
        document.getElementById('atsLabel').style.color = 'var(--color-red)';
        document.getElementById('atsLabel').style.background = 'rgba(239, 68, 68, 0.1)';
        document.getElementById('atsLabel').style.borderColor = 'rgba(239, 68, 68, 0.3)';
    }

    // ==========================================
    // 2. KEYWORD DIAGNOSTICS (Left Column)
    // ==========================================
    const kw = data.keywords || {};
    document.getElementById('kwMatchPercent').textContent = (kw.match_percent || 0) + '%';
    document.getElementById('kwFoundCount').textContent = kw.total_keywords_found || 0;
    
    // Tags
    const foundContainer = document.getElementById('foundKeywords');
    (kw.found_keywords || []).forEach(word => {
        const span = document.createElement('span');
        span.className = 'tag found';
        span.textContent = word;
        foundContainer.appendChild(span);
    });

    const missingContainer = document.getElementById('missingKeywords');
    (kw.missing_keywords || []).forEach(word => {
        const span = document.createElement('span');
        span.className = 'tag missing';
        span.textContent = word;
        missingContainer.appendChild(span);
    });

    // ATS Breakdown Bars
    const breakdown = ats.breakdown || {};
    const bdContainer = document.getElementById('atsBreakdown');
    for (const [key, value] of Object.entries(breakdown)) {
        const title = key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        bdContainer.innerHTML += `
            <div class="breakdown-item">
                <div class="breakdown-header">
                    <span>${title}</span>
                    <span style="color: var(--color-purple);">${value}%</span>
                </div>
                <div class="bar-bg">
                    <div class="bar-fill" style="width: ${value}%; background: var(--color-purple);"></div>
                </div>
            </div>
        `;
    }

    // ==========================================
    // 3. AI SUGGESTIONS (Middle Column)
    // ==========================================
    const suggContainer = document.getElementById('suggestionsList');
    const suggestions = data.suggestions?.suggestions || [];
    
    if (suggestions.length === 0) {
        suggContainer.innerHTML = `<p style="color: var(--text-muted);">No suggestions found. Your resume is perfect!</p>`;
    } else {
        suggestions.forEach(s => {
            const badgeClass = s.priority.toLowerCase();
            suggContainer.innerHTML += `
                <div class="suggestion-card">
                    <div class="suggestion-icon"><i class="fa-solid fa-check"></i></div>
                    <div class="suggestion-content">
                        <h4>${s.title}</h4>
                        <p>${s.description}</p>
                        <span class="suggestion-badge ${badgeClass}">${s.priority} Priority</span>
                    </div>
                </div>
            `;
        });
    }

    // Critical Fixes (if ATS < 50)
    if (data.critical_fixes && data.critical_fixes.critical_fixes) {
        document.getElementById('criticalFixesSection').style.display = 'block';
        const critContainer = document.getElementById('criticalFixesList');
        data.critical_fixes.critical_fixes.forEach(cf => {
            critContainer.innerHTML += `
                <div class="suggestion-card critical">
                    <div class="suggestion-icon"><i class="fa-solid fa-xmark"></i></div>
                    <div class="suggestion-content">
                        <h4>Fix ${cf.section}: ${cf.issue}</h4>
                        <p>${cf.fix}</p>
                        <span class="suggestion-badge high">Critical</span>
                    </div>
                </div>
            `;
        });
    }

    // ==========================================
    // 4. MARKET & JOBS (Right Column)
    // ==========================================
    const web = data.web_research || {};
    
    // Salary
    if (web.salary_range) {
        document.getElementById('salaryRange').textContent = `${web.salary_range.currency} ${web.salary_range.min} - ${web.salary_range.max}`;
    }
    
    // Insight
    document.getElementById('industryInsight').innerHTML = `<strong>Industry Trend:</strong> ${web.industry_insights || 'No data'}`;

    // Trending Skills
    const trendContainer = document.getElementById('trendingSkills');
    (web.trending_skills || []).forEach(word => {
        const span = document.createElement('span');
        span.className = 'tag trending';
        span.innerHTML = `<i class="fa-solid fa-arrow-trend-up"></i> ${word}`;
        trendContainer.appendChild(span);
    });

    // Jobs
    const jobs = data.job_search || {};
    document.getElementById('jobMatchCount').textContent = jobs.total_found || 0;
    document.getElementById('jobMatchSummary').textContent = jobs.match_summary || "Here are some remote jobs that fit your profile.";
    
    const jobsList = document.getElementById('jobsList');
    if (jobs.job_listings && jobs.job_listings.length > 0) {
        jobs.job_listings.forEach(job => {
            jobsList.innerHTML += `
                <div class="job-card">
                    <div class="job-title">${job.title}</div>
                    <div class="job-company">${job.company}</div>
                    <div class="job-details">
                        <span class="job-detail"><i class="fa-solid fa-location-dot"></i> ${job.location || 'Remote'}</span>
                        <span class="job-detail"><i class="fa-solid fa-clock"></i> ${job.type.replace('_', ' ')}</span>
                    </div>
                    <a href="${job.url}" target="_blank" class="job-btn">View Job</a>
                </div>
            `;
        });
    } else {
        jobsList.innerHTML = `<p style="color: var(--text-muted); font-size: 13px;">No active remote jobs found for this profile.</p>`;
    }
}
