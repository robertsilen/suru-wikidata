// SURU Wikidata Extension - Content Script
console.log('=== SURU Extension: Content script loaded ===');

// Function to create the content container
function createContentContainer() {
    const container = document.createElement('div');
    container.className = 'suru-content';
    container.innerHTML = '<div class="suru-loading">🔄 Loading Wikidata lexeme details...</div>';
    console.log('Created suru-content container with loading message');
    return container;
}

// Function to copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        console.log('Copied to clipboard:', text);
    } catch (err) {
        console.error('Failed to copy to clipboard:', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    }
}

// Function to create copy icon
function createCopyIcon(qCode) {
    return `<span class="suru-copy-icon" data-qcode="${qCode}" title="Copy Q-code to clipboard">📋</span>`;
}

// Function to create radiobutton for P5137 selection
function createRadioButton(qCode, translationWord) {
    const cleanWord = translationWord.replace(/^\d+\.\s*/, ''); // Remove number prefix
    return `<input type="radio" name="p5137_selection" class="suru-radio" data-qcode="${qCode}" data-translation="${cleanWord}" title="Select for flask creation">`;
}

// Function to insert content after first hr.display-para
function insertContent(container) {
    const targetElement = document.querySelector('hr.display-para');
    if (targetElement) {
        targetElement.parentNode.insertBefore(container, targetElement.nextSibling);
    } else {
        console.error('Could not find hr.display-para element, trying fallback insertion');
        // Fallback: try to insert at the beginning of the body or after the first h1
        const fallbackTarget = document.querySelector('h1') || document.body;
        if (fallbackTarget) {
            if (fallbackTarget === document.body) {
                fallbackTarget.appendChild(container);
            } else {
                fallbackTarget.parentNode.insertBefore(container, fallbackTarget.nextSibling);
            }
            console.log('Inserted content using fallback method');
        } else {
            console.error('Could not find any suitable insertion point');
        }
    }
}

// Function to collect words from vastine spans
function collectVastineWords() {
    const vastineSpans = document.querySelectorAll('span.vastine');
    const wordsWithGroups = [];
    const seenWords = new Set();
    
    vastineSpans.forEach(span => {
        let text = span.textContent.trim();
        // Remove semicolon from the end if present
        if (text.endsWith(';')) {
            text = text.slice(0, -1);
        }
        // Remove | characters from the middle of the word
        text = text.replace(/\|/g, '');
        
        if (text && !seenWords.has(text)) {
            seenWords.add(text);
            
            // Find the parent merkitysryhma div and get its ID
            let parentDiv = span.closest('div.merkitysryhma');
            let groupId = parentDiv ? parentDiv.id : '';
            
            wordsWithGroups.push({
                word: text,
                groupId: groupId
            });
        }
    });
    return wordsWithGroups;
}

// Function to search for Swedish lexemes
async function searchSwedishLexemes(word) {
    const sparqlQuery = `
    SELECT DISTINCT ?lexeme ?lemma ?sense ?gloss_fi ?item ?item_sv WHERE {
    ?lexeme dct:language wd:Q9027 ;  # Swedish language
            wikibase:lemma ?lemma ;
            wikibase:lexicalCategory wd:Q1084.  # Noun
    FILTER(?lemma = "${word}"@sv)

    OPTIONAL {
        ?lexeme ontolex:sense ?sense .
        OPTIONAL {
        ?sense skos:definition ?gloss_fi .
        FILTER(LANG(?gloss_fi) = "fi")
        }
        OPTIONAL {
        ?sense wdt:P5137 ?item .
        ?item rdfs:label ?item_sv .
        FILTER(LANG(?item_sv) = "sv")
        }
    }
    }`;

    const url = 'https://query.wikidata.org/sparql';
    const headers = {
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/x-www-form-urlencoded'
    };
    const body = new URLSearchParams({
        'query': sparqlQuery,
        'format': 'json'
    });

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: body
        });
        
        if (!response.ok) {
            console.error('SPARQL query failed:', response.status, response.statusText);
            return [];
        }

        const data = await response.json();
        if (!data.results || !data.results.bindings || data.results.bindings.length === 0) {
            return [];
        }

        // Return all bindings instead of just the first one
        return data.results.bindings.map(binding => ({
            lexeme: binding.lexeme.value,
            lemma: binding.lemma.value,
            sense: binding.sense?.value || '',
            gloss_fi: binding.gloss_fi?.value || '',
            item: binding.item?.value || '',
            item_sv: binding.item_sv?.value || ''
        }));
    } catch (error) {
        console.error('Error executing SPARQL query:', error);
        return [];
    }
}

