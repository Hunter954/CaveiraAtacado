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

document.querySelectorAll('[data-cep]').forEach(input => {
  input.addEventListener('blur', () => fillAddressByCep(input));
});
