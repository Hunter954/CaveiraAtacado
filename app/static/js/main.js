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

    brandSelect.innerHTML = '<option value="">Selecione uma marca</option>';
    const activeBrands = brands.filter((brand) => brand.is_active !== false);

    activeBrands.forEach((brand) => {
      const option = document.createElement('option');
      option.value = brand.id;
      option.textContent = brand.name;
      if(String(brand.id) === selectedBrand) {
        option.selected = true;
      }
      brandSelect.appendChild(option);
    });

    if(activeBrands.length === 0){
      brandSelect.innerHTML = '<option value="">Nenhuma marca cadastrada para esta categoria</option>';
    }

    brandSelect.dataset.selectedBrand = '';
    brandSelect.disabled = activeBrands.length === 0;
  };

  categorySelect.removeEventListener?.('change', renderBrands);
  categorySelect.addEventListener('change', () => {
    brandSelect.dataset.selectedBrand = '';
    renderBrands();
  });

  renderBrands();
}

window.hydrateBrandSelect = hydrateBrandSelect;

document.querySelectorAll('[data-cep]').forEach(input => {
  input.addEventListener('blur', () => fillAddressByCep(input));
});

hydrateBrandSelect();