// Function to execute SPARQL query
async function executeSparqlQuery(suruId) {
    console.log('Executing SPARQL query for suru_id:', suruId);
    
    // Collect vastine words
    const vastineWords = collectVastineWords();
    console.log('Collected vastine words:', vastineWords);
    
    // Create word filter for Swedish lexemes
    const wordFilter = vastineWords.map(word => `"${word.word}"@sv`).join(', ');
    
    const sparqlQuery = `
    SELECT DISTINCT ?lexeme ?lemma ?suru_id ?sense ?gloss_sv ?item ?itemLabel ?itemDescription ?lexeme_sv ?lemma_sv ?gloss_sv_fi ?sense_sv ?translation_lexeme ?translation_lemma
    WHERE {
      # Base query for Finnish lexeme with suru_id
      ?lexeme dct:language wd:Q1412 ;
              wikibase:lemma ?lemma ;
              wdt:P12682 ?suru_id ;
              wdt:P12682 "${suruId}" .
      
      # Get the primary sense
      OPTIONAL {
        ?lexeme ontolex:sense ?sense .
      }
      
      # Get Swedish gloss for the sense
      OPTIONAL {
        ?sense skos:definition ?gloss_sv .
        FILTER(LANG(?gloss_sv) = "sv")
      }
      
      # Get the item (P5137) and its Swedish label
      OPTIONAL {
        ?sense wdt:P5137 ?item .
        OPTIONAL {
          ?item rdfs:label ?itemLabel .
          FILTER(LANG(?itemLabel) = "sv")
        }
        OPTIONAL {
          ?item schema:description ?itemDescription .
          FILTER(LANG(?itemDescription) = "sv")
        }
      }
      
      # Get Swedish lexeme through the item
      OPTIONAL {
        ?sense wdt:P5137 ?item .
        ?sense_sv wdt:P5137 ?item .
        ?lexeme_sv ontolex:sense ?sense_sv ;
                  dct:language wd:Q9027 ;
                  wikibase:lemma ?lemma_sv .
        OPTIONAL {
          ?sense_sv skos:definition ?gloss_sv_fi .
          FILTER(LANG(?gloss_sv_fi) = "fi")
        }
      }
    }`;

    console.log('SPARQL Query:', sparqlQuery);

    const url = 'https://query.wikidata.org/sparql';
    const headers = {
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/x-www-form-urlencoded'
    };
    const body = new URLSearchParams({
        'query': sparqlQuery,
        'format': 'json'
    });

    try {
        console.log('Sending request to Wikidata...');
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: body
        });
        
        if (!response.ok) {
            console.error('SPARQL query failed:', response.status, response.statusText);
            const text = await response.text();
            console.error('Response text:', text);
            return null;
        }

        const data = await response.json();
        console.log('SPARQL response:', data);
        
        if (!data.results || !data.results.bindings) {
            console.error('Invalid response format:', data);
            return null;
        }

        console.log('Number of results:', data.results.bindings.length);
        return data;
    } catch (error) {
        console.error('Error executing SPARQL query:', error);
        return null;
    }
}

