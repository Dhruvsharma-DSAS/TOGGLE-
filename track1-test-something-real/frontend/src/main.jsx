import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowUpRight, ArrowRight, BarChart3, Building2, Check, ChevronDown, ChevronRight, CircleHelp, Command, Download, FileText, FlaskConical, GitBranch, Layers3, LayoutDashboard, ListChecks, Network, Search, ShieldCheck, SlidersHorizontal, Upload, X, AlertTriangle, Clock3, Plus } from 'lucide-react';
import './styles.css';

const money = n => new Intl.NumberFormat('en-US', {style:'currency',currency:'USD', maximumFractionDigits:0}).format(n);
const compact = n => n >= 1e6 ? `$${(n/1e6).toFixed(2)}m` : `$${(n/1000).toFixed(1)}k`;
const label = {draft_reminder:'Draft payment reminder', resolve_dispute:'Open dispute review', schedule_followup:'Schedule follow-up'};
const api = async (path, body) => {
  const response = await fetch(`/api/${path}`, body === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  if (!response.ok) { const error = await response.json().catch(()=>({})); throw new Error(typeof error.detail === 'string' ? error.detail : 'Please check the request and try again.'); }
  return response.json();
};
function download(name, text, type='text/csv') {
  const url = URL.createObjectURL(new Blob([text], {type}));
  const anchor = document.createElement('a'); anchor.href=url; anchor.download=name; anchor.click(); setTimeout(()=>URL.revokeObjectURL(url), 1000);
}
const csvCell = value => '"'+String(value).replace(/^[=+@\-\t\r]/,"'$&").replaceAll('"','""')+'"';
function App() {
  const [view,setView] = useState('Overview');
  const [session,setSession] = useState(null);
  const [data,setData] = useState(null);
  const [lab,setLab] = useState(null);
  const [search,setSearch] = useState('');
  const [filter,setFilter] = useState('all');
  const [selected,setSelected] = useState(null);
  const [modal,setModal] = useState(null);
  useEffect(()=>{
    if(!modal)return;
    const previous=document.activeElement;
    const dialog=document.querySelector('[role=dialog]');
    const getFocusable=()=>[...dialog.querySelectorAll('button:not(:disabled),a,input:not([hidden]),select,textarea')];
    getFocusable()[0]?.focus();
    const onKey=e=>{
      if(e.key==='Escape'){setModal(null);return;}
      if(e.key==='Tab'){const elements=getFocusable();const first=elements[0],last=elements.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}
    };
    document.addEventListener('keydown',onKey);
    return()=>{document.removeEventListener('keydown',onKey);previous?.focus();};
  },[modal]);
  const [error,setError] = useState('');
  const [toast,setToast] = useState('');
  const [busy,setBusy] = useState(false);
  const [action,setAction] = useState('draft_reminder');
  const [note,setNote] = useState('');
  const [delay,setDelay] = useState(30);
  const [rate,setRate] = useState(10);
  const [scenarioCustomer,setScenarioCustomer] = useState('Meridian Logistics');
  const exposure = useRef(null);
  const file = useRef(null);
  const credentials = s => ({visitor_id:s.visitor_id, token:s.token});
  async function boot(preview) {
    setError(''); setData(null); setSelected(null); setModal(null);
    try {
      let id = preview ? crypto.randomUUID() : localStorage.getItem('atlas_visitor');
      if (!id) id=crypto.randomUUID();
      localStorage.setItem('atlas_visitor',id);
      const result = await api('session', {visitor_id:id, ...(preview ? {preview_variant:preview} : {})});
      const s={...result, visitor_id:id}; setSession(s);
      const workspace = await api('workspace',credentials(s)); setData(workspace);
    } catch(e) {setError(e.message);}
  }
  useEffect(()=>{boot();},[]);
  useEffect(()=>{
    if(session && data && view !== 'Experiment lab' && exposure.current !== session.visitor_id) {
      exposure.current=session.visitor_id;
      api('exposure',credentials(session)).catch(e=>{exposure.current=null;setError('Exposure could not be saved. '+e.message);});
    }
  },[session,data,view]);
  useEffect(()=>{if(view === 'Experiment lab') api('lab').then(setLab).catch(e=>setError(e.message));},[view]);
  useEffect(()=>{if(toast){const timer=setTimeout(()=>setToast(''),5000);return()=>clearTimeout(timer);}},[toast]);
  const invoices=data?.invoices || [];
  const tasks=data?.tasks || [];
  const total=invoices.reduce((s,r)=>s+r.amount,0);
  const overdue=invoices.filter(r=>r.days_overdue>0);
  const overdueTotal=overdue.reduce((s,r)=>s+r.amount,0);
  const disputes=invoices.filter(r=>r.status==='disputed');
  const disputed=disputes.reduce((s,r)=>s+r.amount,0);
  const customers=[...new Set(invoices.map(r=>r.customer))];
  const concentrations=customers.map(customer=>({customer, amount:invoices.filter(r=>r.customer===customer).reduce((s,r)=>s+r.amount,0)})).sort((a,b)=>b.amount-a.amount);
  const priorities=[...invoices].filter(r=>!r.task_id).sort((a,b)=>b.priority-a.priority);
  const filtered=invoices.filter(r=>(r.customer+' '+r.id).toLowerCase().includes(search.toLowerCase()) && (filter==='all'||(filter==='overdue'&&r.days_overdue>0)||(filter==='disputed'&&r.status==='disputed'))).sort((a,b)=>session?.variant==='decision_brief'?b.priority-a.priority:a.id.localeCompare(b.id));
  const buckets=[['Current', r=>!r.days_overdue,'#91aaa6'],['1–30 days',r=>r.days_overdue>0&&r.days_overdue<=30,'#467d73'],['31–60 days',r=>r.days_overdue>30&&r.days_overdue<=60,'#254f48'],['61+ days',r=>r.days_overdue>60,'#d5a168']].map(([name,test,color])=>({name,amount:invoices.filter(test).reduce((s,r)=>s+r.amount,0),color}));
  const activeCustomer=customers.includes(scenarioCustomer)?scenarioCustomer:customers[0];
  const customerExposure=invoices.filter(r=>r.customer===activeCustomer).reduce((s,r)=>s+r.amount,0);
  const scenarioCost=customerExposure*(rate/100)*delay/365;
  const title={Overview:'Revenue intelligence',Receivables:'Receivables',Relationships:'Business relationships',Scenarios:'Scenario workspace','Action log':'Action log','Experiment lab':'Experiment lab'}[view];
  function openTask(item) {setSelected(item);setAction(item.suggested_action);setNote('');setModal('task');setError('');}
  async function saveTask(e) {
    e.preventDefault();setBusy(true);setError('');
    try {
      await api('tasks',{...credentials(session), invoice_id:selected.id,action,note});
      setData(await api('workspace',credentials(session)));setModal(null);setToast('Action saved to the audit log.');
    } catch(e){setError(e.message);}finally{setBusy(false);}
  }
  async function importFile(e) {
    const upload=e.target.files?.[0]; if(!upload)return;
    setBusy(true);setError('');
    try{
      if(upload.size>200000)throw new Error('Choose a CSV smaller than 200 KB.');
      const result=await api('import',{...credentials(session),csv_text:await upload.text()});
      setData(await api('workspace',credentials(session)));setToast(`Imported ${result.imported} invoices.`);setModal(null);
    }catch(e){setError(e.message);}finally{setBusy(false);e.target.value='';}
  }
  function exportData(){
    const rows=[['invoice_id','customer','amount','currency','due_date','status'],...invoices.map(r=>[r.id,r.customer,r.amount,'USD',r.due_date,r.status])];
    download('atlas-receivables.csv',rows.map(row=>row.map(csvCell).join(',')).join('\n'));setToast('Receivables exported.');
  }
  return <div className="app-shell">
    <a className="skip" href="#main">Skip to content</a>
    <aside className="sidebar">
      <a href="#" className="brand" onClick={e=>{e.preventDefault();setView('Overview');}}><span className="brand-mark"><Layers3 size={23}/></span>ATLAS<span className="brand-dot">®</span></a>
      <div className="workspace"><span className="workspace-icon"><Building2 size={17}/></span><div><strong>{data?.dataset==='imported'?'Imported portfolio':'Meridian Holdings'}</strong><small>{data?.dataset==='imported'?'Your CSV workspace':'Sample organisation'}</small></div></div>
      <div className="nav-label">WORKSPACE</div>
      <nav aria-label="Main navigation">{[[LayoutDashboard,'Overview'],[FileText,'Receivables'],[Network,'Relationships'],[SlidersHorizontal,'Scenarios'],[ListChecks,'Action log']].map(([Icon,name])=><button key={name} className={view===name?'nav-item active':'nav-item'} title={name} onClick={()=>setView(name)}><Icon size={18}/>{name}{name==='Action log'&&tasks.length>0&&<span className="nav-count">{tasks.length}</span>}</button>)}</nav>
      <div className="nav-label second-label">VALIDATION</div><button className={view==='Experiment lab'?'nav-item active':'nav-item'} onClick={()=>setView('Experiment lab')}><FlaskConical size={18}/>Experiment lab<span className="tiny-tag">A/B</span></button>
      <div className="sidebar-bottom"><div className="system-note"><ShieldCheck size={17}/><div>Human decisions.<br/><span>Traceable by design.</span></div></div><button className="profile" onClick={()=>setModal('about')}><span className="avatar">DS</span><span><strong>Dhruv Sharma</strong><small>Workspace owner · local demo</small></span><CircleHelp size={16}/></button></div>
    </aside>
    <div className="main-shell">
      <header className="topbar"><div className="breadcrumb">Workspace<ChevronRight size={14}/><strong>{view}</strong></div><div className="topbar-right"><span className="status-dot"/><span>{session?.mode==='live'?'Flagsmith connected':'Local demo'}</span><span className="top-divider"/><button className="icon-button" aria-label="About this workspace" onClick={()=>setModal('about')}><CircleHelp size={18}/></button><span className="small-avatar">DS</span></div></header>
      <main id="main">
        <div className="page-heading"><div><div className="eyebrow">BUSINESS OPERATIONS INTELLIGENCE</div><h1>{title}<span className="heading-dot">.</span></h1><p>{view==='Overview'?'A clear view of your cash exposure. A deliberate next move.':view==='Experiment lab'?'Measure decisions, not dashboard impressions.':'Connected information. Accountable action.'}</p></div><div className="heading-actions"><button className="button secondary" onClick={exportData} disabled={!data}><Download size={15}/>Export</button><button className="button primary" onClick={()=>{setError('');setModal('import');}} disabled={!data}><Upload size={15}/>Import data</button></div></div>
        {error&&<div role="alert" className="error"><AlertTriangle size={16}/>{error}<button aria-label="Dismiss error" onClick={()=>setError('')}><X size={15}/></button></div>}
        {!data?<div className="loading"><Layers3 size={32}/><h2>{error?'Workspace unavailable':'Preparing your workspace…'}</h2><p>{error?'Start the backend, then try again.':'Connecting the business objects.'}</p>{error&&<button className="button primary" onClick={()=>boot()}>Try again</button>}</div>:<>
          <div className="dataset-strip"><span><span className="status-dot"/>{data.dataset==='sample'?'SAMPLE DATA':'IMPORTED DATA'}<span className="strip-divider">/</span>As of {data.as_of}<span className="strip-divider">/</span>USD</span><span>{session.mode==='demo'?'Preview environment':'Experiment environment'}<span className="strip-divider">/</span>{session.variant==='decision_brief'?'Decision workspace':'Standard workspace'}</span></div>
          {(view==='Overview'||view==='Receivables')&&<>
            <div className="metrics">
              {[["Total receivables",total,`${invoices.length} open invoices`, 'neutral'],['Overdue exposure',overdueTotal,`${overdue.length} invoices past due`, 'warning'],['Disputed balance',disputed,`${disputes.length} invoices need review`, 'warning'],['Customer concentration',concentrations[0]?.amount||0,`${concentrations[0]?.customer||'No customers'} · ${total?Math.round((concentrations[0]?.amount||0)/total*100):0}% of total`,'neutral']].map(([name,value,sub,type],i)=><section className="metric" key={name}><div className="metric-label">{name}{i===0?<BarChart3 size={16}/>:i===1?<Clock3 size={16}/>:i===2?<AlertTriangle size={16}/>:<Building2 size={16}/>}</div><div className="metric-value">{money(value)}</div><div className={`metric-sub ${type}`}><span className="small-dot"/>{sub}</div></section>)}
            </div>
            {session.variant==='decision_brief'&&<section className="decision-brief"><div className="brief-icon"><Command size={22}/></div><div><div className="eyebrow">TODAY’S DECISION BRIEF</div><h2>{priorities.length?`${priorities[0].customer} leads your action queue.`:'Your action queue is clear.'}</h2><p>{priorities.length?`${money(priorities[0].amount)} outstanding · ${priorities[0].days_overdue} days overdue. ${priorities[0].status==='disputed'?'Resolve the dispute before contacting collections.':'Review the invoice and prepare the next action.'}`:'All invoices have a recorded next action. Review the audit log for details.'}</p></div>{priorities.length>0&&<button className="button primary" onClick={()=>openTask(priorities[0])}>Review action<ArrowRight size={15}/></button>}</section>}
            {session.variant==='decision_brief'&&priorities.length>1&&<div className="brief-followups">{priorities.slice(1,3).map((r,i)=><button key={r.id} onClick={()=>openTask(r)}><span className="brief-rank">0{i+2}</span><div><strong>{r.customer}</strong><small>{r.reason}</small></div><span>{label[r.suggested_action]}<ArrowUpRight size={15}/></span></button>)}</div>}{view==='Overview'&&<div className="charts-grid"><section className="panel aging"><div className="panel-heading"><div><h2>Where cash is waiting</h2><p>Receivables by age</p></div><span className="subtle-tag">Contractual balance</span></div><div className="stacked-bar">{buckets.map(b=><div key={b.name} style={{width:`${total?b.amount/total*100:0}%`,background:b.color}} title={`${b.name}: ${money(b.amount)}`}/>)}</div><div className="bucket-grid">{buckets.map(b=><div key={b.name}><span><i style={{background:b.color}}/>{b.name}</span><strong>{money(b.amount)}</strong><small>{total?(b.amount/total*100).toFixed(1):0}% of portfolio</small></div>)}</div><div className="panel-foot"><ShieldCheck size={14}/>Calculated from invoice dates. No predictive model.</div></section>
              <section className="panel concentration"><div className="panel-heading"><div><h2>Customer exposure</h2><p>Know where you’re concentrated</p></div><ArrowUpRight size={17}/></div>{concentrations.slice(0,4).map((c,i)=><button className="concentration-row" key={c.customer} onClick={()=>{setView('Receivables');setSearch(c.customer);}}><span className="rank">0{i+1}</span><div><span>{c.customer}</span><div className="mini-track"><i style={{width:`${total?c.amount/total*100:0}%`}}/></div></div><strong>{compact(c.amount)}</strong></button>)}</section></div>}
            <section className="panel invoice-panel"><div className="panel-heading"><div><h2>{session.variant==='decision_brief'?'Prioritised action queue':'Invoice register'}<span className="count">{invoices.length}</span></h2><p>{session.variant==='decision_brief'?'Ranked by assumed incremental cash per hour. Inspect each reason before acting.':'Review balances, payment dates, and open exceptions.'}</p></div><button className="text-button" onClick={()=>{setView(view==='Overview'?'Receivables':'Overview');setSearch('');setFilter('all');}}>{view==='Overview'?'View all invoices':'Back to overview'}<ArrowRight size={14}/></button></div>
              <div className="table-toolbar"><div className="filter-tabs">{[['all','All invoices'],['overdue','Overdue'],['disputed','Disputed']].map(([value,text])=><button key={value} className={filter===value?'selected':''} onClick={()=>setFilter(value)}>{text}</button>)}</div><label className="search"><Search size={15}/><input placeholder="Search customers or invoices" aria-label="Search invoices" value={search} onChange={e=>setSearch(e.target.value)}/></label></div>
              <div className="table-wrap"><table><thead><tr><th>Customer / invoice</th><th>Outstanding</th><th>Due date</th><th>Status</th><th>Next action</th><th><span className="sr-only">Review</span></th></tr></thead><tbody>{filtered.map((r,i)=><tr key={r.id}><td><div className="customer-cell"><span className={`company-logo logo-${i%4}`}>{r.customer.split(' ').map(x=>x[0]).join('')}</span><div><button className="customer-name" onClick={()=>{setSelected(r);setModal('detail');}}>{r.customer}</button><small>{r.id} · {r.sector}</small></div></div></td><td className="amount">{money(r.amount)}</td><td><span>{new Date(r.due_date+'T00:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric'})}</span><small className={r.days_overdue?'overdue-text':''}>{r.days_overdue?`${r.days_overdue} days overdue`:'Within terms'}</small></td><td><span className={`badge ${r.status==='disputed'?'amber':r.days_overdue?'rose':'green'}`}><i/>{r.status==='disputed'?'Disputed':r.days_overdue?'Overdue':'Current'}</span></td><td>{r.task_id?<span className="task-saved"><Check size={14}/>Task recorded</span>:<span className="action-label">{label[r.suggested_action]}</span>}</td><td><button className="row-arrow" aria-label={`Review ${r.id}`} onClick={()=>openTask(r)} disabled={!!r.task_id}><ArrowUpRight size={17}/></button></td></tr>)}</tbody></table>{!filtered.length&&<div className="empty"><Search size={23}/><p>No invoices match your filters.</p><button className="text-button" onClick={()=>{setSearch('');setFilter('all');}}>Clear filters</button></div>}</div><div className="table-footer"><span>Showing {filtered.length} of {invoices.length} invoices</span><span>Review → approve → record<ShieldCheck size={13}/></span></div></section>
          </>}
          {view==='Relationships'&&<section className="panel relationship-panel"><div className="panel-heading"><div><h2>The business, connected</h2><p>Follow a customer’s exposure through invoices, disputes, and recorded tasks.</p></div><span className="subtle-tag">{customers.length} customers · {invoices.length} invoices</span></div><div className="relationship-grid"><div className="relationship-root"><Layers3 size={26}/><h2>Receivables portfolio</h2><strong>{money(total)}</strong><p>Customer → Invoice → Action</p></div><div className="relationship-branches">{concentrations.map(c=><button key={c.customer} onClick={()=>{setSelected(invoices.find(r=>r.customer===c.customer));setModal('detail');}}><span className="node-dot"/><div><strong>{c.customer}</strong><small>{invoices.filter(r=>r.customer===c.customer).length} linked invoices · {invoices.filter(r=>r.customer===c.customer&&r.status==='disputed').length} disputes</small></div><span>{money(c.amount)}<ChevronRight size={15}/></span></button>)}</div></div><div className="panel-foot"><GitBranch size={15}/>Relationships are derived from this workspace’s imported or sample records.</div></section>}
          {view==='Scenarios'&&<><section className="panel quant-panel"><div className="panel-heading"><div><h2>Illustrative 30-day cash distribution</h2><p>Monte Carlo simulation · {data.quant.runs.toLocaleString()} runs · seed {data.quant.seed} · assumptions, not fitted predictions</p></div><span className="subtle-tag">Synthetic model</span></div><div className="quant-metrics">{[['5th percentile',data.quant.p05],['Median receipts',data.quant.p50],['95th percentile',data.quant.p95],['Median less 5th percentile',data.quant.cash_at_risk]].map(([name,value])=><div key={name}><small>{name}</small><strong>{money(value)}</strong></div>)}</div><div className="panel-foot"><AlertTriangle size={14}/>{data.quant.note} Customer concentration HHI: {data.quant.concentration_hhi} / 10,000.</div></section><div className="scenario-grid"><section className="panel scenario-input"><div className="panel-heading"><div><h2>What if payment arrives later?</h2><p>Funding-cost sensitivity, with explicit assumptions.</p></div></div><label className="field">Customer<select value={customers.includes(scenarioCustomer)?scenarioCustomer:customers[0]} onChange={e=>setScenarioCustomer(e.target.value)}>{customers.map(c=><option key={c}>{c}</option>)}</select></label><label className="field">Additional payment delay <strong>{delay} days</strong><input type="range" min="0" max="90" value={delay} onChange={e=>setDelay(Number(e.target.value))}/></label><label className="field">Assumed annual funding cost <strong>{rate}%</strong><input type="range" min="0" max="30" step="0.5" value={rate} onChange={e=>setRate(Number(e.target.value))}/></label><div className="formula">Outstanding balance × annual rate × delay ÷ 365</div></section><section className="panel scenario-output"><span className="eyebrow">SCENARIO OUTPUT</span><h2>{customers.includes(scenarioCustomer)?scenarioCustomer:customers[0]}</h2><p>Additional funding cost under your assumptions</p><div className="scenario-value">{money(scenarioCost)}</div><div className="scenario-baseline"><span>Outstanding balance<strong>{money(customerExposure)}</strong></span><span>Additional delay<strong>{delay} days</strong></span><span>Annual rate<strong>{rate}%</strong></span></div><div className="scenario-disclaimer"><AlertTriangle size={16}/><p>This is a sensitivity calculation, not a cash-flow forecast or a probability of non-payment. It assumes the entire balance is delayed.</p></div></section></div></>}
          {view==='Action log'&&<section className="panel"><div className="panel-heading"><div><h2>Decisions leave a trail</h2><p>Saved tasks are internal records. They do not send emails or move money.</p></div><button className="button secondary" onClick={()=>download('atlas-action-log.json',JSON.stringify(tasks,null,2),'application/json')}><Download size={15}/>Export audit</button></div>{tasks.length?tasks.map(t=><div className="audit-row" key={t.id}><span className="audit-check"><Check size={18}/></span><div><strong>{label[t.action]}</strong><p>{t.invoice} · {t.note}</p><small>{new Date(t.created*1000).toLocaleString('en-IN',{timeZone:'Asia/Kolkata'})} IST · Workspace owner</small></div><span className="badge green">Recorded</span></div>):<div className="empty"><ListChecks size={36}/><h2>No actions recorded yet</h2><p>Review an invoice and save its next action.</p><button className="button primary" onClick={()=>setView('Receivables')}>Review receivables<ArrowRight size={15}/></button></div>}</section>}
          {view==='Experiment lab'&&<><section className="experiment-intro panel"><div><span className="eyebrow">TRACK 1 · TEST SOMETHING REAL</span><h2>Does clarity lead to a better next action?</h2><p>Test a standard invoice register against a prioritised decision workspace. Same dataset, same tasks, same validation. One measurable question.</p></div><span className="lab-status"><span className="status-dot"/>{session.mode==='demo'?'LOCAL DEMONSTRATION':'LIVE INSTRUMENTATION'}</span></section><div className="lab-grid"><section className="panel"><div className="panel-heading"><h2>The experiment contract</h2><FlaskConical size={18}/></div><dl className="contract"><dt>Hypothesis</dt><dd>A decision brief increases actions on the fixed top-five priority accounts within 10 minutes.</dd><dt>Primary event</dt><dd><code>valid_collection_action</code> · occurrence</dd><dt>Guardrails</dt><dd>Low-priority actions · invalid attempts · mean seconds to first valid action</dd><dt>Assignment</dt><dd><code>collections_workspace</code> · control / decision_brief · 50:50</dd><dt>Decision rule</dt><dd>Use Flagsmith uncertainty, split health, and guardrails before recommending rollout.</dd></dl></section><section className="panel"><div className="panel-heading"><h2>Local event audit</h2><button className="text-button" onClick={()=>api('lab').then(setLab).catch(e=>setError(e.message))}>Refresh<ArrowRight size={14}/></button></div><div className="lab-table"><table><thead><tr><th>Cohort / arm</th><th>Exposed</th><th>Valid actions</th></tr></thead><tbody>{lab?.arms.map(a=><tr key={a.cohort+a.variant}><td>{a.cohort} / {a.variant}</td><td>{a.exposures}</td><td>{a.conversions}</td></tr>)}</tbody></table></div><div className="lab-verdict"><Clock3 size={19}/><div><strong>Keep running</strong><p>No verified statistical verdict loaded. Local counts are not Flagsmith results.</p></div></div><p className="lab-note">{lab?.note} Pending SDK submissions: {lab?.pending_events??'—'}.</p></section></div><section className="panel preview-panel"><div><h2>Preview both experiences</h2><p>Creates a new isolated sample workspace. Forced previews are excluded from experiment counts.</p></div>{session.mode==='demo'?<div className="heading-actions"><button className="button secondary" onClick={()=>{setView('Overview');boot('control');}}>Preview A · Standard</button><button className="button primary" onClick={()=>{setView('Overview');boot('decision_brief');}}>Preview B · Decision<ArrowRight size={15}/></button></div>:<span className="subtle-tag">Previews disabled in live mode</span>}</section></>}
          <footer className="footer"><span><Layers3 size={13}/>ATLAS<span className="footer-separator">/</span>From exposure to accountable action.</span><span>Independent prototype · {data.dataset==='sample'?'Fictional sample business':'Imported workspace'} · v0.1</span></footer>
        </>}
      </main>
    </div>
    {toast&&<div className="toast" role="status"><Check size={17}/>{toast}</div>}
    {modal&&<div className="modal-overlay" onClick={e=>{if(e.target===e.currentTarget&&!busy)setModal(null);}}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><button className="modal-close icon-button" aria-label="Close dialog" onClick={()=>setModal(null)}><X size={20}/></button>
      {modal==='task'&&selected&&<form onSubmit={saveTask}><span className="eyebrow">REVIEW & RECORD</span><h2 id="modal-title">Make the next move.</h2><p>{selected.customer} · {selected.id}</p><div className="detail-summary"><strong>{money(selected.amount)}</strong><span>{selected.days_overdue} days overdue · {selected.status}</span></div><label className="field">Action<select autoFocus value={action} onChange={e=>setAction(e.target.value)}>{Object.entries(label).map(([key,value])=><option value={key} key={key}>{value}</option>)}</select></label><label className="field">Review note<textarea required maxLength={1000} placeholder="Record your reasoning and the planned next step…" value={note} onChange={e=>setNote(e.target.value)}/></label><p className="dialog-note">{selected.status==='disputed'?'This invoice is disputed. Review the dispute before a collection reminder.':'Check the invoice details before approving a task.'} Saving creates an internal task only.</p>{error&&<p className="error" role="alert">{error}</p>}<button className="button primary full-width" type="submit" disabled={busy||!note.trim()}>{busy?'Saving…':'Approve & record task'}<ShieldCheck size={16}/></button></form>}
      {modal==='detail'&&selected&&<><span className="eyebrow">CONNECTED CUSTOMER RECORD</span><h2 id="modal-title">{selected.customer}</h2><p>Linked invoices in this workspace</p><div className="detail-invoices">{invoices.filter(r=>r.customer===selected.customer).map(r=><button key={r.id} onClick={()=>openTask(r)} disabled={!!r.task_id}><span><strong>{r.id}</strong><small>{r.status} · due {r.due_date}</small></span><span>{money(r.amount)}<ArrowUpRight size={17}/></span></button>)}</div><div className="formula">Priority = balance × assumed improvement in 30-day payment chance ÷ effort hours. Assumptions are published in the project docs; this is not an estimated causal effect.</div></>}
      {modal==='import'&&<><span className="eyebrow">CONNECT YOUR DATA</span><h2 id="modal-title">Bring the business into view.</h2><p>Import up to 500 outstanding invoices. A successful import replaces sample invoices in this workspace.</p><div className="import-zone"><Upload size={30}/><strong>Choose an invoice CSV</strong><span>USD only · max 200 KB · open or disputed invoices</span><button className="button primary" onClick={()=>file.current.click()} disabled={busy}>{busy?'Importing…':'Choose file'}<Plus size={15}/></button><input ref={file} type="file" accept=".csv,text/csv" hidden onChange={importFile}/></div><p className="dialog-note">Columns: invoice_id, customer, amount, currency, due_date (YYYY-MM-DD), status. Import before recording tasks. Controlled live experiment sessions use the sample dataset.</p><button className="text-button" onClick={()=>download('atlas-import-template.csv','invoice_id,customer,amount,currency,due_date,status\nINV-001,Example Company,12500.00,USD,2026-11-10,open\n')}>Download CSV template<Download size={14}/></button>{error&&<p role="alert" className="error">{error}</p>}</>}
      {modal==='about'&&<><span className="eyebrow">ABOUT THIS WORKSPACE</span><h2 id="modal-title">Operational clarity.</h2><p>ATLAS connects receivables, customers, disputes, and actions in one working prototype. Sample organisations and balances are fictional.</p><div className="formula">Current scope: invoice analysis, illustrative cash simulations, deterministic scenarios, internal task records, CSV import, and Flagsmith experimentation.</div><p className="dialog-note">This prototype uses anonymous workspace tokens. Company SSO, role-based permissions, tenant administration, and ERP integrations are future production work. Use sample or non-sensitive test data.</p></>}
    </section></div>}
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
