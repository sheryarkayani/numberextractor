document.getElementById('scrapeBtn').addEventListener('click', async () => {
    const searchTerm = document.getElementById('searchTerm').value.trim();
    if (!searchTerm) {
        alert('Please enter a search term (e.g., dental clinics in Lahore).');
        return;
    }

    const modal = document.getElementById('permissionModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const proceedBtn = document.getElementById('proceedBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    
    modalTitle.textContent = 'Start Scraping?';
    modalMessage.textContent = `Do you want to start scraping phone numbers for "${searchTerm}"? This might take a few minutes.`;
    modal.classList.remove('hidden');
    
    const proceed = await new Promise(resolve => {
        proceedBtn.onclick = () => { modal.classList.add('hidden'); resolve(true); };
        cancelBtn.onclick = () => { modal.classList.add('hidden'); resolve(false); };
    });
    
    if (!proceed) return;

    const progressDiv = document.getElementById('progress');
    const progressText = document.getElementById('progressText');
    const progressBar = document.getElementById('progressBar');
    const resultsDiv = document.getElementById('results');
    const resultsTable = document.getElementById('resultsTable');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');

    progressDiv.classList.remove('hidden', 'bg-red-100', 'bg-green-100');
    resultsDiv.classList.add('hidden');
    resultsTable.innerHTML = '';
    scrapeBtn.disabled = true;
    loadingSpinner.classList.remove('hidden');
    progressText.textContent = `Scraping for "${searchTerm}" has started. Please wait...`;
    progressBar.classList.add('indeterminate');
    
    try {
        const response = await fetch('/start_scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ search_term: searchTerm })
        });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        const jobId = data.job_id;
        pollJobStatus(jobId);

    } catch (error) {
        progressDiv.classList.add('bg-red-100');
        progressText.textContent = `Error: ${error.message}`;
        scrapeBtn.disabled = false;
        loadingSpinner.classList.add('hidden');
    }
});

function pollJobStatus(jobId, startTime = Date.now()) {
    const progressDiv = document.getElementById('progress');
    const progressText = document.getElementById('progressText');
    const progressBar = document.getElementById('progressBar');
    const resultsDiv = document.getElementById('results');
    const resultsTable = document.getElementById('resultsTable');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    const MAX_POLL_DURATION = 10 * 60 * 1000; // 10 minutes
    const elapsedTime = Date.now() - startTime;
    
    if (elapsedTime > MAX_POLL_DURATION) {
        throw new Error('Scraping timeout. Please try again.');
    }

    fetch(`/scrape_status/${jobId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'running') {
                // Update progress bar - maybe with a pulsing animation or indeterminate state
                const currentWidth = parseFloat(progressBar.style.width) || 0;
                const newWidth = currentWidth < 95 ? currentWidth + 2 : 95; // Slow progress
                progressBar.style.width = `${newWidth}%`;
                progressText.textContent = 'Scraping is in progress, please wait...';
                setTimeout(() => pollJobStatus(jobId, startTime), 3000); // Poll every 3 seconds

            } else if (data.status === 'complete') {
                progressBar.style.width = '100%';
                progressDiv.classList.add('bg-green-100');
                progressText.textContent = 'Scraping complete!';
                loadingSpinner.classList.add('hidden');
                scrapeBtn.disabled = false;
                
                resultsTable.innerHTML = ''; // Clear previous results
                if (data.result && data.result.length > 0) {
                    data.result.forEach(business => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td class="px-6 py-4 whitespace-nowrap">${business.business_name}</td>
                            <td class="px-6 py-4 whitespace-nowrap"><a href="${business.website}" target="_blank" class="text-blue-600 hover:underline">${business.website}</a></td>
                            <td class="px-6 py-4 whitespace-nowrap">${business.phone}</td>
                        `;
                        resultsTable.appendChild(row);
                    });
                } else {
                    resultsTable.innerHTML = '<tr><td colspan="3" class="text-center py-4">No businesses found.</td></tr>';
                }
                
                resultsDiv.classList.remove('hidden');
                const downloadWebsites = document.getElementById('downloadWebsites');
                const downloadPhones = document.getElementById('downloadPhones');
                downloadWebsites.href = data.websites_csv;
                downloadPhones.href = data.phones_csv;
                downloadWebsites.classList.remove('hidden');
                downloadPhones.classList.remove('hidden');

            } else if (data.status === 'failed') {
                const errorMsg = data.error || 'Scraping job failed. Please check the logs.';
                throw new Error(errorMsg);

            } else if (data.status === 'not_found') {
                throw new Error('Scraping job not found. Please try again.');
            }
        })
        .catch(error => {
            progressDiv.classList.add('bg-red-100');
            progressText.textContent = `Error: ${error.message}`;
            progressBar.style.width = '100%';
            loadingSpinner.classList.add('hidden');
            scrapeBtn.disabled = false;
        });
}