// Function to create translation table
async function createTranslationTable() {
    // Collect vastine words
    const vastineWords = collectVastineWords();
    console.log('Collected vastine words:', vastineWords);

    if (vastineWords.length === 0) {
        return '';
    }

    // Search for Swedish lexemes for each vastine word
    const translationResults = await Promise.all(
        vastineWords.map(word => searchSwedishLexemes(word.word))
    );

    let content = `
        <div class="suru-table-container">
            <table class="suru-table">
                <thead>
                    <tr>
                        <th>Translation word (and lexeme if found)</th>
                        <th>Sense</th>
                        <th>P5137</th>
                    </tr>
                </thead>
                <tbody>
    `;

    for (let i = 0; i < vastineWords.length; i++) {
        const word = vastineWords[i];
        const results = translationResults[i];
        
        if (results && Array.isArray(results) && results.length > 0) {
            // Sort results by sense number (S1 before S2, etc.)
            const sortedResults = results.sort((a, b) => {
                const aSense = a.sense ? a.sense.split('/').pop() : '';
                const bSense = b.sense ? b.sense.split('/').pop() : '';
                
                // Extract numbers from sense codes (e.g., "S1" -> 1, "S2" -> 2)
                const aNum = parseInt(aSense.replace(/[^0-9]/g, '')) || 0;
                const bNum = parseInt(bSense.replace(/[^0-9]/g, '')) || 0;
                
                return aNum - bNum;
            });
            
            // Handle multiple senses for the same word
            for (let senseIndex = 0; senseIndex < sortedResults.length; senseIndex++) {
                const result = sortedResults[senseIndex];
                let lexemeInfo = '';
                let senseInfo = '';
                let p5137Info = '';
                
                const lCode = result.lexeme.split('/').pop();
                lexemeInfo = ` <a href="${result.lexeme}" target="_blank" class="suru-link">(${lCode})</a>`;
                
                // Add sense link if available
                if (result.sense) {
                    const sCode = result.sense.split('/').pop();
                    senseInfo = `<a href="${result.sense}" target="_blank" class="suru-link">${sCode}</a>`;
                }
                
                // Add P5137 info if available
                if (result.item && result.item_sv) {
                    const qCode = result.item.split('/').pop();
                    
                    // Fetch sitelinks for this P5137 object
                    const sitelinks = await fetchSitelinks(qCode);
                    let sitelinksHTML = '';
                    if (sitelinks) {
                        sitelinksHTML = createSitelinksHTML(sitelinks);
                    }
                    
                    // Add radiobutton after the clipboard icon
                    const radioButton = createRadioButton(qCode, word.word);
                    p5137Info = `<a href="${result.item}" target="_blank" class="suru-link">${result.item_sv} (${qCode}${createCopyIcon(qCode)} ${radioButton}${sitelinksHTML ? ', ' + sitelinksHTML : ''})</a>`;
                }

                // Only show the word in the first row for this lexeme
                const groupIdDisplay = word.groupId ? `${word.groupId}. ` : '';
                const wordCell = senseIndex === 0 ? `${groupIdDisplay}${word.word}${lexemeInfo}` : `&nbsp;`;
                
                content += `
                    <tr>
                        <td>${wordCell}</td>
                        <td>${senseInfo}</td>
                        <td>${p5137Info}</td>
                    </tr>
                `;
            }
        } else {
            // No results found for this word
            const searchUrl = `https://www.wikidata.org/w/index.php?search=${encodeURIComponent(word.word)}&title=Special%3ASearch&profile=advanced&fulltext=1&ns146=1`;
            const createUrl = `https://www.wikidata.org/wiki/Special:NewLexeme?lemma=${encodeURIComponent(word.word)}&language=sv&lexicalCategory=Q1084`;
            const svenskaUrl = `https://svenska.se/tre/?sok=${encodeURIComponent(word.word)}&pz=1`;
            const lexemeInfo = ` <a href="${createUrl}" target="_blank" class="suru-link">(create</a>, <a href="${searchUrl}" target="_blank" class="suru-link">search</a>, <a href="${svenskaUrl}" target="_blank" class="suru-link">svenska.se)</a>`;
            const groupIdDisplay = word.groupId ? `${word.groupId}. ` : '';
            
            content += `
                <tr>
                    <td>${groupIdDisplay}${word.word}${lexemeInfo}</td>
                    <td></td>
                    <td></td>
                </tr>
            `;
        }
    }

    content += `
                </tbody>
            </table>
        </div>`;
    return content;
}

