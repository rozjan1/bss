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
  pager: document.getElementById('pager')
}

let products = []
let filtered = []
let page = 1
const PAGE_SIZE = 48

function fmtPrice(v){ if(v==null) return '—'; return Number(v).toFixed(2) + ' Kč' }

function parsePrice(raw){
  if(raw == null) return null
  if(typeof raw === 'number') return raw
  // try to extract numeric parts (handles "9,90 Kč" or "9.90" )
  const s = String(raw).replace(/\s|Kč|CZK/gi, '').replace(',', '.').replace(/[^0-9.\-]/g,'')
  const n = parseFloat(s)
  return Number.isFinite(n) ? n : null
}

function normalizeProduct(p){
  // attach a normalized numeric price used for sorting/filtering
  const sale = parsePrice(p.sale_price)
  const orig = parsePrice(p.original_price)
  const fallback = parsePrice(p.price ?? p.original_price)
  p._price = sale ?? orig ?? fallback ?? null

  // Ensure product_url exists if provided by source JSON
  if(!p.product_url){
    // common direct field
    if(p.url) p.product_url = p.url
    else if(p.product_url) p.product_url = p.product_url
    // try typical Tesco derivation if source indicates tesco and nested id exists
    else if((p.source || '').toLowerCase().includes('tesco')){
      try{
        let id = null
        if(p.data && p.data.category && Array.isArray(p.data.category.results) && p.data.category.results[0] && p.data.category.results[0].node && p.data.category.results[0].node.id){
          id = p.data.category.results[0].node.id
        }
        id = id || p.id || p.tpnb || p.baseProductId || (p.sellers && p.sellers.results && p.sellers.results[0] && p.sellers.results[0].id) || null
        if(id) p.product_url = `https://nakup.itesco.cz/groceries/cs-CZ/products/${id}`
      }catch(e){ /* ignore */ }
    }
  }

  return p
}

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
    products = raw.map(normalizeProduct)
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
    
    const price = p._price
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
    return true
  })

  const sort = selectors.sort.value
  if(sort==='price-asc') filtered.sort((a,b)=>( (a._price??Infinity)-(b._price??Infinity) ))
  if(sort==='price-desc') filtered.sort((a,b)=>( (b._price??-Infinity)-(a._price??-Infinity) ))
  if(sort==='name-asc') filtered.sort((a,b)=> (a.item_name||a.name||'').localeCompare(b.item_name||b.name||'') )
  if(sort==='name-desc') filtered.sort((a,b)=> (b.item_name||b.name||'').localeCompare(a.item_name||a.name||'') )
  
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
  // Determine sale vs original prices (numeric)
  const saleVal = parsePrice(p.sale_price ?? p.sale_price)
  const origVal = parsePrice(p.original_price ?? p.original_price)

  // Primary visible price: prefer sale price if present otherwise use normalized price
  const primaryPrice = saleVal != null ? saleVal : p._price
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

// initial load
loadSource(selectors.source.value)

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
    // Handle both object (albert) and potentially other formats if any
    if(typeof p.allergies === 'object' && !Array.isArray(p.allergies)){
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
    for(const [key, val] of Object.entries(p.nutrition)){
      html += `<tr><th>${escapeHtml(key)}</th><td>${escapeHtml(val)}</td></tr>`;
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
