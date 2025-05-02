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
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    modalTitle.textContent = 'Start Scraping?';
    modalMessage.textContent = `Do you want to start scraping phone numbers for "${searchTerm}"?`;
    modal.classList.remove('hidden');
    
    const proceed = await new Promise(resolve => {
        proceedBtn.onclick = () => { modal.classList.add('hidden'); resolve(true); };
        cancelBtn.onclick = () => { modal.classList.add('hidden'); resolve(false); };
    });
    
    if (!proceed) return;

    const progressDiv = document.getElementById('progress');
    const progressText = document.getElementById('progressText');
    const progressBar = document.getElementById('progressBar');
    const etaText = document.getElementById('etaText');
    const resultsDiv = document.getElementById('results');
    const resultsTable = document.getElementById('resultsTable');
    const scrapeBtn = document.getElementById('scrapeBtn');
    
    progressDiv.classList.remove('hidden', 'bg-red-100', 'bg-yellow-100', 'bg-green-100');
    progressDiv.classList.add('bg-white');
    resultsDiv.classList.add('hidden');
    resultsTable.innerHTML = '';
    scrapeBtn.disabled = true;
    progressText.textContent = `Initializing scrape for "${searchTerm}"...`;
    progressBar.style.width = '5%';
    loadingSpinner.classList.remove('hidden');
    
    try {
        let response = await fetch('/start_scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ search_term: searchTerm })
        });
        let data = await response.json();
        loadingSpinner.classList.add('hidden');

        if (data.error) {
            progressDiv.classList.add('bg-red-100');
            progressText.textContent = `Error: ${data.error}. Check logs.`;
            alert(`Error: ${data.error}`);
            return;
        }

        progressText.textContent = data.message;
        progressBar.style.width = '10%';
        const totalBusinesses = data.business_count;
        let batch = 0;
        let batchStartTime;

        while (data.status !== 'complete') {
            modalTitle.textContent = `Continue Processing Batch ${batch + 1}?`;
            modalMessage.textContent = `Processed ${data.results ? data.results.length : 0} of ${totalBusinesses} businesses. Proceed with next batch of 30? (${data.remaining || 0} remaining)`;
            modal.classList.remove('hidden');
            
            const continueBatch = await new Promise(resolve => {
                proceedBtn.onclick = () => { modal.classList.add('hidden'); resolve(true); };
                cancelBtn.onclick = () => { modal.classList.add('hidden'); resolve(false); };
            });
            
            if (!continueBatch) {
                progressDiv.classList.add('bg-yellow-100');
                progressText.textContent = 'Scraping cancelled by user.';
                alert('Scraping cancelled.');
                break;
            }
            
            batchStartTime = Date.now();
            progressText.textContent = `Processing batch ${batch + 1}...`;
            progressBar.style.width = `${10 + (batch + 1) * 10}%`;
            loadingSpinner.classList.remove('hidden');
            
            response = await fetch('/scrape_batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            data = await response.json();
            loadingSpinner.classList.add('hidden');
            
            if (data.error) {
                progressDiv.classList.add('bg-red-100');
                progressText.textContent = `Error: ${data.error}. Check logs.`;
                alert(`Error: ${data.error}`);
                return;
            }
            
            const batchDuration = (Date.now() - batchStartTime) / 1000;
            const remainingBatches = Math.ceil(data.remaining / 30);
            const etaSeconds = remainingBatches * batchDuration;
            etaText.textContent = `Estimated time remaining: ${Math.round(etaSeconds / 60)} minutes`;
            
            progressText.textContent = data.message;
            resultsTable.innerHTML = '';
            data.results.forEach(result => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td class="px-6 py-3">${result.business_name || 'N/A'}</td>
                    <td class="px-6 py-3"><a href="${result.website}" target="_blank" class="text-blue-600 hover:underline">${result.website}</a></td>
                    <td class="px-6 py-3">${result.phone}</td>
                `;
                resultsTable.appendChild(row);
            });
            
            resultsDiv.classList.remove('hidden');
            batch++;
        }
        
        if (data.status === 'complete') {
            progressDiv.classList.add('bg-green-100');
            progressBar.style.width = '100%';
            progressText.textContent = data.message;
            etaText.textContent = '';
            const downloadWebsites = document.getElementById('downloadWebsites');
            const downloadPhones = document.getElementById('downloadPhones');
            downloadWebsites.href = data.websites_csv;
            downloadPhones.href = data.phones_csv;
            downloadWebsites.classList.remove('hidden');
            downloadPhones.classList.remove('hidden');
            alert('Scraping completed successfully!');
        }
        
    } catch (error) {
        progressDiv.classList.add('bg-red-100');
        progressText.textContent = `Error: ${error.message}. Check logs.`;
        alert(`Error: ${error.message}`);
    } finally {
        scrapeBtn.disabled = false;
        loadingSpinner.classList.add('hidden');
    }
});