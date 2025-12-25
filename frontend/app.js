const selectors = {
  source: document.getElementById('sourceSelect'),
  search: document.getElementById('search'),
  sort: document.getElementById('sort'),
  grid: document.getElementById('grid'),
  meta: document.getElementById('meta'),
  category: document.getElementById('categoryFilter'),
  priceMin: document.getElementById('priceMin'),
  priceMax: document.getElementById('priceMax'),
  saleOnly: document.getElementById('saleOnly'),
  applyFilters: document.getElementById('applyFilters'),
  pager: document.getElementById('pager'),
  advancedFiltersBtn: document.getElementById('advancedFiltersBtn')
}

// Advanced filters state
let advancedFilters = {
  excludeAllergens: [],
  requireAllergenFree: [],
  excludeIngredients: [],
  nutritionMin: {},
  nutritionMax: {}
}

let products = []
let filtered = []
let page = 1
const PAGE_SIZE = 48

function fmtPrice(v){ if(v==null) return '—'; return Number(v).toFixed(2) + ' Kč' }

// Product data is now normalized by the Python backend script

async function loadSource(url){
  selectors.meta.textContent = 'Loading products…'
  try{
    let raw = []
    if(url === 'all'){
      // fetch all option values except the 'all' entry and merge results
      const opts = Array.from(selectors.source.options).map(o=>o.value).filter(v=>v && v !== 'all')
      const fetches = await Promise.all(opts.map(u=>fetch(u).then(r=>r.json()).catch(e=>{ console.warn('failed to load',u,e); return [] })))
      raw = fetches.flat()
    } else {
      const res = await fetch(url)
      raw = await res.json()
    }
    // Products are already normalized by backend Python script
    products = raw
    filtered = products.slice()
    populateCategories()
    page = 1
    applyAllFilters() // This will apply current sorting and filters
  }catch(e){ selectors.meta.textContent = 'Failed to load: '+e.message }
}

