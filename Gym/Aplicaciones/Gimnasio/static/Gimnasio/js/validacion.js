// GYM Admin — Validación cliente (4 tipos) — archivo externo exigido R7
// 1: obligatorio, 2: largo, 3: formato (email/RUT), 4: selección obligatoria. Mensajes junto al campo, bloquea submit.

function showError(input, msg){
  input.style.borderColor='#DC2626';
  input.style.background='#FEE2E2';
  let err = input.parentElement.querySelector('.js-error');
  if(!err){
    err=document.createElement('span');
    err.className='js-error';
    err.style.cssText='color:#DC2626; font-size:12px; font-weight:600; display:block; margin-top:4px';
    input.parentElement.appendChild(err);
  }
  err.textContent=msg;
  err.style.display='block';
}
function clearError(input){
  input.style.borderColor='#E2E8F0';
  input.style.background='white';
  const err=input.parentElement.querySelector('.js-error');
  if(err) err.style.display='none';
}
function isEmail(v){ return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }
function isRut(v){
  const clean=v.replace(/\./g,'').trim();
  return /^\d{7,8}-[\dkK]$/.test(clean);
}

function validateSocioForm(form){
  let ok=true;
  const nombre=form.querySelector('[name="nombre"]');
  const rut=form.querySelector('[name="rut"]');
  const email=form.querySelector('[name="email"]');
  const plan=form.querySelector('[name="plan"]');
  const clase=form.querySelector('[name="clase"]');

  // 1: obligatorio + 2: largo
  if(nombre){
    clearError(nombre);
    if(!nombre.value.trim()){ showError(nombre,'El nombre es obligatorio.'); ok=false; }
    else if(nombre.value.trim().length < 3){ showError(nombre,'El nombre debe tener al menos 3 caracteres.'); ok=false; }
  }
  // 1: obligatorio + 3: formato RUT
  if(rut){
    clearError(rut);
    if(!rut.value.trim()){ showError(rut,'El RUT es obligatorio.'); ok=false; }
    else if(!isRut(rut.value)){ showError(rut,'Formato de RUT no válido. Ej: 12.345.678-9'); ok=false; }
  }
  // 3: formato email
  if(email){
    clearError(email);
    if(!email.value.trim()){ showError(email,'El email es obligatorio.'); ok=false; }
    else if(!isEmail(email.value.trim())){ showError(email,'Formato de correo no válido. Ej: juan@mail.cl'); ok=false; }
  }
  // 4: selección obligatoria plan
  if(plan){
    clearError(plan);
    if(!plan.value){ showError(plan,'Debes seleccionar un plan.'); ok=false; }
  }
  // 4: selección obligatoria clase
  if(clase){
    clearError(clase);
    if(!clase.value){ showError(clase,'Debes seleccionar una clase.'); ok=false; }
  }
  return ok;
}

function validateLoginForm(form){
  let ok=true;
  const user=form.querySelector('[name="username"]');
  const pass=form.querySelector('[name="password"]');
  const rut=form.querySelector('[name="rut"]'); // por si está visible (legacy)
  if(user){
    clearError(user);
    if(!user.value.trim()){ showError(user,'El usuario es obligatorio.'); ok=false; }
    else if(user.value.trim().length < 3){ showError(user,'Mínimo 3 caracteres.'); ok=false; }
  }
  if(pass && pass.offsetParent !== null){
    clearError(pass);
    if(!pass.value.trim()){ showError(pass,'La contraseña es obligatoria.'); ok=false; }
    else if(pass.value.length < 4){ showError(pass,'Mínimo 4 caracteres.'); ok=false; }
  }
  if(rut && rut.offsetParent !== null){
    clearError(rut);
    if(!rut.value.trim()){ showError(rut,'El RUT es obligatorio.'); ok=false; }
    else if(!isRut(rut.value)){ showError(rut,'Formato RUT Ej: 12.345.678-9'); ok=false; }
  }
  return ok;
}

document.addEventListener('DOMContentLoaded', ()=>{
  // Socio / Inscripción / Registro
  document.querySelectorAll('form').forEach(form=>{
    // detectar si es login por hidden tipo, si no, es socio/inscripción
    const tipo=form.querySelector('[name="tipo"]');
    const isLogin = !!tipo || form.querySelector('[name="username"]');
    if(isLogin){
      form.addEventListener('submit', e=>{
        if(!validateLoginForm(form)) e.preventDefault();
      });
    } else if(form.querySelector('[name="nombre"]') || form.querySelector('[name="rut"]')){
      form.addEventListener('submit', e=>{
        if(!validateSocioForm(form)) e.preventDefault();
      });
      // validación en tiempo real
      form.querySelectorAll('input, select').forEach(el=>{
        el.addEventListener('blur', ()=>{ if(el.name) clearError(el); });
      });
    }
  });
});
