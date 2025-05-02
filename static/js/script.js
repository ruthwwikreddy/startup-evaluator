const examples = {
    1: "A mobile app that uses AI to create personalized meal plans and recipes based on dietary preferences, health goals, and available ingredients. The app would analyze users' dietary restrictions, nutritional needs, and taste preferences to generate customized meal plans. It would also integrate with smart kitchen appliances and grocery delivery services to streamline the cooking process. The AI would learn from user feedback and adapt recommendations over time, creating increasingly personalized and effective meal plans.",
    2: "An immersive VR fitness platform that transforms traditional workouts into engaging virtual experiences with gamification and social features. Users can join virtual classes, compete with friends, and explore exotic locations while exercising. The platform would track performance metrics and provide real-time feedback through haptic feedback and visual cues. It would also offer personalized workout programs and integrate with popular fitness trackers and smart equipment.",
    3: "An online marketplace connecting eco-conscious consumers with sustainable fashion brands, featuring a carbon footprint calculator for each purchase. The platform would verify the sustainability claims of brands and provide transparent information about materials, manufacturing processes, and supply chains. Users could track their environmental impact and earn rewards for making sustainable choices. The marketplace would also include a resale section to promote circular fashion.",
    // Add more examples if needed
};

function fillExample(number) {
    const ideaTextArea = document.getElementById('ideaText');
    if (examples[number]) {
        ideaTextArea.value = examples[number];
        ideaTextArea.focus(); // Optional: bring focus to the textarea
    }
}

document.getElementById('evaluationForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const ideaText = document.getElementById('ideaText').value;
    const submitButton = document.getElementById('submitBtn');
    const resultsArea = document.getElementById('resultsArea');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const saveButtons = document.getElementById('saveButtons');

    if (!ideaText.trim()) {
        alert('Please enter your startup idea.');
        return;
    }

    // Show loading indicator and disable button
    resultsArea.innerHTML = ''; // Clear previous results
    loadingIndicator.classList.remove('d-none');
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Evaluating...';
    saveButtons.classList.add('d-none'); // Hide save buttons

    try {
        const response = await fetch('/evaluate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ idea: ideaText })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const results = await response.json();
        displayResults(results);
        saveButtons.classList.remove('d-none'); // Show save buttons after results

    } catch (error) {
        console.error('Error during evaluation:', error);
        resultsArea.innerHTML = `<div class="alert alert-danger" role="alert">An error occurred during evaluation. Please try again. Error: ${error.message}</div>`;
    } finally {
        // Hide loading indicator and re-enable button
        loadingIndicator.classList.add('d-none');
        submitButton.disabled = false;
        submitButton.innerHTML = 'Evaluate Idea';
    }
});

function displayResults(results) {
    const resultsArea = document.getElementById('resultsArea');
    let htmlContent = `<h2 class="animate__animated animate__fadeInDown">Evaluation Results</h2>`;

    // Helper function to format lists
    const formatList = (items) => {
        if (!Array.isArray(items) || items.length === 0) return '<p>N/A</p>';
        return `<ul>${items.map(item => `<li>${item}</li>`).join('')}</ul>`;
    };

    // Display sections dynamically based on received data
    const sections = {
        'Executive Summary': results.executive_summary,
        'Market Potential': results.market_potential,
        'Uniqueness & Innovation': results.uniqueness_innovation,
        'Business Model': results.business_model,
        'Risk Assessment': results.risk_assessment,
        'Potential Challenges': results.potential_challenges,
        'Recommendations': results.recommendations,
        'Pros': results.pros ? formatList(results.pros) : null,
        'Cons': results.cons ? formatList(results.cons) : null,
        'Technical Feasibility': results.technical_feasibility,
        'Investment Worthiness': results.investment_worthiness,
        'Scalability': results.scalability,
        'Target Audience': results.target_audience,
        'Competitive Advantage': results.competitive_advantage
    };

    for (const [title, content] of Object.entries(sections)) {
        if (content) { // Only display if content exists
            htmlContent += `
                <div class="result-section animate__animated animate__fadeInUp">
                    <h3>${title.replace(/_/g, ' ')}</h3>
                    ${title === 'Pros' || title === 'Cons' ? content : `<p>${content}</p>`}
                </div>
            `;
        }
    }

    // Overall Score (assuming it exists in results)
    if (results.overall_score !== undefined) {
        let scoreClass = 'score-neutral';
        if (results.overall_score >= 7) scoreClass = 'score-positive';
        else if (results.overall_score < 4) scoreClass = 'score-negative';
        
        htmlContent += `
            <div class="result-section animate__animated animate__fadeInUp">
                <h3>Overall Score</h3>
                <p><strong class="evaluation-score ${scoreClass}">${results.overall_score} / 10</strong></p>
                <p>${results.score_rationale || 'Based on the analysis above.'}</p> 
            </div>
        `;
    }
    
    resultsArea.innerHTML = htmlContent;
     // Store results globally for saving
     window.currentResults = results; 
}

// Save results functionality (assuming window.currentResults is set in displayResults)
function saveResults(format) {
    if (!window.currentResults) {
        alert('No results to save.');
        return;
    }

    let content = '';
    let filename = 'startup_evaluation';
    let mimeType = '';

    if (format === 'json') {
        content = JSON.stringify(window.currentResults, null, 2);
        filename += '.json';
        mimeType = 'application/json';
    } else if (format === 'txt') {
        content = `Startup Idea Evaluation\n========================\n\n`;
        content += `Idea Submitted:\n${document.getElementById('ideaText').value}\n\n`;
        
         // Helper function to format lists for text
        const formatListTxt = (items) => {
            if (!Array.isArray(items) || items.length === 0) return 'N/A\n';
            return items.map(item => `- ${item}`).join('\n') + '\n';
        };

        // Append sections to text content
        const sections = {
            'Executive Summary': window.currentResults.executive_summary,
            'Market Potential': window.currentResults.market_potential,
            'Uniqueness & Innovation': window.currentResults.uniqueness_innovation,
            'Business Model': window.currentResults.business_model,
            'Risk Assessment': window.currentResults.risk_assessment,
            'Potential Challenges': window.currentResults.potential_challenges,
            'Recommendations': window.currentResults.recommendations,
            'Pros': window.currentResults.pros ? formatListTxt(window.currentResults.pros) : null,
            'Cons': window.currentResults.cons ? formatListTxt(window.currentResults.cons) : null,
            'Technical Feasibility': window.currentResults.technical_feasibility,
            'Investment Worthiness': window.currentResults.investment_worthiness,
            'Scalability': window.currentResults.scalability,
            'Target Audience': window.currentResults.target_audience,
            'Competitive Advantage': window.currentResults.competitive_advantage
        };

        for (const [title, sectionContent] of Object.entries(sections)) {
            if (sectionContent) {
                 content += `\n${title.replace(/_/g, ' ')}:\n------------------------\n`;
                content += sectionContent;
            }
        }
        
        // Overall Score
        if (window.currentResults.overall_score !== undefined) {
            content += `\nOverall Score:\n------------------------\n`;
            content += `${window.currentResults.overall_score} / 10\n`;
            content += `${window.currentResults.score_rationale || 'Based on the analysis.'}\n`;
        }

        filename += '.txt';
        mimeType = 'text/plain';
    } else {
        alert('Invalid format specified.');
        return;
    }

    const blob = new Blob([content], { type: mimeType });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
}
