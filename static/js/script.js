document.getElementById('scrapeBtn').addEventListener('click', async () => {
    const searchTerm = document.getElementById('searchTerm').value.trim();
    if (!searchTerm) {
        alert('Please enter a search term (e.g., dental clinics in London).');
        return;
    }

    // Show permission modal
    const modal = document.getElementById('permissionModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const proceedBtn = document.getElementById('proceedBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    
    modalTitle.textContent = 'Start Scraping?';
    modalMessage.textContent = `Do you want to start scraping phone numbers for "${searchTerm}"? Chrome will open to perform the scrape.`;
    modal.classList.remove('hidden');
    
    const proceed = await new Promise(resolve => {
        proceedBtn.onclick = () => {
            modal.classList.add('hidden');
            resolve(true);
        };
        cancelBtn.onclick = () => {
            modal.classList.add('hidden');
            resolve(false);
        };
    });
    
    if (!proceed) return;

    // Initialize UI
    const progressDiv = document.getElementById('progress');
    const progressText = document.getElementById('progressText');
    const progressBar = document.getElementById('progressBar');
    const resultsDiv = document.getElementById('results');
    const resultsTable = document.getElementById('resultsTable');
    const scrapeBtn = document.getElementById('scrapeBtn');
    progressDiv.classList.remove('hidden');
    resultsDiv.classList.add('hidden');
    resultsTable.innerHTML = '';
    scrapeBtn.disabled = true;
    progressText.textContent = `Scraping business names, URLs, and phone numbers for "${searchTerm}"...`;
    progressBar.style.width = '10%';

    try {
        // Start scraping
        let response = await fetch('/start_scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ search_term: searchTerm })
        });
        let data = await response.json();

        if (data.error) {
            progressDiv.classList.remove('bg-white');
            progressDiv.classList.add('bg-red-100');
            progressText.textContent = `Error: ${data.error}. Check console.`;
            return;
        }

        progressText.textContent = data.message;
        progressBar.style.width = '20%';
        
        // Process batches
        let batch = 0;
        while (data.status !== 'complete') {
            modalTitle.textContent = `Continue Processing Batch ${batch + 1}?`;
            modalMessage.textContent = `Processed ${data.results ? data.results.length : 0} businesses. Proceed with the next batch of 30 businesses? (${data.remaining || 0} businesses remaining)`;
            modal.classList.remove('hidden');
            
            const continueBatch = await new Promise(resolve => {
                proceedBtn.onclick = () => {
                    modal.classList.add('hidden');
                    resolve(true);
                };
                cancelBtn.onclick = () => {
                    modal.classList.add('hidden');
                    resolve(false);
                };
            });
            
            if (!continueBatch) {
                progressText.textContent = 'Scraping cancelled by user.';
                progressDiv.classList.remove('bg-white');
                progressDiv.classList.add('bg-yellow-100');
                break;
            }
            
            progressText.textContent = `Processing batch ${batch + 1}...`;
            progressBar.style.width = `${20 + (batch + 1) * 16}%`;
            
            response = await fetch('/scrape_batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            data = await response.json();
            
            if (data.error) {
                progressDiv.classList.remove('bg-white');
                progressDiv.classList.add('bg-red-100');
                progressText.textContent = `Error: ${data.error}. Check console.`;
                return;
            }
            
            progressText.textContent = data.message;
            
            // Update results table
            resultsTable.innerHTML = '';
            data.results.forEach(result => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td class="px-6 py-3">${result.business_name || 'N/A'}</td>
                    <td class="px-6 py-3">${result.website}</td>
                    <td class="px-6 py-3">${result.phone}</td>
                `;
                resultsTable.appendChild(row);
            });
            
            resultsDiv.classList.remove('hidden');
            batch++;
        }
        
        // Show final results
        progressDiv.classList.remove('bg-white');
        progressDiv.classList.add('bg-green-100');
        progressBar.style.width = '100%';
        
        const downloadWebsites = document.getElementById('downloadWebsites');
        const downloadPhones = document.getElementById('downloadPhones');
        downloadWebsites.href = data.websites_csv;
        downloadPhones.href = data.phones_csv;
        downloadWebsites.classList.remove('hidden');
        downloadPhones.classList.remove('hidden');
        
    } catch (error) {
        progressDiv.classList.remove('bg-white');
        progressDiv.classList.add('bg-red-100');
        progressText.textContent = `Error: ${error.message}. Check console.`;
    } finally {
        scrapeBtn.disabled = false;
    }
});