// Function to create table from SPARQL results
async function createTable(results) {
    console.log('Creating table from results:', results);
    
    if (!results || !results.results || !results.results.bindings) {
        console.error('Invalid results format:', results);
        return '<div class="suru-error">No results found or invalid response format</div>';
    }

    const bindings = results.results.bindings;
    console.log('Number of bindings:', bindings.length);
    
    if (bindings.length === 0) {
        const hakusanaElement = document.querySelector('h1.hakusana');
        const searchWord = hakusanaElement ? hakusanaElement.textContent.trim() : '';
        const searchUrl = `https://www.wikidata.org/w/index.php?search=${encodeURIComponent(searchWord)}&title=Special%3ASearch&profile=advanced&fulltext=1&ns146=1`;
        const searchObjectsUrl = `https://www.wikidata.org/w/index.php?search=${encodeURIComponent(searchWord)}&ns0=1`;
        
        // Get the suru_id from the URL to display in the error message
        const urlParams = new URLSearchParams(window.location.search);
        let suruId = urlParams.get('suru_id');
        if (suruId && suruId.startsWith('SURU_')) {
            suruId = suruId.substring(5);
        }
        
        const suruIdDisplay = suruId ? createCopyIcon(suruId) : '';
        const flaskUrl = `http://localhost:5001/add?lang=fi&lemma=${encodeURIComponent(searchWord)}&category=noun&suru_id=${suruId || ''}`;
        
        return `<div class="suru-error">No lexemes with suru_id ${suruIdDisplay}. <a href="${searchUrl}" target="_blank" class="suru-link">Search lexemes</a> | <a href="${searchObjectsUrl}" target="_blank" class="suru-link">Search objects</a> | <a href="https://www.wikidata.org/wiki/Special:NewLexeme?lemma=${encodeURIComponent(searchWord)}" target="_blank" class="suru-link">Create on Wikidata</a> | <a href="${flaskUrl}" target="_blank" class="suru-link" id="flask-create-link">Create with flask</a></div>`;
    }

    let content = `
        <div class="suru-table-container">
            <table class="suru-table">
                <thead>
                    <tr>
                        <th>Lemma</th>
                        <th>Sense</th>
                        <th>P5137</th>
                        <th>Lemma (SV)</th>
                    </tr>
                </thead>
                <tbody>
    `;

    for (let index = 0; index < bindings.length; index++) {
        const binding = bindings[index];
        console.log(`Processing binding ${index}:`, binding);
        
        const lexeme = binding.lexeme?.value || '';
        const lemma = binding.lemma?.value || '';
        const sense = binding.sense?.value || '';
        const item = binding.item?.value || '';
        const itemLabel = binding.itemLabel?.value || '';
        const lexeme_sv = binding.lexeme_sv?.value || '';
        const lemma_sv = binding.lemma_sv?.value || '';

        // Extract L-codes and S-codes
        const lCode = lexeme.split('/').pop();
        const sCode = sense.split('/').pop();
        const lCodeSv = lexeme_sv.split('/').pop();
        const qCode = item.split('/').pop();

        console.log(`Row ${index} data:`, {
            lexeme, lemma, sense, item, itemLabel, lexeme_sv, lemma_sv,
            lCode, sCode, lCodeSv, qCode
        });

        let p5137Cell = '';
        if (item && itemLabel) {
            // Fetch sitelinks for this P5137 object
            const sitelinks = await fetchSitelinks(qCode);
            let sitelinksHTML = '';
            if (sitelinks) {
                sitelinksHTML = createSitelinksHTML(sitelinks);
            }
            
            p5137Cell = `<a href="${item}" target="_blank" class="suru-link">${itemLabel} (${qCode}${createCopyIcon(qCode)}${sitelinksHTML ? ', ' + sitelinksHTML : ''})</a>`;
        }

        content += `
            <tr>
                <td><a href="${lexeme}" target="_blank" class="suru-link">${lemma} (${lCode})</a></td>
                <td><a href="${sense}" target="_blank" class="suru-link">${sCode}</a></td>
                <td>${p5137Cell}</td>
                <td><a href="${lexeme_sv}" target="_blank" class="suru-link">${lemma_sv} (${lCodeSv})</a></td>
            </tr>
        `;
    }

    content += `
                </tbody>
            </table>
        </div>`;
    return content;
}

// Function to fetch sitelinks from Wikidata API
async function fetchSitelinks(qCode) {
    if (!qCode) return null;
    
    try {
        const url = `https://www.wikidata.org/wiki/Special:EntityData/${qCode}.json`;
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error('Failed to fetch sitelinks for', qCode, response.status);
            return null;
        }
        
        const data = await response.json();
        const entity = data.entities[qCode];
        
        if (!entity || !entity.sitelinks) {
            return null;
        }
        
        const sitelinks = entity.sitelinks;
        const result = {
            sv: null,
            fi: null,
            en: null,
            otherCount: 0
        };
        
        // Extract specific language sitelinks
        if (sitelinks.svwiki) {
            result.sv = {
                title: sitelinks.svwiki.title,
                url: sitelinks.svwiki.url
            };
        }
        if (sitelinks.fiwiki) {
            result.fi = {
                title: sitelinks.fiwiki.title,
                url: sitelinks.fiwiki.url
            };
        }
        if (sitelinks.enwiki) {
            result.en = {
                title: sitelinks.enwiki.title,
                url: sitelinks.enwiki.url
            };
        }
        
        // Count other languages (excluding sv, fi, en)
        const otherLanguages = Object.keys(sitelinks).filter(key => 
            !['svwiki', 'fiwiki', 'enwiki'].includes(key)
        );
        result.otherCount = otherLanguages.length;
        
        return result;
    } catch (error) {
        console.error('Error fetching sitelinks for', qCode, error);
        return null;
    }
}