function populateCategories(){
  const cats = Array.from(new Set(products.map(p=>p.product_category||p.category||'Other'))).filter(Boolean).sort()
  selectors.category.innerHTML = '<option value="">All categories</option>' + cats.map(c=>`<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('')
}

function escapeHtml(s){ return (s+'').replace(/[&<>"']/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c])) }

function removeDiacritics(str) {
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

function applyAllFilters(){
  const q = selectors.search.value.trim().toLowerCase()
  const terms = q.split(/\s+/).filter(Boolean).map(term => removeDiacritics(term))
  const cat = selectors.category.value
  const min = parseFloat(selectors.priceMin.value)
  const max = parseFloat(selectors.priceMax.value)
  const saleOnly = selectors.saleOnly.checked

  filtered = products.filter(p=>{
    if(cat && (p.product_category||p.category||'') !== cat) return false
    
    const price = p.price
    if(price != null) {
      if(!isNaN(min) && min > 0 && price < min) return false
      if(!isNaN(max) && max > 0 && price > max) return false
    }

    if(saleOnly) {
      const isSale = (p.sale_price != null && p.sale_price !== p.original_price) || !!p.sale_requirement
      if(!isSale) return false
    }

    if(terms.length > 0){ 
      const name = removeDiacritics((p.item_name||p.name||p.title||'').toLowerCase())
      if(!terms.every(term => name.includes(term))) return false
    }

    // Advanced filters - Allergens
    if(advancedFilters.excludeAllergens.length > 0 && p.allergies){
      const productAllergens = extractAllergensFromProduct(p)
      const hasExcludedAllergen = advancedFilters.excludeAllergens.some(excluded => 
        productAllergens.some(pa => pa.toLowerCase().includes(excluded.toLowerCase()))
      )
      if(hasExcludedAllergen) return false
    }

    if(advancedFilters.requireAllergenFree.length > 0 && p.allergies){
      const productAllergens = extractAllergensFromProduct(p)
      const hasForbiddenAllergen = advancedFilters.requireAllergenFree.some(required =>
        productAllergens.some(pa => pa.toLowerCase().includes(required.toLowerCase()))
      )
      if(hasForbiddenAllergen) return false
    }

    // Advanced filters - Ingredients
    if(advancedFilters.excludeIngredients.length > 0 && p.ingredients){
      const ingredientsLower = removeDiacritics(p.ingredients.toLowerCase())
      const hasExcludedIngredient = advancedFilters.excludeIngredients.some(excluded =>
        ingredientsLower.includes(removeDiacritics(excluded.toLowerCase()))
      )
      if(hasExcludedIngredient) return false
    }

    // Advanced filters - Nutrition
    if(p.nutrition && Object.keys(advancedFilters.nutritionMin).length > 0){
      for(const [key, minVal] of Object.entries(advancedFilters.nutritionMin)){
        if(minVal !== '' && minVal != null){
          const productVal = parseNutritionValue(p.nutrition[key])
          if(productVal == null || productVal < parseFloat(minVal)) return false
        }
      }
    }

    if(p.nutrition && Object.keys(advancedFilters.nutritionMax).length > 0){
      for(const [key, maxVal] of Object.entries(advancedFilters.nutritionMax)){
        if(maxVal !== '' && maxVal != null){
          const productVal = parseNutritionValue(p.nutrition[key])
          if(productVal == null || productVal > parseFloat(maxVal)) return false
        }
      }
    }

    return true
  })

  const sort = selectors.sort.value
  if(sort==='price-asc') filtered.sort((a,b)=>( (a.price??Infinity)-(b.price??Infinity) ))
  if(sort==='price-desc') filtered.sort((a,b)=>( (b.price??-Infinity)-(a.price??-Infinity) ))
  if(sort==='name-asc') filtered.sort((a,b)=> (a.item_name||a.name||'').localeCompare(b.item_name||b.name||'') )
  if(sort==='name-desc') filtered.sort((a,b)=> (b.item_name||b.name||'').localeCompare(a.item_name||a.name||'') )
  
  // Nutrition-based sorting
  if(sort.startsWith('nutrition-')){
    const parts = sort.split('-')
    const nutrientType = parts[1]
    const direction = parts[2] // 'asc' or 'desc'
    
    // Map nutrient types to normalized and legacy nutrition keys
    const nutrientKeyMap = {
      'protein': ['protein', 'Bílkoviny', 'Bílkoviny (g)', 'Protein'],
      'energy': ['energy_kcal', 'Energetická hodnota kcal', 'Energetická hodnota (kcal)', 'Energy kcal'],
      'fat': ['fat', 'Tuky', 'Tuky (g)', 'Fat'],
      'carbs': ['carbohydrates', 'Sacharidy', 'Sacharidy (g)', 'Carbohydrates'],
      'sugar': ['sugar', 'z toho cukry', 'Z toho cukry', ' z toho cukry (g)', 'Sugar'],
      'salt': ['salt', 'Sůl', 'Sůl (g)', 'Salt']
    }
    
    const possibleKeys = nutrientKeyMap[nutrientType] || []
    
    filtered.sort((a, b) => {
      let valA = null
      let valB = null
      
      // Find the first matching nutrition key for product A
      if(a.nutrition){
        for(const key of possibleKeys){
          if(a.nutrition[key] != null){
            valA = parseNutritionValue(a.nutrition[key])
            break
          }
        }
      }
      
      // Find the first matching nutrition key for product B
      if(b.nutrition){
        for(const key of possibleKeys){
          if(b.nutrition[key] != null){
            valB = parseNutritionValue(b.nutrition[key])
            break
          }
        }
      }
      
      // Products without nutrition data go to the end
      if(valA == null && valB == null) return 0
      if(valA == null) return 1
      if(valB == null) return -1
      
      // Sort by direction
      return direction === 'desc' ? valB - valA : valA - valB
    })
  }
  
  page = 1
  render()
}

function render(){
  selectors.meta.textContent = `Showing ${filtered.length} products — page ${page}`
  selectors.grid.innerHTML = ''
  const start = (page-1)*PAGE_SIZE
  const pageItems = filtered.slice(start, start+PAGE_SIZE)
  for(const p of pageItems){
    const card = document.createElement('div'); card.className='card'
    const img = document.createElement('img'); img.src = p.image_url || p.image || '';
    img.alt = p.item_name || p.name || ''
    img.addEventListener('click', ()=> window.open(img.src, '_blank'))
    const title = document.createElement('div'); title.className='title'
    const nameText = p.item_name || p.name || 'Unnamed'
    if(p.product_url){
      const a = document.createElement('a'); a.href = p.product_url; a.textContent = nameText; a.target = '_blank'; a.rel = 'noopener noreferrer'
      title.appendChild(a)
      // make the whole title clickable (but avoid double-open when clicking the anchor)
      title.style.cursor = 'pointer'
      title.addEventListener('click', (e)=>{
        const tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : ''
        if(tag !== 'a'){
          window.open(p.product_url, '_blank', 'noopener')
        }
      })
    } else {
      title.textContent = nameText
    }
    const source = document.createElement('div'); source.className='source'; source.textContent = p.source || ''; source.style.fontStyle = 'italic'; source.style.fontSize = 'small'; source.style.color = '#666'
    const metaRow = document.createElement('div'); metaRow.className='metaRow'
  // Determine sale vs original prices (already normalized as floats)
  const saleVal = p.sale_price
  const origVal = p.original_price

  // Primary visible price: prefer sale price if present otherwise use normalized price field
  const primaryPrice = saleVal != null ? saleVal : p.price
  const price = document.createElement('div'); price.className='price'; price.textContent = fmtPrice(primaryPrice)

  // If there's an original price different from the primary price, show it as strikethrough
  if(origVal != null && (saleVal == null || origVal !== saleVal) && origVal !== primaryPrice){
    const origPrice = document.createElement('div'); origPrice.className = 'original-price'; origPrice.textContent = fmtPrice(origVal)
    // place original price next to main price
    const priceWrapper = document.createElement('div'); priceWrapper.style.display = 'flex'; priceWrapper.style.alignItems = 'center'
    priceWrapper.appendChild(price);
    priceWrapper.appendChild(origPrice);
    metaRow.appendChild(priceWrapper)
  } else {
    metaRow.appendChild(price)
  }

  // Per-unit pricing: show current ppu and, if available, original ppu as strikethrough
  const ppuText = (p.sale_ppu ?? p.original_ppu ?? '') ? `${p.sale_ppu ?? p.original_ppu} Kč / ${p.unit_code ?? ''}` : ''
  const ppu = document.createElement('div'); ppu.className='ppu'; ppu.textContent = ppuText
  if((p.original_ppu != null) && (p.sale_ppu == null || p.original_ppu !== p.sale_ppu)){
    const origPpuText = p.original_ppu ? `${p.original_ppu} Kč / ${p.unit_code ?? ''}` : ''
    if(origPpuText){
      const origPpu = document.createElement('div'); origPpu.className = 'original-ppu'; origPpu.textContent = origPpuText
      const ppuWrapper = document.createElement('div'); ppuWrapper.style.display = 'flex'; ppuWrapper.style.flexDirection = 'column'; ppuWrapper.appendChild(ppu); ppuWrapper.appendChild(origPpu)
      metaRow.appendChild(ppuWrapper)
    } else {
      metaRow.appendChild(ppu)
    }
  } else {
    metaRow.appendChild(ppu)
  }
    const cat = document.createElement('div'); cat.className='ppu'; cat.textContent = p.product_category || ''
    const badge = document.createElement('div'); if(p.sale_requirement){ badge.className='badge'; badge.textContent = p.sale_requirement }
    
    const detailBtn = document.createElement('button');
    detailBtn.className = 'detail-btn';
    detailBtn.textContent = 'Informace';
    detailBtn.onclick = (e) => { e.stopPropagation(); showDetails(p); };

    card.appendChild(img); card.appendChild(title); card.appendChild(source); card.appendChild(metaRow); card.appendChild(cat); 
    if(p.sale_requirement) card.appendChild(badge)
    card.appendChild(detailBtn)
    selectors.grid.appendChild(card)
  }
  renderPager()
}

function renderPager(){
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  selectors.pager.innerHTML = ''
  if(totalPages<=1) return
  const prev = document.createElement('button'); prev.textContent='◀ Prev'; prev.disabled = page<=1; prev.onclick=()=>{ page--; render() }
  const next = document.createElement('button'); next.textContent='Next ▶'; next.disabled = page>=totalPages; next.onclick=()=>{ page++; render() }
  selectors.pager.appendChild(prev)
  const info = document.createElement('span'); info.style.margin='0 12px'; info.textContent = `${page} / ${totalPages}`
  selectors.pager.appendChild(info)
  selectors.pager.appendChild(next)
}

selectors.source.addEventListener('change', e=> loadSource(e.target.value))
selectors.search.addEventListener('input', ()=>{ page=1; applyAllFilters() })
selectors.sort.addEventListener('change', applyAllFilters)
selectors.applyFilters.addEventListener('click', applyAllFilters)
selectors.priceMin.addEventListener('input', applyAllFilters)
selectors.saleOnly.addEventListener('change', applyAllFilters)

// Advanced filters button
selectors.advancedFiltersBtn.addEventListener('click', () => {
  setupAdvancedFiltersModal()
  document.getElementById('advancedFiltersModal').style.display = 'block'
})

// initial load
loadSource(selectors.source.value)

function extractAllergensFromProduct(p){
  const allergens = []
  if(!p.allergies) return allergens
  
  // Handle normalized format
  if(typeof p.allergies === 'object' && !Array.isArray(p.allergies)){
    // Check for normalized format
    if('contains' in p.allergies && Array.isArray(p.allergies.contains)){
      allergens.push(...p.allergies.contains)
    }
    if('may_contain' in p.allergies && Array.isArray(p.allergies.may_contain)){
      allergens.push(...p.allergies.may_contain)
    }
    
    // Also support old format (for backwards compatibility)
    for(const [type, items] of Object.entries(p.allergies)){
      if(type !== 'Neobsahuje' && type !== 'free_from' && Array.isArray(items)){
        allergens.push(...items)
      }
    }
  } else if(Array.isArray(p.allergies)){
    allergens.push(...p.allergies)
  }
  return [...new Set(allergens)]  // Remove duplicates
}

function parseNutritionValue(val){
  if(val == null) return null
  
  // Handle normalized format: {value: 7.0, unit: "g"}
  if(typeof val === 'object' && val.value !== undefined){
    return typeof val.value === 'number' ? val.value : parseFloat(val.value)
  }
  
  // Handle numeric values
  if(typeof val === 'number') return val
  
  // Handle string values (backwards compatibility)
  // Extract numeric value from strings like "1,5 g" or "326 kJ"
  const s = String(val).replace(/\s/g, '').replace(',', '.')
  const match = s.match(/[\d.]+/)
  return match ? parseFloat(match[0]) : null
}

function getAllUniqueAllergens(){
  const allergenSet = new Set()
  products.forEach(p => {
    extractAllergensFromProduct(p).forEach(a => allergenSet.add(a))
  })
  return Array.from(allergenSet).sort()
}

function getAllNutritionKeys(){
  const keySet = new Set()
  products.forEach(p => {
    if(p.nutrition && typeof p.nutrition === 'object'){
      Object.keys(p.nutrition).forEach(k => {
        // Skip metadata fields
        if(k !== 'Výživové údaje na' && k !== 'per_serving'){
          keySet.add(k)
        }
      })
    }
  })
  return Array.from(keySet).sort()
}

function setupModal(){
  if(document.getElementById('detailModal')) return;
  const modalHtml = `
    <div id="detailModal" class="modal">
      <div class="modal-content">
        <span class="close">&times;</span>
        <h2 id="modalTitle" style="margin-top:0; padding-right:20px;"></h2>
        <div id="modalBody"></div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', modalHtml);
  
  const modal = document.getElementById('detailModal');
  const span = document.getElementsByClassName("close")[0];
  
  span.onclick = function() { modal.style.display = "none"; }
  window.onclick = function(event) {
    if (event.target == modal) { modal.style.display = "none"; }
  }
}

function setupAdvancedFiltersModal(){
  if(document.getElementById('advancedFiltersModal')) return;
  
  const modalHtml = `
    <div id="advancedFiltersModal" class="modal">
      <div class="modal-content" style="max-width: 800px; max-height: 85vh; overflow-y: auto;">
        <span class="close-advanced">&times;</span>
        <h2 style="margin-top:0; padding-right:20px;">Advanced Filters</h2>
        <div id="advancedFiltersBody">
          
          <div class="detail-section">
            <h3>Exclude Products With Allergens</h3>
            <div id="excludeAllergensContainer" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;"></div>
            <input id="customAllergenExclude" type="text" placeholder="Add custom allergen to exclude..." 
                   style="width: 100%; margin-top: 8px; padding: 8px; border-radius: 8px; border: 1px solid #dfe6f2;" />
          </div>

          <div class="detail-section">
            <h3>Must Be Free Of (Strict)</h3>
            <div id="requireAllergenFreeContainer" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;"></div>
            <input id="customAllergenRequired" type="text" placeholder="Add custom allergen requirement..." 
                   style="width: 100%; margin-top: 8px; padding: 8px; border-radius: 8px; border: 1px solid #dfe6f2;" />
          </div>

          <div class="detail-section">
            <h3>Exclude Ingredients</h3>
            <div id="excludeIngredientsDisplay" style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 8px;"></div>
            <input id="excludeIngredientsInput" type="text" placeholder="Type ingredient to exclude (e.g., 'palm oil', 'sugar')..." 
                   style="width: 100%; margin-top: 8px; padding: 8px; border-radius: 8px; border: 1px solid #dfe6f2;" />
          </div>

          <div class="detail-section">
            <h3>Nutrition Filters</h3>
            <div id="nutritionFiltersContainer"></div>
          </div>

          <div style="display: flex; gap: 12px; margin-top: 20px;">
            <button id="applyAdvancedFilters" style="flex: 1; padding: 10px; background: var(--accent); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
              Apply Filters
            </button>
            <button id="clearAdvancedFilters" style="flex: 1; padding: 10px; background: #e5e7eb; color: #374151; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
              Clear All
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', modalHtml);
  
  const modal = document.getElementById('advancedFiltersModal');
  const span = document.getElementsByClassName("close-advanced")[0];
  
  span.onclick = function() { modal.style.display = "none"; }
  
  // Populate allergens checkboxes
  populateAllergenOptions()
  
  // Populate nutrition filters
  populateNutritionFilters()
  
  // Add ingredient exclusion
  setupIngredientExclusion()
  
  // Apply button
  document.getElementById('applyAdvancedFilters').onclick = function(){
    applyAdvancedFiltersFromModal()
    modal.style.display = "none"
    applyAllFilters()
  }
  
  // Clear button
  document.getElementById('clearAdvancedFilters').onclick = function(){
    advancedFilters = {
      excludeAllergens: [],
      requireAllergenFree: [],
      excludeIngredients: [],
      nutritionMin: {},
      nutritionMax: {}
    }
    populateAllergenOptions()
    populateNutritionFilters()
    document.getElementById('excludeIngredientsDisplay').innerHTML = ''
    updateAdvancedFilterBadge()
    applyAllFilters()
  }
}

function populateAllergenOptions(){
  const allergens = getAllUniqueAllergens()
  const excludeContainer = document.getElementById('excludeAllergensContainer')
  const requireContainer = document.getElementById('requireAllergenFreeContainer')
  
  excludeContainer.innerHTML = ''
  requireContainer.innerHTML = ''
  
  allergens.forEach(allergen => {
    // Exclude checkbox
    const excludeLabel = document.createElement('label')
    excludeLabel.style.cssText = 'display: flex; align-items: center; gap: 4px; padding: 4px 8px; background: #f3f4f6; border-radius: 6px; font-size: 13px; cursor: pointer;'
    const excludeCheck = document.createElement('input')
    excludeCheck.type = 'checkbox'
    excludeCheck.value = allergen
    excludeCheck.checked = advancedFilters.excludeAllergens.includes(allergen)
    excludeLabel.appendChild(excludeCheck)
    excludeLabel.appendChild(document.createTextNode(allergen))
    excludeContainer.appendChild(excludeLabel)
    
    // Required free checkbox
    const requireLabel = document.createElement('label')
    requireLabel.style.cssText = 'display: flex; align-items: center; gap: 4px; padding: 4px 8px; background: #fef3c7; border-radius: 6px; font-size: 13px; cursor: pointer;'
    const requireCheck = document.createElement('input')
    requireCheck.type = 'checkbox'
    requireCheck.value = allergen
    requireCheck.checked = advancedFilters.requireAllergenFree.includes(allergen)
    requireLabel.appendChild(requireCheck)
    requireLabel.appendChild(document.createTextNode(allergen))
    requireContainer.appendChild(requireLabel)
  })
  
  // Custom allergen inputs
  document.getElementById('customAllergenExclude').addEventListener('keydown', e => {
    if(e.key === 'Enter' && e.target.value.trim()){
      const val = e.target.value.trim()
      if(!advancedFilters.excludeAllergens.includes(val)){
        advancedFilters.excludeAllergens.push(val)
        populateAllergenOptions()
      }
      e.target.value = ''
    }
  })
  
  document.getElementById('customAllergenRequired').addEventListener('keydown', e => {
    if(e.key === 'Enter' && e.target.value.trim()){
      const val = e.target.value.trim()
      if(!advancedFilters.requireAllergenFree.includes(val)){
        advancedFilters.requireAllergenFree.push(val)
        populateAllergenOptions()
      }
      e.target.value = ''
    }
  })
}

function populateNutritionFilters(){
  const nutritionKeys = getAllNutritionKeys()
  const container = document.getElementById('nutritionFiltersContainer')
  container.innerHTML = ''
  
  nutritionKeys.forEach(key => {
    const row = document.createElement('div')
    row.style.cssText = 'display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 13px;'
    
    const label = document.createElement('span')
    label.textContent = key
    label.style.cssText = 'flex: 1; min-width: 150px;'
    
    const minInput = document.createElement('input')
    minInput.type = 'number'
    minInput.placeholder = 'Min'
    minInput.step = 'any'
    minInput.value = advancedFilters.nutritionMin[key] || ''
    minInput.style.cssText = 'width: 80px; padding: 6px; border-radius: 6px; border: 1px solid #dfe6f2;'
    minInput.dataset.key = key
    minInput.dataset.type = 'min'
    
    const maxInput = document.createElement('input')
    maxInput.type = 'number'
    maxInput.placeholder = 'Max'
    maxInput.step = 'any'
    maxInput.value = advancedFilters.nutritionMax[key] || ''
    maxInput.style.cssText = 'width: 80px; padding: 6px; border-radius: 6px; border: 1px solid #dfe6f2;'
    maxInput.dataset.key = key
    maxInput.dataset.type = 'max'
    
    row.appendChild(label)
    row.appendChild(minInput)
    row.appendChild(document.createTextNode(' – '))
    row.appendChild(maxInput)
    container.appendChild(row)
  })
}

function setupIngredientExclusion(){
  const input = document.getElementById('excludeIngredientsInput')
  const display = document.getElementById('excludeIngredientsDisplay')
  
  const renderTags = () => {
    display.innerHTML = ''
    advancedFilters.excludeIngredients.forEach(ingredient => {
      const tag = document.createElement('span')
      tag.style.cssText = 'display: inline-flex; align-items: center; gap: 6px; background: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 12px; font-size: 12px;'
      tag.textContent = ingredient
      
      const removeBtn = document.createElement('span')
      removeBtn.textContent = '×'
      removeBtn.style.cssText = 'cursor: pointer; font-weight: bold; font-size: 16px;'
      removeBtn.onclick = () => {
        advancedFilters.excludeIngredients = advancedFilters.excludeIngredients.filter(i => i !== ingredient)
        renderTags()
      }
      
      tag.appendChild(removeBtn)
      display.appendChild(tag)
    })
  }
  
  input.addEventListener('keydown', e => {
    if(e.key === 'Enter' && e.target.value.trim()){
      const val = e.target.value.trim()
      if(!advancedFilters.excludeIngredients.includes(val)){
        advancedFilters.excludeIngredients.push(val)
        renderTags()
      }
      e.target.value = ''
    }
  })
  
  renderTags()
}

function updateAdvancedFilterBadge(){
  const badge = document.getElementById('advancedFilterBadge')
  if(!badge) return
  
  let count = 0
  count += advancedFilters.excludeAllergens.length
  count += advancedFilters.requireAllergenFree.length
  count += advancedFilters.excludeIngredients.length
  count += Object.keys(advancedFilters.nutritionMin).length
  count += Object.keys(advancedFilters.nutritionMax).length
  
  if(count > 0){
    badge.textContent = `(${count})`
    badge.style.display = 'inline'
    badge.style.cssText = 'display: inline; background: #ef4444; color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px; margin-left: 4px; font-weight: bold;'
  } else {
    badge.style.display = 'none'
  }
}

function applyAdvancedFiltersFromModal(){
  // Collect allergen exclusions
  advancedFilters.excludeAllergens = Array.from(
    document.querySelectorAll('#excludeAllergensContainer input[type="checkbox"]:checked')
  ).map(el => el.value)
  
  // Collect required allergen-free
  advancedFilters.requireAllergenFree = Array.from(
    document.querySelectorAll('#requireAllergenFreeContainer input[type="checkbox"]:checked')
  ).map(el => el.value)
  
  // Collect nutrition filters
  advancedFilters.nutritionMin = {}
  advancedFilters.nutritionMax = {}
  
  document.querySelectorAll('#nutritionFiltersContainer input[data-type="min"]').forEach(input => {
    if(input.value) advancedFilters.nutritionMin[input.dataset.key] = input.value
  })
  
  document.querySelectorAll('#nutritionFiltersContainer input[data-type="max"]').forEach(input => {
    if(input.value) advancedFilters.nutritionMax[input.dataset.key] = input.value
  })
  
  updateAdvancedFilterBadge()
}

function showDetails(p){
  const modal = document.getElementById('detailModal');
  const title = document.getElementById('modalTitle');
  const body = document.getElementById('modalBody');
  
  title.textContent = p.item_name || p.name || 'Product Details';
  body.innerHTML = '';

  // Allergies
  if(p.allergies){
    const div = document.createElement('div'); div.className = 'detail-section';
    let html = `<h3>Alergie</h3><div class="detail-text">`;
    
    let hasAllergyInfo = false;
    
    // Handle normalized format
    if(typeof p.allergies === 'object' && !Array.isArray(p.allergies)){
      // Check for normalized format
      if('contains' in p.allergies || 'may_contain' in p.allergies || 'free_from' in p.allergies){
        if(p.allergies.contains && p.allergies.contains.length > 0){
          hasAllergyInfo = true;
          html += `<div style="margin-bottom:4px"><strong>Obsahuje:</strong> `;
          p.allergies.contains.forEach(item => {
            html += `<span class="allergy-tag">${escapeHtml(item)}</span>`;
          });
          html += `</div>`;
        }
        
        if(p.allergies.may_contain && p.allergies.may_contain.length > 0){
          hasAllergyInfo = true;
          html += `<div style="margin-bottom:4px"><strong>Může obsahovat:</strong> `;
          p.allergies.may_contain.forEach(item => {
            html += `<span class="allergy-tag trace">${escapeHtml(item)}</span>`;
          });
          html += `</div>`;
        }
        
        if(p.allergies.free_from && p.allergies.free_from.length > 0){
          hasAllergyInfo = true;
          html += `<div style="margin-bottom:4px"><strong>Neobsahuje:</strong> `;
          p.allergies.free_from.forEach(item => {
            html += `<span class="allergy-tag safe">${escapeHtml(item)}</span>`;
          });
          html += `</div>`;
        }
      } else {
        // Handle old format (backwards compatibility)
        for(const [type, items] of Object.entries(p.allergies)){
          if(Array.isArray(items) && items.length > 0){
            hasAllergyInfo = true;
            html += `<div style="margin-bottom:4px"><strong>${escapeHtml(type)}:</strong> `;
            items.forEach(item => {
              const cls = type === 'Neobsahuje' ? 'safe' : (type === 'Může obsahovat' ? 'trace' : '');
              html += `<span class="allergy-tag ${cls}">${escapeHtml(item)}</span>`;
            });
            html += `</div>`;
          }
        }
      }
    } else if (Array.isArray(p.allergies)) {
       // Fallback if allergies is just a list of strings
       hasAllergyInfo = true;
       p.allergies.forEach(item => {
          html += `<span class="allergy-tag">${escapeHtml(item)}</span>`;
       });
    }
    
    if(!hasAllergyInfo) html += 'No allergy information provided.';
    html += `</div>`;
    div.innerHTML = html;
    body.appendChild(div);
  }

  // Nutrition
  if(p.nutrition && typeof p.nutrition === 'object' && Object.keys(p.nutrition).length > 0){
    const div = document.createElement('div'); div.className = 'detail-section';
    let html = `<h3>Výživové hodnoty</h3><table class="nutrition-table">`;
    
    // Handle per_serving info if present
    if(p.nutrition.per_serving){
      html += `<tr><th colspan="2" style="text-align:left; font-style:italic;">Výživové údaje na: ${escapeHtml(p.nutrition.per_serving)}</th></tr>`;
    }
    
    // Map normalized keys to readable names
    const nutrientNames = {
      'energy_kj': 'Energetická hodnota',
      'energy_kcal': 'Energetická hodnota',
      'protein': 'Bílkoviny',
      'fat': 'Tuky',
      'saturated_fat': 'Z toho nasycené mastné kyseliny',
      'carbohydrates': 'Sacharidy',
      'sugar': 'Z toho cukry',
      'fiber': 'Vláknina',
      'salt': 'Sůl',
      'sodium': 'Sodík'
    };
    
    for(const [key, val] of Object.entries(p.nutrition)){
      if(key === 'per_serving') continue;
      
      let displayValue;
      if(typeof val === 'object' && val.value !== undefined){
        // Normalized format: {value: 7.0, unit: "g"}
        displayValue = `${val.value} ${val.unit || ''}`;
      } else {
        // Legacy format or string
        displayValue = escapeHtml(val);
      }
      
      const displayName = nutrientNames[key] || key;
      html += `<tr><th>${escapeHtml(displayName)}</th><td>${displayValue}</td></tr>`;
    }
    html += `</table>`;
    div.innerHTML = html;
    body.appendChild(div);
  }

  // Ingredients
  if(p.ingredients){
    const div = document.createElement('div'); div.className = 'detail-section';
    div.innerHTML = `<h3>Složení</h3><div class="detail-text">${escapeHtml(p.ingredients)}</div>`;
    body.appendChild(div);
  }

  if(!p.ingredients && (!p.allergies || Object.keys(p.allergies).length === 0) && !p.nutrition){
    body.innerHTML = '<p>Podrobné informace o tomto produktu nejsou k dispozici.</p>';
  }

  modal.style.display = "block";
}

setupModal();
