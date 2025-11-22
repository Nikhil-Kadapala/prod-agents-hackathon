// Learning Resource Curator - Frontend Application

const API_BASE = '/api/v1';

// DOM Elements
const form = document.getElementById('analysisForm');
const resultsSection = document.getElementById('resultsSection');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const error = document.getElementById('error');
const analyzeBtn = document.getElementById('analyzeBtn');

// Form submission handler
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get form data
    const formData = {
        target_job_title: document.getElementById('targetJob').value,
        resume_text: document.getElementById('resume').value,
        job_description: document.getElementById('jobDescription').value,
        filters: {
            free_only: document.getElementById('freeOnly').checked,
            max_duration_hours: 100,
            resource_types: ['course', 'tutorial', 'video']
        }
    };
    
    // Show loading
    resultsSection.style.display = 'block';
    loading.style.display = 'block';
    results.style.display = 'none';
    error.style.display = 'none';
    analyzeBtn.disabled = true;
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    try {
        // Call API
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display results
        displayResults(data);
        
    } catch (err) {
        console.error('Analysis failed:', err);
        showError(err.message);
    } finally {
        loading.style.display = 'none';
        analyzeBtn.disabled = false;
    }
});

// Display results
function displayResults(data) {
    if (data.status === 'failed') {
        showError(data.error_message || 'Analysis failed');
        return;
    }
    
    const analysisResult = data.analysis_result;
    const curatedResources = data.curated_resources;
    
    // Update stats
    document.getElementById('skillGapsCount').textContent = 
        analysisResult.skill_gaps.length;
    document.getElementById('resourcesCount').textContent = 
        Object.values(curatedResources).reduce((sum, resources) => sum + resources.length, 0);
    document.getElementById('existingSkillsCount').textContent = 
        analysisResult.existing_skills.length;
    
    // Display existing skills
    displayExistingSkills(analysisResult.existing_skills);
    
    // Display skill gaps and resources
    displaySkillGaps(analysisResult.skill_gaps, curatedResources);
    
    // Show results
    results.style.display = 'block';
}

// Display existing skills
function displayExistingSkills(skills) {
    const container = document.getElementById('existingSkillsList');
    container.innerHTML = '';
    
    if (skills.length === 0) {
        container.innerHTML = '<p>No existing skills identified.</p>';
        return;
    }
    
    skills.forEach(skill => {
        const card = document.createElement('div');
        card.className = 'skill-card';
        card.innerHTML = `
            <h4>${skill.skill_name}</h4>
            <div class="skill-badges">
                <span class="badge badge-${skill.proficiency_level}">${skill.proficiency_level}</span>
                <span class="badge">${skill.years_experience} years</span>
            </div>
        `;
        container.appendChild(card);
    });
}

// Display skill gaps and resources
function displaySkillGaps(skillGaps, resources) {
    const container = document.getElementById('skillGapsList');
    container.innerHTML = '';
    
    if (skillGaps.length === 0) {
        container.innerHTML = '<p>No skill gaps identified! 🎉</p>';
        return;
    }
    
    skillGaps.forEach(gap => {
        const card = document.createElement('div');
        card.className = 'skill-card';
        
        const skillResources = resources[gap.skill_name] || [];
        
        card.innerHTML = `
            <h4>${gap.skill_name}</h4>
            <div class="skill-badges">
                <span class="badge badge-${gap.priority}">${gap.priority}</span>
                <span class="badge badge-${gap.required_level}">Required: ${gap.required_level}</span>
            </div>
            <p style="margin-top: 12px; color: #666;">
                <strong>Recommended Starting Point:</strong> ${gap.recommended_starting_level}
            </p>
            ${displayResources(skillResources)}
        `;
        
        container.appendChild(card);
    });
}

// Display resources for a skill
function displayResources(resources) {
    if (resources.length === 0) {
        return '<p style="margin-top: 16px; color: #999;">No resources found for this skill.</p>';
    }
    
    let html = '<div class="resource-list">';
    html += '<h5 style="margin-bottom: 12px; color: #667eea;">📚 Curated Resources:</h5>';
    
    resources.forEach(resource => {
        html += `
            <div class="resource-item">
                <div class="resource-title">
                    <a href="${resource.url}" target="_blank" rel="noopener">
                        ${resource.title}
                    </a>
                </div>
                <div class="resource-meta">
                    <span>📦 ${resource.provider}</span>
                    <span>📝 ${resource.resource_type}</span>
                    <span>⏱️ ${resource.duration_hours}h</span>
                    ${resource.is_free ? '<span>💰 Free</span>' : ''}
                    ${resource.rating ? `<span>⭐ ${resource.rating}/5</span>` : ''}
                </div>
                ${resource.description ? `
                    <div class="resource-description">
                        ${resource.description}
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

// Show error message
function showError(message) {
    error.style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
}

// Load sample data (for testing)
function loadSample() {
    document.getElementById('targetJob').value = 'Senior Full Stack Engineer';
    
    document.getElementById('resume').value = `John Doe
Software Engineer

EXPERIENCE:
- 3 years of Python development
- Built REST APIs with Flask
- Experience with PostgreSQL databases
- Basic knowledge of Docker

SKILLS:
- Python, JavaScript
- Flask, jQuery
- PostgreSQL
- Git, Linux
`;
    
    document.getElementById('jobDescription').value = `Senior Full Stack Engineer

REQUIREMENTS:
- 5+ years of experience
- Expert in React and Node.js
- Strong AWS/cloud experience
- Kubernetes and Docker
- CI/CD pipelines
- TypeScript proficiency
- Microservices architecture

Nice to have:
- GraphQL
- Terraform
- Redis caching
`;
}

// Add sample button (for development)
if (window.location.hostname === 'localhost') {
    const sampleBtn = document.createElement('button');
    sampleBtn.textContent = 'Load Sample Data';
    sampleBtn.className = 'btn-primary';
    sampleBtn.style.marginBottom = '20px';
    sampleBtn.style.background = '#28a745';
    sampleBtn.onclick = (e) => {
        e.preventDefault();
        loadSample();
    };
    form.insertBefore(sampleBtn, form.firstChild);
}

