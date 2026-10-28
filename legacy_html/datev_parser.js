// DATEV payslip parser: input = array of pages, each = array of {str,x,y,w}
(function(root){
const DE_PAGE = /Abrechnung der Brutto\/Netto-Bez/;
const EN_PAGE = /Pay Advice/;
const MONTHS = {januar:1,februar:2,'märz':3,maerz:3,april:4,mai:5,juni:6,juli:7,august:8,september:9,oktober:10,november:11,dezember:12,
 january:1,february:2,march:3,may:5,june:6,july:7,october:10,december:12};
const L = {
 de:{taxGross:'Steuer-Brutto',wageTax:'Lohnsteuer',church:'Kirchensteuer',soli:'Solidaritätszuschlag',
   kvB:'KV-Brutto',rvB:'RV-Brutto',avB:'AV-Brutto',pvB:'PV-Brutto',kv:'KV-Beitrag',rv:'RV-Beitrag',av:'AV-Beitrag',pv:'PV-Beitrag',
   totalGross:'Gesamt-Brutto',taxTot:'Steuerrechtliche Abzüge',svTot:'SV-rechtliche Abzüge',netInc:'Netto-Verdienst',payout:'Auszahlungsbetrag',
   agSv:'SV-AG-Anteil',agAdd:'Zus. AG-Kosten',agTot:'Gesamtkosten',payHead:'Lohnart',netHead:'Netto-Bezüge/Netto-Abzüge',
   ytd:{'Gesamt-Brutto':'gross','Steuer-Brutto':'taxGross','Lohnsteuer':'wageTax','Kirchensteuer':'church','Solidaritätszuschlag':'soli','Steuerfreie Bezüge':'taxFree',
        'SV-Brutto':'svGross','KV-Beitrag':'kv','RV-Beitrag':'rv','AV-Beitrag':'av','PV-Beitrag':'pv'}},
 en:{taxGross:'Taxable gross income',wageTax:'Wage tax',church:'Church tax',soli:'Solidarity surcharge',
   kvB:'Contr.income(HI)',rvB:'Contr.income(PI)',avB:'Contr.income(UI)',pvB:'Contr.income(CI)',kv:'HI Contribution',rv:'PI Contribution',av:'UI Contribution',pv:'CI Contribution',
   totalGross:'Total gross income',taxTot:'Tax deductions',svTot:'Soc. sec. deductions',netInc:'Net income',payout:'Net pay',
   agSv:'Emp.soc.sec.contr.',agAdd:'Empl. cost, add.',agTot:'Total cost',payHead:'Wag. code',netHead:'Non-taxable/non-contributory payments and deductions',
   ytd:{'Total gross income':'gross','Tax. gross income':'taxGross','Wage tax':'wageTax','Church tax':'church','Solidarity surcharge':'soli','Non-tax. payments':'taxFree',
        'Contr. inc. (Soc.sec.)':'svGross','HI Contribution':'kv','PI Contribution':'rv','UI Contribution':'av','CI Contribution':'pv'}}
};
function num(s){
  if(s==null) return null;
  s=String(s).trim(); const neg=/-$/.test(s)||/^-/.test(s);
  s=s.replace(/[^0-9.,]/g,'');
  if(!s) return null;
  let v;
  if(s.includes(',')) v=parseFloat(s.replace(/\./g,'').replace(',','.'));
  else v=parseInt(s.replace(/\./g,''),10)/100;   // DATEV prints some columns without the decimal comma
  return isNaN(v)?null:(neg?-v:v);
}
const isNumTok = s => /^-?[\d.]+(,\d+)?-?(\s*[A-Z])?$/.test(s.trim());
function find(items,label,opts={}){ return items.find(i=>i.str.trim()===label && (!opts.minY||i.y>opts.minY) && (!opts.maxY||i.y<opts.maxY)); }
function findStarts(items,label){ return items.find(i=>i.str.trim().startsWith(label)); }
// value directly under a header row label, matched to nearest column centre among that header row
function underHeader(items,label,headerY){
  const lab=items.find(i=>i.str.trim()===label && Math.abs(i.y-headerY)<2); if(!lab) return null;
  const row=items.filter(i=>Math.abs(i.y-headerY)<2 && i.str.trim().length>2);
  const cands=items.filter(i=>i.y<headerY-6 && i.y>headerY-22 && isNumTok(i.str));
  const c=i=>i.x+i.w/2;
  let best=null;
  for(const v of cands){
    const nearest=row.reduce((a,b)=>Math.abs(c(b)-c(v))<Math.abs(c(a)-c(v))?b:a);
    if(nearest===lab){ if(!best||Math.abs(c(v)-c(lab))<Math.abs(c(best)-c(lab))) best=v; }
  }
  return best;
}
function sameRowRight(items,lab,xMin,xMax){
  return items.filter(i=>Math.abs(i.y-lab.y)<3 && i.x>=xMin && i.x<=xMax && isNumTok(i.str)).sort((a,b)=>a.x-b.x)[0]||null;
}
function parse(pages){
  let page=pages.find(p=>p.some(i=>DE_PAGE.test(i.str))), lang='de';
  if(!page){ page=pages.find(p=>p.some(i=>EN_PAGE.test(i.str))); lang='en'; }
  if(!page) return {ok:false, reason:'not_datev'};
  const T=L[lang], it=page, out={ok:true,lang,warnings:[]};
  // header
  const per=it.find(i=>/^(für|for)\s+\S+\s+\d{4}$/i.test(i.str.trim()));
  if(per){ const m=per.str.trim().match(/^(?:für|for)\s+(\S+)\s+(\d{4})$/i); out.month=MONTHS[m[1].toLowerCase()]||null; out.year=+m[2]; }
  const dateIt=it.find(i=>/^\d{2}[./]\d{2}[./]\d{4}$/.test(i.str.trim())); out.payDate=dateIt?dateIt.str.trim().replace(/\//g,'.'):null;
  const idRow=it.find(i=>/^\d{5}\s+\d{6}\s+\d/.test(i.str.trim()));
  if(idRow){ const p=idRow.str.trim().split(/\s+/); out.taxClass=+p[2]; out.birth=p[1]; }
  const kkRow=it.find(i=>/^\d{7}\s+\d{4}\s+\d\s+\d{1,2}$/.test(i.str.trim()));
  if(kkRow){ const m=kkRow.str.trim().match(/^(\d{2})(\d{2})(\d{3})\s+(\d{4})/); out.kvRateTotal=+(m[1]+'.'+m[2]); out.pgrs=m[3]; out.bgrs=m[4]; }
  const insRow=it.find(i=>/^\d{8}[A-Z]\d{3}\s+/.test(i.str.trim()));
  if(insRow) out.insurer=insRow.str.trim().replace(/^\S+\s+/,'');
  const startRow=it.find(i=>/^\d{6}$/.test(i.str.trim()) && i.x>300 && i.x<360 && i.y>700);
  if(startRow){ const s=startRow.str.trim(); out.startDate=s.slice(0,2)+'.'+s.slice(2,4)+'.20'+s.slice(4); }
  const nameIt=it.find(i=>i.x<120 && i.y>640 && i.y<690 && /^[A-ZÄÖÜ][a-zäöüß]+(\s[A-ZÄÖÜ][a-zäöüß-]+)+$/.test(i.str.trim()) && !/GmbH/.test(i.str));
  out.name=nameIt?nameIt.str.trim():null;
  const emp=it.find(i=>/\*/.test(i.str) && /(GmbH|AG|KG|SE|UG|e\.V\.)/.test(i.str));
  if(emp) out.employer=emp.str.split('*').slice(0,1).join('').trim(), out.employerCity=(emp.str.split('*').pop()||'').replace(/^\d{5}\s*/,'').trim();
  // tax + social security rows
  const tg=find(it,T.taxGross,{maxY:420,minY:250});
  if(tg){ const y=tg.y;
    for(const [k,lab] of [['taxGross',T.taxGross],['wageTax',T.wageTax],['church',T.church],['soli',T.soli]]){ const v=underHeader(it,lab,y); out[k]=v?num(v.str):0; } }
  const kvb=find(it,T.kvB,{maxY:420,minY:200});
  if(kvb){ const y=kvb.y;
    for(const [k,lab] of [['kvGross',T.kvB],['rvGross',T.rvB],['avGross',T.avB],['pvGross',T.pvB],['kv',T.kv],['rv',T.rv],['av',T.av],['pv',T.pv]]){
      const v=underHeader(it,lab,y); out[k]=v?num(v.str):0; if(v&&/Z\s*$/.test(v.str)) out.childlessFlag=true; }
    if(it.some(i=>Math.abs(i.y-(y-14))<4 && /^\s*Z\s*$/.test(i.str))) out.childlessFlag=true;
  }
  // right column totals: value is the number at x>480 just below the label
  const rightTotal=lab=>{ const l=it.find(i=>i.str.trim()===lab && i.x>470); if(!l) return null;
    const v=it.filter(i=>i.x>480 && i.y<l.y-4 && i.y>l.y-22 && isNumTok(i.str)).sort((a,b)=>b.y-a.y)[0]; return v?num(v.str):null; };
  out.totalGross=rightTotal(T.totalGross); out.taxTotal=rightTotal(T.taxTot); out.svTotal=rightTotal(T.svTot);
  out.netIncome=rightTotal(T.netInc); out.payout=rightTotal(T.payout);
  // employer cost row
  for(const [k,lab] of [['agSv',T.agSv],['agAdd',T.agAdd],['agTotal',T.agTot]]){
    const l=it.find(i=>i.str.trim()===lab); if(!l){out[k]=null;continue;}
    const v=underHeader(it,lab,l.y); out[k]=v?num(v.str):null; }
  // payments (gross lines)
  const ph=it.find(i=>i.str.trim()===T.payHead && i.y>420);
  out.payments=[];
  if(ph){ const bottom=(tg?tg.y:350)+15;
    const rows=it.filter(i=>i.x<120 && i.y<ph.y-4 && i.y>bottom && /^\d{3,4}\s+\S/.test(i.str.trim()));
    for(const r of rows.sort((a,b)=>b.y-a.y)){
      const amt=it.filter(i=>Math.abs(i.y-r.y)<3 && i.x>480 && isNumTok(i.str))[0];
      const flags=it.filter(i=>Math.abs(i.y-r.y)<3 && i.x>420 && i.x<480 && /^[A-Z]$/.test(i.str.trim())).sort((a,b)=>a.x-b.x).map(i=>i.str.trim());
      const m=r.str.trim().match(/^(\d{3,4})\s+(.*)$/);
      out.payments.push({code:m[1],label:m[2],amount:amt?num(amt.str):null,tax:flags[0]||'',sv:flags[1]||'',gb:flags[2]||''});
    } }
  // net deductions / additions
  const nh=it.find(i=>i.str.trim()===T.netHead);
  out.netItems=[];
  if(nh){ const rows=it.filter(i=>i.x>280 && i.x<480 && i.y<nh.y-4 && i.y>100 && /^\d{3,4}\s+\S/.test(i.str.trim()));
    for(const r of rows.sort((a,b)=>b.y-a.y)){
      const amt=it.filter(i=>Math.abs(i.y-r.y)<3 && i.x>480 && isNumTok(i.str))[0];
      const m=r.str.trim().match(/^(\d{3,4})\s+(.*)$/);
      out.netItems.push({code:m[1],label:m[2],amount:amt?num(amt.str):null}); } }
  // year to date
  out.ytd={};
  const ytdTop=nh?nh.y:260;
  for(const [lab,key] of Object.entries(T.ytd)){
    const l=it.find(i=>i.str.trim()===lab && i.y<ytdTop+2 && i.y>110 && i.x<260); if(!l) continue;
    const xmin=l.x<100?95:220, xmax=l.x<100?175:290;
    const v=sameRowRight(it,l,xmin,xmax); out.ytd[key]=v?num(v.str):0; }
  // sanity
  if(out.totalGross==null||out.payout==null) out.warnings.push('missing_totals');
  const sumPay=out.payments.reduce((a,p)=>a+(p.amount||0),0);
  if(out.totalGross!=null && Math.abs(sumPay-out.totalGross)>0.02) out.warnings.push('gross_mismatch');
  const net=(out.totalGross||0)-(out.taxTotal||0)-(out.svTotal||0);
  if(out.netIncome!=null && Math.abs(net-out.netIncome)>0.02) out.warnings.push('net_mismatch');
  const pay=(out.netIncome||0)+out.netItems.reduce((a,p)=>a+(p.amount||0),0);
  if(out.payout!=null && Math.abs(pay-out.payout)>0.02) out.warnings.push('payout_mismatch');
  return out;
}
root.DatevParser={parse,num};
})(typeof window!=='undefined'?window:globalThis);
