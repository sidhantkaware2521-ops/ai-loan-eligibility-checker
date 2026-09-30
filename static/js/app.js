const $ = (s) => document.querySelector(s);
const money = n => new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(n);

for (const tab of document.querySelectorAll('.tab')) tab.addEventListener('click',()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active-panel'));
  tab.classList.add('active'); $('#'+tab.dataset.target).classList.add('active-panel');
});

$('#loanForm').addEventListener('submit', async e=>{
  e.preventDefault();
  const data=Object.fromEntries(new FormData(e.target).entries());
  for(const k of ['age','income','creditScore','existingEmi','loanAmount']) data[k]=Number(data[k]);
  const box=$('#eligibilityResult'); box.classList.remove('hidden'); box.innerHTML='<div class="result-card"><h3>Analyzing</h3><div class="big">Please wait…</div></div>';
  const r=await fetch('/api/application',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}); const out=await r.json();
  if(!r.ok){box.innerHTML=`<div class="result-card"><h3>Error</h3><div class="big bad">${out.error}</div></div>`;return}
  const x=out.result; const cls=x.status==='Likely Eligible'?'good':x.status==='Review Required'?'warn':'bad';
  box.innerHTML=`<div class="result-card"><h3>Estimated status</h3><div class="big ${cls}">${x.status}</div><p>${x.reasons.length?x.reasons.join(' '):'Your entered profile meets the demo rules used for this educational estimate.'}</p></div><div class="result-card"><h3>Assessment score</h3><div class="big">${x.score}/100</div></div><div class="result-card"><h3>Estimated rate</h3><div class="big">${x.interestRate}%</div></div><div class="result-card"><h3>Estimated amount</h3><div class="big">${money(x.estimatedEligibleAmount)}</div></div>`;
  alert(out.message);
});

$('#creditBtn').addEventListener('click', async()=>{const r=await fetch('/api/credit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({creditScore:Number($('#creditInput').value)})});const x=await r.json();const box=$('#creditResult');box.classList.remove('hidden');box.innerHTML=`<div class="result-card"><h3>Credit band</h3><div class="big">${x.band}</div><p>${x.summary}</p></div><div class="result-card" style="grid-column:span 3"><h3>Practical habits</h3><p>${x.tips.map(t=>'• '+t).join('\n')}</p></div>`});

$('#emiBtn').addEventListener('click', async()=>{const body={principal:Number($('#emiPrincipal').value),rate:Number($('#emiRate').value),months:Number($('#emiMonths').value)};const r=await fetch('/api/emi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const x=await r.json();const box=$('#emiResult');box.classList.remove('hidden');if(x.error){box.innerHTML=`<div class="result-card"><h3>Error</h3><div class="big bad">${x.error}</div></div>`;return}box.innerHTML=`<div class="result-card"><h3>Monthly EMI</h3><div class="big good">${money(x.emi)}</div></div><div class="result-card"><h3>Total payment</h3><div class="big">${money(x.totalPayment)}</div></div><div class="result-card"><h3>Total interest</h3><div class="big">${money(x.totalInterest)}</div></div>`});

$('#tipsBtn').addEventListener('click',async()=>{const body={age:Number($('#tipAge').value),income:Number($('#tipIncome').value),creditScore:Number($('#tipCredit').value),employment:$('#tipEmployment').value,existingEmi:Number($('#tipEmi').value)};const r=await fetch('/api/ai-tips',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const x=await r.json();const box=$('#tipsResult');box.classList.remove('hidden');box.textContent=(x.aiEnabled?'Claude AI guidance:\n\n':'Demo guidance (configure Claude API for AI responses):\n\n')+x.answer});
