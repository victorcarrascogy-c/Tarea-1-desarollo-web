function navigate(view){
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  const el = document.getElementById('view-'+view);
  if(el) el.classList.add('active');
  document.querySelectorAll('#nav a').forEach(a=>{
    a.classList.toggle('active', a.dataset.view===view);
    if(a.dataset.view===view) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current');
  });
  window.scrollTo({top:0, behavior:'smooth'});
}
document.querySelectorAll('#nav a').forEach(a=>{
  a.addEventListener('click', e=>{
    e.preventDefault();
    navigate(a.dataset.view);
  });
});

// Today
const todayEl = document.getElementById('today');
if(todayEl){
  const d = new Date();
  todayEl.textContent = d.toLocaleDateString('es-CL', {weekday:'long', day:'numeric', month:'long', year:'numeric'});
}

// Filters Socios
function filtrarSocios(){
  const plan = document.getElementById('filtro-plan').value.toLowerCase();
  const q = document.getElementById('busca-socio').value.toLowerCase();
  const rows = document.querySelectorAll('#tabla-socios tbody tr');
  let visibles=0;
  rows.forEach(r=>{
    const matchPlan = plan==='todos' || r.dataset.plan.toLowerCase()===plan;
    const matchQ = !q || r.dataset.nombre.includes(q) || r.dataset.rut.includes(q);
    const show = matchPlan && matchQ;
    r.style.display = show ? '' : 'none';
    if(show) visibles++;
  });
  document.getElementById('empty-socios').style.display = visibles===0 ? 'block' : 'none';
  document.querySelector('#tabla-socios').style.display = visibles===0 ? 'none' : '';
}

// Filters Inscripciones
function filtrarIns(){
  const estado = document.getElementById('f-estado').value;
  const clase = document.getElementById('f-clase').value;
  document.querySelectorAll('#tabla-ins tbody tr').forEach(r=>{
    const okEstado = estado==='todos' || r.dataset.estado===estado;
    const okClase = clase==='todos' || r.dataset.clase===clase;
    r.style.display = (okEstado && okClase) ? '' : 'none';
  });
}

// Modals
function openModal(id){ document.getElementById(id).classList.add('open'); }
function closeModal(id){ document.getElementById(id).classList.remove('open'); }

// Validations
function validarRut(el){
  const err = document.getElementById('err-rut');
  const dupes = ['12.345.678-9','16.222.333-4'];
  const isDup = dupes.includes(el.value.trim());
  const badFormat = el.value && !el.value.includes('-');
  if(isDup || badFormat){
    el.classList.add('error'); err.classList.add('show');
  } else {
    el.classList.remove('error'); err.classList.remove('show');
  }
}
function guardarSocio(){
  const rutEl = document.getElementById('inp-rut');
  if(document.getElementById('err-rut').classList.contains('show')){
    toast('Corrige el RUT antes de guardar');
    rutEl.focus(); return;
  }
  const nombre = document.getElementById('inp-nombre').value.trim();
  if(!nombre || !rutEl.value.trim()){ toast('Completa nombre y RUT'); return; }
  toast('Socio guardado ✓');
  closeModal('modal-socio');
}
function checkCapacidad(sel){
  const err = document.getElementById('err-capacidad');
  if(sel.value==='Pesas'){ err.classList.add('show'); sel.style.borderColor='#DC2626'; } else { err.classList.remove('show'); sel.style.borderColor='#E2E8F0'; }
}

// Toast
let toastTimer;
function toast(msg){
  const t=document.getElementById('toast');
  t.textContent=msg; t.style.display='block';
  clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>t.style.display='none',2200);
}

// Logout custom event
window.addEventListener('gym-admin:logout', ()=>toast('Sesión cerrada'));