// Function to create sitelinks HTML
function createSitelinksHTML(sitelinks) {
    if (!sitelinks) return '';
    
    let html = '';
    
    // Add language codes as links
    const languages = [];
    if (sitelinks.sv) {
        languages.push(`<a href="${sitelinks.sv.url}" target="_blank" class="suru-link">sv</a>`);
    }
    if (sitelinks.fi) {
        languages.push(`<a href="${sitelinks.fi.url}" target="_blank" class="suru-link">fi</a>`);
    }
    if (sitelinks.en) {
        languages.push(`<a href="${sitelinks.en.url}" target="_blank" class="suru-link">en</a>`);
    }
    
    if (languages.length > 0) {
        html += languages.join(', ');
    }
    
    // Add other languages count
    if (sitelinks.otherCount > 0) {
        html += ` <span class="suru-other-langs">+${sitelinks.otherCount}</span>`;
    }
    
    return html;
}

// Function to update flask link with selected parameters
function updateFlaskLink(qCode = '', translation = '') {
    const flaskLink = document.getElementById('flask-create-link');
    if (flaskLink) {
        const currentUrl = new URL(flaskLink.href);
        
        // Only set betydelse_objekt if qCode is provided
        if (qCode) {
            currentUrl.searchParams.set('betydelse_objekt', qCode);
        } else {
            currentUrl.searchParams.delete('betydelse_objekt');
        }
        
        // Only set sv_gloss if translation is provided
        if (translation) {
            currentUrl.searchParams.set('sv_gloss', translation);
        } else {
            currentUrl.searchParams.delete('sv_gloss');
        }
        
        flaskLink.href = currentUrl.toString();
        console.log('Updated flask link with qCode:', qCode, 'and translation:', translation);
    }
}

// Main function to initialize the content
async function initWidget() {
    console.log('=== SURU Extension: Initializing content... ===');
    console.log('Current URL:', window.location.href);
    console.log('Document ready state:', document.readyState);
    
    try {
        // Get suru_id from URL
        const urlParams = new URLSearchParams(window.location.search);
        let suruId = urlParams.get('suru_id');
        console.log('Found suru_id:', suruId);

        // Create content container
        const container = createContentContainer();
        console.log('Created container:', container);
        
        // Insert container into the page
        insertContent(container);
        console.log('Inserted container into page');

        let content = '';

        // Handle suru_id results if present
        if (suruId) {
            // Remove 'SURU_' prefix if present
            if (suruId.startsWith('SURU_')) {
                suruId = suruId.substring(5);
                console.log('Removed SURU_ prefix, new suru_id:', suruId);
            }

            // Execute SPARQL query and display results
            console.log('Executing SPARQL query...');
            const results = await executeSparqlQuery(suruId);
            
            if (!results) {
                content += '<div class="suru-error">Error fetching data from Wikidata</div>';
            } else {
                content += await createTable(results);
            }
        }

        // Add translation table
        console.log('Creating translation table...');
        content += await createTranslationTable();

        console.log('Setting container innerHTML...');
        container.innerHTML = content;

        // Add event listeners for copy icons
        const copyIcons = container.querySelectorAll('.suru-copy-icon');
        copyIcons.forEach(icon => {
            icon.addEventListener('click', async (e) => {
                e.preventDefault();
                const qCode = icon.getAttribute('data-qcode');
                if (qCode) {
                    await copyToClipboard(qCode);
                    // Visual feedback
                    icon.textContent = '✓';
                    icon.style.color = 'green';
                    setTimeout(() => {
                        icon.textContent = '📋';
                        icon.style.color = '';
                    }, 1000);
                }
            });
        });

        // Add event listeners for radiobuttons
        const radioButtons = container.querySelectorAll('.suru-radio');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    const qCode = e.target.getAttribute('data-qcode');
                    const translation = e.target.getAttribute('data-translation');
                    updateFlaskLink(qCode, translation);
                }
            });
        });

        // Initialize flask link with empty values
        updateFlaskLink();
        
        console.log('=== SURU Extension: Initialization complete ===');
    } catch (error) {
        console.error('=== SURU Extension: Error in initWidget ===', error);
        // Find the container and update it with error message
        const container = document.querySelector('.suru-content');
        if (container) {
            container.innerHTML = `<div class="suru-error">Error initializing widget: ${error.message}</div>`;
        } else {
            console.error('Could not find .suru-content container to display error');
        }
    }
}

// Initialize when the page is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidget);
} else {
    initWidget();
}