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
    const selectedCategory = categorySelect.value;
    const selectedBrand = brandSelect.dataset.selectedBrand || brandSelect.value;
    const brands = brandsByCategory[selectedCategory] || [];
    brandSelect.innerHTML = '<option value="">Selecione uma marca</option>';
    brands.forEach((brand) => {
      if(brand.is_active === false) return;
      const option = document.createElement('option');
      option.value = brand.id;
      option.textContent = brand.name;
      if(String(brand.id) === String(selectedBrand)) {
        option.selected = true;
      }
      brandSelect.appendChild(option);
    });
    brandSelect.dataset.selectedBrand = '';
    brandSelect.disabled = brands.length === 0;
  };

  categorySelect.addEventListener('change', () => {
    brandSelect.dataset.selectedBrand = '';
    renderBrands();
  });
  renderBrands();
}

document.querySelectorAll('[data-cep]').forEach(input => {
  input.addEventListener('blur', () => fillAddressByCep(input));
});

hydrateBrandSelect();
