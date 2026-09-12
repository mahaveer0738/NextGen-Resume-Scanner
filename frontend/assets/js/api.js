/**
 * ============================================================
 *  assets/js/api.js  —  API Communication Layer
 *
 *  📌 WHAT IS THIS FILE?
 *     This is the "bridge" file between your frontend and
 *     your Python FastAPI backend.
 *
 *     All fetch() calls to the backend live HERE.
 *     Other JS files (script.js, results.js) just call
 *     these clean functions — they don't deal with raw fetch.
 *
 *  📌 WHY SEPARATE THIS?
 *     If you ever change the API URL (e.g., for deployment),
 *     you only update ONE place — this file.
 * ============================================================
 */

// ─────────────────────────────────────────────
// BASE URL — Change this when deploying
// ─────────────────────────────────────────────

const API_BASE_URL = "http://localhost:8000/api";


// ─────────────────────────────────────────────
// ANALYZE RESUME
// Called when user uploads a resume for full analysis
// ─────────────────────────────────────────────

async function analyzeResume(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Analysis failed");
    }

    return await response.json();
}


// ─────────────────────────────────────────────
// JOB MATCH
// Called when user provides a resume + job description
// ─────────────────────────────────────────────

async function matchJob(file, jobDescription) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("job_description", jobDescription);

    const response = await fetch(`${API_BASE_URL}/job-match`, {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Job match failed");
    }

    return await response.json();
}


// ─────────────────────────────────────────────
// COVER LETTER GENERATOR
// ─────────────────────────────────────────────

async function generateCoverLetter(file, jobTitle, companyName = "") {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("job_title", jobTitle);
    formData.append("company_name", companyName);

    const response = await fetch(`${API_BASE_URL}/cover-letter`, {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Cover letter generation failed");
    }

    return await response.json();
}


// ─────────────────────────────────────────────
// INTERVIEW QUESTIONS GENERATOR
// ─────────────────────────────────────────────

async function generateInterviewQuestions(file, jobTitle) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("job_title", jobTitle);

    const response = await fetch(`${API_BASE_URL}/interview-questions`, {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Interview question generation failed");
    }

    return await response.json();
}
