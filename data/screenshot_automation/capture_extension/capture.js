(async()=>{
 const q=new URL(location.href).searchParams, mode=q.get('capture');
 const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 const $=id=>document.getElementById(id);
 const waitFor=async(fn,ms=60000)=>{const end=Date.now()+ms;while(Date.now()<end){if(fn())return true;await sleep(250)}return false};
 const set=(id,value,change=false)=>{const e=$(id);e.value=value;if(change)e.dispatchEvent(new Event('change',{bubbles:true}))};
 const click=(sel)=>document.querySelector(sel)?.click();
 const runTranslate=async(src,target,code)=>{
  set('source',src,true);await sleep(400);set('target',target);set('sourceCode',code);click('button[onclick="translateCode()"]');
  await waitFor(()=>!$('status').textContent.includes('Translating'));
  document.querySelector('.inspector-panel').open=true;
 };
 if(mode==='languages'){
  set('source','Pascal',true);set('target','Python');
  await waitFor(()=>!$('status').textContent.includes('Translating'));window.scrollTo(0,0);
 } else if(mode==='translation'){
  const code=`IDENTIFICATION DIVISION.\nPROGRAM-ID. SCREENSHOT-DEMO.\nDATA DIVISION.\nWORKING-STORAGE SECTION.\n01 A PIC 999 VALUE 10.\n01 B PIC 999 VALUE 20.\nPROCEDURE DIVISION.\nCOMPUTE SUM = A + B.\nDISPLAY SUM.\nSTOP RUN.`;
  await runTranslate('COBOL','JavaScript',code);window.scrollTo(0,0);
 } else if(mode==='success'){
  const code=`10 LET A = 10\n20 LET B = 20\n30 PRINT A + B\n40 IF A < B THEN PRINT "A IS SMALLER"\n50 FOR I = 1 TO 3\n60 PRINT I\n70 NEXT I\n80 END`;
  await runTranslate('BASIC','JavaScript',code);window.scrollTo(0,0);
 } else if(mode==='unsupported'){
  const code=`IDENTIFICATION DIVISION.\nPROGRAM-ID. UNSUPPORTED-DEMO.\nPROCEDURE DIVISION.\nPERFORM 3 TIMES\n DISPLAY "HELLO"\nEND-PERFORM.\nSTOP RUN.`;
  await runTranslate('COBOL','JavaScript',code);window.scrollTo(0,0);
 } else if(mode==='rules'||mode==='benchmark'||mode==='experiment'){
  const tools=document.querySelector('.tools-panel');tools.open=true;
  document.querySelector('.more-actions').open=true;
  if(mode==='rules'){
   click('button[onclick="loadRulesReport()"]');await waitFor(()=>$('rulesReportDetails').textContent.includes('rules'));
   document.querySelectorAll('.card').forEach(c=>{if(c.querySelector('.card-title')?.textContent.includes('rule catalogue'))c.scrollIntoView({block:'start'})});
  } else if(mode==='benchmark'){
   set('target',q.get('target')||'JavaScript');click('button[onclick="runBenchmark()"]');await waitFor(()=>$('benchmarkDetails').textContent.trim().startsWith('{'));
   document.querySelectorAll('.card').forEach(c=>{if(c.querySelector('.card-title')?.textContent.includes('In-project benchmark'))c.scrollIntoView({block:'start'})});
  } else {
   set('target',q.get('target')||'JavaScript');click('button[onclick="runExperiment()"]');await waitFor(()=>$('experimentDetails').textContent.trim().startsWith('{'));
   document.querySelectorAll('.card').forEach(c=>{if(c.querySelector('.card-title')?.textContent.includes('Controlled rule-only'))c.scrollIntoView({block:'start'})});
  }
 } else {window.scrollTo(0,0)}
 document.documentElement.style.scrollBehavior='auto';await sleep(1000);
})();