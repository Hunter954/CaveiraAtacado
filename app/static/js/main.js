async function fillAddressByCep(cepInput){
  const cep = cepInput.value.replace(/\D/g,'');
  if(cep.length !== 8) return;
  try{
    const res = await fetch(`/api/cep/${cep}`);
    const data = await res.json();
    if(data.error) return;
    const form = cepInput.closest('form');
    const street = form.querySelector('[data-street]');
    const neighborhood = form.querySelector('[data-neighborhood]');
    const city = form.querySelector('[data-city]');
    const state = form.querySelector('[data-state]');
    if(street) street.value = data.logradouro || '';
    if(neighborhood) neighborhood.value = data.bairro || '';
    if(city) city.value = data.localidade || '';
    if(state) state.value = data.uf || '';
  }catch(e){console.error(e)}
}

function hydrateBrandSelect(){
  const categorySelect = document.querySelector('[data-category-select]');
  const brandSelect = document.querySelector('[data-brand-select]');
  const brandsByCategory = window.productBrandsByCategory || {};
  if(!categorySelect || !brandSelect) return;

  const renderBrands = () => {
    const selectedCategory = String(categorySelect.value || '');
    const selectedBrand = String(brandSelect.dataset.selectedBrand || brandSelect.value || '');
    const brands = brandsByCategory[selectedCategory] || [];

    if(!selectedCategory){
      brandSelect.innerHTML = '<option value="">Selecione primeiro uma categoria</option>';
      brandSelect.disabled = true;
      return;
    }

    brandSelect.innerHTML = '<option value="">Sem marca</option>';

    brands.forEach((brand) => {
      const option = document.createElement('option');
      option.value = brand.id;
      option.textContent = brand.is_active === false ? `${brand.name} (inativa)` : brand.name;
      if(String(brand.id) === selectedBrand || brand.selected) {
        option.selected = true;
      }
      brandSelect.appendChild(option);
    });

    if(brands.length === 0){
      brandSelect.innerHTML = '<option value="">Nenhuma marca cadastrada para esta categoria</option>';
    }

    brandSelect.dataset.selectedBrand = '';
    brandSelect.disabled = false;
  };

  categorySelect.addEventListener('change', () => {
    brandSelect.dataset.selectedBrand = '';
    renderBrands();
  });

  renderBrands();
}

function setupFlavorBadges(){
  const input = document.querySelector('[data-flavor-input]');
  const hidden = document.querySelector('[data-flavor-hidden]');
  const list = document.querySelector('[data-flavor-list]');
  if(!input || !hidden || !list) return;

  let flavors = hidden.value
    .split(/\n|,/) 
    .map((item) => item.trim())
    .filter(Boolean);

  const sync = () => {
    const uniqueFlavors = [];
    const seen = new Set();

    flavors.forEach((flavor) => {
      const normalized = flavor.toLocaleLowerCase();
      if(!seen.has(normalized)){
        seen.add(normalized);
        uniqueFlavors.push(flavor);
      }
    });

    flavors = uniqueFlavors;
    hidden.value = flavors.join('\n');
    list.innerHTML = '';

    flavors.forEach((flavor, index) => {
      const badge = document.createElement('button');
      badge.type = 'button';
      badge.className = 'flavor-badge flavor-badge-removable';
      badge.innerHTML = `${flavor}<span aria-hidden="true">×</span>`;
      badge.addEventListener('click', () => {
        flavors.splice(index, 1);
        sync();
      });
      list.appendChild(badge);
    });
  };

  const addFlavors = (value) => {
    const items = value.split(',').map((item) => item.trim()).filter(Boolean);
    if(!items.length) return;
    flavors.push(...items);
    input.value = '';
    sync();
  };

  input.addEventListener('keydown', (event) => {
    if(event.key === 'Enter'){
      event.preventDefault();
      addFlavors(input.value);
    }
  });

  input.addEventListener('blur', () => addFlavors(input.value));
  sync();
}

window.hydrateBrandSelect = hydrateBrandSelect;

document.querySelectorAll('[data-cep]').forEach(input => {
  input.addEventListener('blur', () => fillAddressByCep(input));
});

hydrateBrandSelect();
setupFlavorBadges();
