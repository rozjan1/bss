// When served from the container the file is mounted at the web root as /tesco_products.json
const PRODUCTS_JSON = '/tesco_products.json';

let products = [];
let cart = JSON.parse(localStorage.getItem('cart') || '{}');

const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));

async function loadProducts(){
  try{
    const res = await fetch(PRODUCTS_JSON);
    const raw = await res.json();

    // normalize different possible shapes:
    // - an array at the root
    // - { products: [...] }
    // - { data: { products: [...] } }
    if(Array.isArray(raw)){
      products = raw;
    } else if(raw && Array.isArray(raw.products)){
      products = raw.products;
    } else if(raw && raw.data && Array.isArray(raw.data.products)){
      products = raw.data.products;
    } else if(raw && raw.results && Array.isArray(raw.results)){
      products = raw.results;
    } else {
      // attempt to find the first array value in the object
      const firstArray = Object.values(raw).find(v=>Array.isArray(v));
      products = firstArray || [];
    }
  }catch(e){
    console.error('Failed to load products', e);
    products = [];
  }
}

function currency(n){
  return Number(n).toFixed(2);
}

function renderCategories(){
  const cats = [...new Set(products.map(p=>p.category || 'Uncategorized'))];
  const container = $('#categories');
  container.innerHTML = '';
  cats.forEach(c=>{
    const btn = document.createElement('button');
    btn.textContent = c;
    btn.className = 'cat-btn';
    btn.onclick = ()=>{
      $$('#product-grid .card').forEach(card=>{
        card.style.display = (card.dataset.category===c || c==='All') ? '' : 'none';
      });
    };
    container.appendChild(btn);
  });
  // add show all
  const all = document.createElement('button');
  all.textContent = 'All';
  all.onclick = ()=> $$('#product-grid .card').forEach(card=>card.style.display='');
  container.prepend(all);
}

function renderProducts(items){
  const grid = $('#product-grid');
  grid.innerHTML = '';
  if(!items || items.length===0){
    grid.innerHTML = '<div style="padding:24px;color:#666">No products found in the JSON file.</div>';
    return;
  }
  items.forEach(p=>{
    const card = document.createElement('div');
    card.className = 'card';
    card.dataset.sku = p.sku || p.id || '';
    card.dataset.category = p.category || 'Uncategorized';

  const img = document.createElement('img');
  img.src = p.image || p.image_url || p.thumbnail || (p.images && p.images[0]) || 'https://via.placeholder.com/220x140?text=No+Image';
    img.alt = p.title || p.name || 'Product';

    const title = document.createElement('div');
    title.className = 'title';
    title.textContent = p.title || p.name || 'Untitled';

    const meta = document.createElement('div');
    meta.className = 'meta';
  meta.textContent = p.brand ? p.brand : (p.manufacturer || p.supplier || '');

    const price = document.createElement('div');
    price.className = 'price';
  // price fields vary per dataset
  const priceVal = p.price || p.unit_price || p.price_including_tax || p.sale_price || p.price_gross || 0;
  price.textContent = '£' + currency(priceVal);

    const btn = document.createElement('button');
    btn.textContent = 'Add to cart';
    btn.onclick = ()=> addToCart(p);

    card.appendChild(img);
    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(price);
    card.appendChild(btn);
    grid.appendChild(card);
  });
}

function addToCart(p){
  const key = p.sku || p.id || p.ean || p.upc || p.name;
  if(!cart[key]) cart[key] = {...p, qty:0};
  cart[key].qty += 1;
  saveCart();
  updateCartUI();
}

function saveCart(){
  localStorage.setItem('cart', JSON.stringify(cart));
}

function updateCartUI(){
  const count = Object.values(cart).reduce((s,i)=>s + (i.qty||0),0);
  $('#cart-count').textContent = count;
}

function openCart(){
  $('#cart-modal').classList.remove('hidden');
  const container = $('#cart-items');
  container.innerHTML = '';
  let total = 0;
  Object.values(cart).forEach(item=>{
    const div = document.createElement('div');
    div.className = 'cart-item';
    const img = document.createElement('img');
    img.src = item.image || item.image_url || 'https://via.placeholder.com/64';
    const meta = document.createElement('div');
    meta.innerHTML = `<div style="font-weight:600">${item.title||item.name}</div><div>£${currency(item.price||item.unit_price||0)} × ${item.qty}</div>`;
    const controls = document.createElement('div');
    controls.innerHTML = `<button class="qty-minus">-</button><button class="qty-plus">+</button><button class="remove">Remove</button>`;

    controls.querySelector('.qty-minus').onclick = ()=>{ item.qty = Math.max(0,(item.qty||0)-1); if(item.qty===0) delete cart[item.sku||item.id||item.name]; saveCart(); openCart(); updateCartUI(); };
    controls.querySelector('.qty-plus').onclick = ()=>{ item.qty = (item.qty||0)+1; saveCart(); openCart(); updateCartUI(); };
    controls.querySelector('.remove').onclick = ()=>{ delete cart[item.sku||item.id||item.name]; saveCart(); openCart(); updateCartUI(); };

    div.appendChild(img);
    div.appendChild(meta);
    div.appendChild(controls);
    container.appendChild(div);
    total += (Number(item.price||item.unit_price||0) * (item.qty||0));
  });
  $('#cart-total').textContent = currency(total);
}

function closeCart(){
  $('#cart-modal').classList.add('hidden');
}

function setupHandlers(){
  $('#cart-btn').onclick = openCart;
  $('#close-cart').onclick = closeCart;
  $('#search').addEventListener('input', e=>{
    const q = e.target.value.toLowerCase().trim();
    const filtered = products.filter(p=>((p.title||p.name||'').toLowerCase().includes(q) || (p.brand||'').toLowerCase().includes(q)));
    renderProducts(filtered);
  });
  $('#sort').onchange = e=>{
    const val = e.target.value;
    let items = [...products];
    if(val==='price-asc') items.sort((a,b)=>(a.price||a.unit_price||0)-(b.price||b.unit_price||0));
    if(val==='price-desc') items.sort((a,b)=>(b.price||b.unit_price||0)-(a.price||a.unit_price||0));
    renderProducts(items);
  };
  $('#checkout').onclick = ()=> alert('Checkout demo — not implemented');
}

(async function init(){
  await loadProducts();
  renderCategories();
  renderProducts(products);
  setupHandlers();
  updateCartUI();
})();
