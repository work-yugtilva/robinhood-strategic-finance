import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const root = process.argv[2];
if (!root) throw new Error('Pass repository root');
const facts = JSON.parse(await fs.readFile(path.join(root,'data/strategy/headline_facts.json')));
const data = JSON.parse(await fs.readFile(path.join(root,'data/strategy/workbook_inputs.json')));
const wb = Workbook.create();
const names = ['Cover','Sources','Assumptions','Historical Financials','Operating KPIs',
  'Revenue Drivers','Expense Build','Forecast','Scenarios','Sensitivity',
  'Strategic Analysis','Executive Dashboard'];
const sheet = Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const navy='#172B45', blue='#1F4E78', teal='#087E8B', light='#E9F1F5';
const gray='#64748B', text='#1D2733', green='#187240', input='#215DC6';
const fmtMoney='"$"#,##0;("$"#,##0);–', fmtNumber='#,##0.0;(#,##0.0);–', fmtPct='0.0%';
const periods=['2026Q3','2026Q4','2027Q1','2027Q2','2027Q3','2027Q4',
 '2028Q1','2028Q2','2028Q3','2028Q4','2029Q1','2029Q2'];
const cols='HIJKLMNOPQRS'.split('');
const col=i=>cols[i];
const set=(sh,addr,val)=>{sh.getRange(addr).values=[[val]]};
const formula=(sh,addr,val)=>{sh.getRange(addr).formulas=[[val]]};
const num=x=>x===''||x===null||x===undefined?null:Number(x);
const title=(sh,s)=>{
  sh.showGridLines=false;
  sh.getRange('B2').values=[[s]];
  sh.getRange('B2').format.font={name:'Arial',size:15,bold:true,color:navy};
  sh.getRange('B3:S3').format.borders={bottom:{style:'thin',color:'#C4D5E0'}};
  sh.getRange('B:B').format.columnWidth=31;
  sh.getRange('C:C').format.columnWidth=17;
  sh.getRange('D:D').format.columnWidth=16;
  sh.getRange('H:S').format.columnWidth=13;
  sh.getRange('B4:S130').format.font={name:'Arial',size:10,color:text};
};
const header=(sh,range)=>{
  const r=sh.getRange(range); r.format.fill=navy;
  r.format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};
  r.format.rowHeight=24;
};
const total=(sh,row)=>{
  const r=sh.getRange(`B${row}:S${row}`);
  r.format.fill=light; r.format.font={name:'Arial',size:10,bold:true,color:navy};
  r.format.borders={top:{style:'thin',color:'#94B5C5'}};
};
const labeled=(sh,map)=>Object.entries(map).forEach(([r,label])=>set(sh,`B${r}`,label));
const caseTag=sh=>{set(sh,'B4','Case Selected:');formula(sh,'C4',`=CHOOSE('Assumptions'!$D$4,"Base","Upside","Downside")`);sh.getRange('C4').format.font={name:'Arial',size:10,bold:true,color:green}};
const quarterHeader=(sh,row=7)=>{set(sh,`B${row}`,'USD millions unless labeled');periods.forEach((p,i)=>set(sh,`${col(i)}${row}`,p));header(sh,`B${row}:S${row}`)};

// Cover and source context.
title(sheet.Cover,'Robinhood Strategic Finance & Operating Model');
set(sheet.Cover,'B5','What Drives Robinhood’s Next Phase of Profitable Growth?');
set(sheet.Cover,'B7','Independent portfolio analysis · public data through September 28, 2026');
set(sheet.Cover,'B9','Central question');
set(sheet.Cover,'B10','Which drivers turn customer scale, assets, and product breadth into operating profit?');
set(sheet.Cover,'B13','Historical actuals'); set(sheet.Cover,'D13','2023 Q1–2026 Q2 · 14 quarters');
set(sheet.Cover,'B14','Forecast'); set(sheet.Cover,'D14','2026 Q3–2029 Q2 · 12 quarters');
set(sheet.Cover,'B15','Q3 status'); set(sheet.Cover,'D15','FORECAST / NOWCAST; July and August operating facts only');
set(sheet.Cover,'B18','Read first'); set(sheet.Cover,'D18','Executive Dashboard → Strategic Analysis → Forecast');
set(sheet.Cover,'B21','The workbook opens in Base Case. Edit blue assumption cells on Assumptions.');
set(sheet.Cover,'B22','The Scenarios comparison is a build-time snapshot; rerun the pipeline to refresh it.');
set(sheet.Cover,'B25','This is not affiliated with Robinhood Markets, Inc. Forecasts are analyst scenarios, not guidance.');
sheet.Cover.getRange('B5').format.font={name:'Arial',size:13,bold:true,color:teal};
sheet.Cover.getRange('D:D').format.columnWidth=76;

title(sheet.Sources,'Sources and model starting values');
set(sheet.Sources,'B4','Primary evidence'); header(sheet.Sources,'B4:D4');
[
 ['2026 Q2 10-Q',facts.sources.q2_2026_filing,'REPORTED'],
 ['2026 Q2 results',facts.sources.q2_2026_release,'REPORTED'],
 ['2025 10-K/A',facts.sources.fy2025,'REPORTED'],
 ['Historical registry','data/source_registry.csv','REPORTED / DERIVED'],
 ['Forecast assumptions','data/forecast/forecast_assumptions.csv','ASSUMPTION / REPORTED'],
].forEach((r,i)=>{set(sheet.Sources,`B${5+i}`,r[0]);set(sheet.Sources,`C${5+i}`,r[1]);set(sheet.Sources,`D${5+i}`,r[2]);});
sheet.Sources.getRange('C:C').format.columnWidth=74;
set(sheet.Sources,'B12','2026 Q2 model anchor'); header(sheet.Sources,'B12:D12');
const anchors=[
 ['Funded customers (m)',28.4],['Platform assets ($b)',368.7],['Gold subscribers (m)',4.8],
 ['Margin book ($b)',21.6],['Cash/deposits ($b)',18.7],['Cash Sweep ($b)',29.7],
 ['Credit avg balance ($b)',1.347],['Options contracts (m)',773.9],
 ['Equity notional ($b)',955.8],['Crypto notional ($b)',40.4],['Event contracts (b)',13.6]
];
const anchorRow={};
anchors.forEach((a,i)=>{const r=13+i;anchorRow[a[0]]=r;set(sheet.Sources,`B${r}`,a[0]);set(sheet.Sources,`C${r}`,a[1]);set(sheet.Sources,`D${r}`,'2026 Q2 report / operating release')});
set(sheet.Sources,'G12','Monthly observations — Q3 is not a financial actual');header(sheet.Sources,'G12:I12');
set(sheet.Sources,'H13','Jul 2026');set(sheet.Sources,'I13','Aug 2026');
const monthlyFields=[['funded_customers_m','Funded customers (m)'],['platform_assets_b','Platform assets ($b)'],
 ['net_deposits_b','Net deposits ($b)'],['options_contracts_m','Options contracts (m)'],
 ['equity_notional_b','Equity notional ($b)'],['crypto_app_notional_b','Crypto App notional ($b)'],
 ['crypto_bitstamp_notional_b','Bitstamp notional ($b)'],['event_contracts_b','Event contracts (b)'],
 ['margin_book_b','Margin book ($b)'],['cash_deposits_b','Cash/deposits ($b)'],['cash_sweep_b','Cash Sweep ($b)']];
const monthRow={};
for(let i=0;i<monthlyFields.length;i++){
 const [key,label]=monthlyFields[i],r=14+i;monthRow[key]=r;set(sheet.Sources,`G${r}`,label);
 for(const [j,p] of ['2026-07','2026-08'].entries()){
  const obs=data.assumptions.find(a=>a.period===p&&a.driver===key&&a.classification==='REPORTED');
  if(!obs)throw new Error(`Missing monthly fact ${p} ${key}`);
  set(sheet.Sources,`${j?'I':'H'}${r}`,Number(obs.value));
 }
}
sheet.Sources.getRange('G:G').format.columnWidth=27;
sheet.Sources.getRange('H:I').format.columnWidth=15;
set(sheet.Sources,'G27','Stocks are month-end; flows sum across months. September is an assumption.');

// Assumptions: one authoritative selector, active row, then three editable cases.
title(sheet.Assumptions,'Scenario assumptions');
set(sheet.Assumptions,'B4','Case (1 Base / 2 Upside / 3 Downside)');set(sheet.Assumptions,'D4',1);
sheet.Assumptions.getRange('D4').format.font={name:'Arial',size:11,bold:true,color:input};
sheet.Assumptions.getRange('D4').dataValidation={rule:{type:'list',values:['1','2','3']}};
set(sheet.Assumptions,'B6','Driver');set(sheet.Assumptions,'C6','Scenario');set(sheet.Assumptions,'D6','Unit');
set(sheet.Assumptions,'E6','Source / basis');periods.forEach((p,i)=>set(sheet.Assumptions,`${col(i)}6`,p));
header(sheet.Assumptions,'B6:S6');
sheet.Assumptions.getRange('E:E').format.columnWidth=43;
const drivers=[...new Set(data.assumptions.filter(a=>a.scenario==='Base'&&a.classification==='ASSUMPTION').map(a=>a.driver))].sort();
const aRow={}; let next=8;
for(const driver of drivers){
 const first=data.assumptions.find(a=>a.driver===driver&&a.scenario==='Base');
 const r=next; aRow[driver]=r;
 set(sheet.Assumptions,`B${r}`,driver.replaceAll('_',' '));set(sheet.Assumptions,`C${r}`,'ACTIVE');
 set(sheet.Assumptions,`D${r}`,first.unit);set(sheet.Assumptions,`E${r}`,first.historical_reference||first.source||'Analyst assumption');
 for(let j=0;j<3;j++){
  const sc=['Base','Upside','Downside'][j],rr=r+1+j;
  set(sheet.Assumptions,`C${rr}`,sc);
  for(let i=0;i<12;i++){
   const period=driver.startsWith('sept_')?(i===0?'2026-09':null):periods[i];
   const x=period&&data.assumptions.find(a=>a.driver===driver&&a.scenario===sc&&a.period===period);
   if(x)set(sheet.Assumptions,`${col(i)}${rr}`,Number(x.value));
  }
 }
 for(let i=0;i<12;i++){
  if(driver.startsWith('sept_')&&i!==0)continue;
  formula(sheet.Assumptions,`${col(i)}${r}`,`=CHOOSE($D$4,${col(i)}${r+1},${col(i)}${r+2},${col(i)}${r+3})`);
 }
 sheet.Assumptions.getRange(`H${r+1}:S${r+3}`).format.font={name:'Arial',size:10,color:input};
 sheet.Assumptions.getRange(`B${r}:S${r}`).format.fill='#F2F7FA';
 next+=4;
}
sheet.Assumptions.freezePanes.freezeRows(6);
sheet.Assumptions.getRange(`B131:S${next}`).format.font={name:'Arial',size:10,color:text};

// Historical actuals preserve nulls. Columns are quarters; no forecast values here.
const actual=data.actual;
const histFields=[['revenue_m','Total revenue'],['transaction_revenue_m','Transaction revenue'],
 ['net_interest_revenue_m','Net interest revenue'],['other_revenue_m','Other revenue'],
 ['options_revenue_m','Options revenue'],['crypto_revenue_m','Crypto revenue'],
 ['equities_revenue_m','Equities revenue'],['event_contracts_revenue_m','Event-contract revenue'],
 ['operating_expense_m','Operating expense'],['operating_income_m','Operating income'],
 ['net_income_m','Net income'],['adjusted_ebitda_m','Adjusted EBITDA'],
 ['operating_margin_pct','Operating margin (%)'],['adjusted_ebitda_margin_pct','Adjusted EBITDA margin (%)']];
title(sheet['Historical Financials'],'Historical financial performance · ACTUAL');
set(sheet['Historical Financials'],'B6','USD millions unless labeled');
actual.forEach((x,i)=>set(sheet['Historical Financials'],`${String.fromCharCode(68+i)}7`,x.period));
header(sheet['Historical Financials'],'B7:Q7');
const histRow={};histFields.forEach(([key,label],i)=>{
 const r=9+i;histRow[key]=r;set(sheet['Historical Financials'],`B${r}`,label);
 actual.forEach((x,j)=>{const v=num(x[key]);if(v!==null)set(sheet['Historical Financials'],`${String.fromCharCode(68+j)}${r}`,v)});
 if(['revenue_m','operating_expense_m','operating_income_m','adjusted_ebitda_m'].includes(key))total(sheet['Historical Financials'],r);
});
sheet['Historical Financials'].freezePanes.freezeRows(7);
sheet['Historical Financials'].getRange('D21:Q22').format.numberFormat='0.0"%"';
set(sheet['Historical Financials'],'B26','Source: data/processed/historical_financials_quarterly.csv; missing disclosures remain blank.');

const kpiFields=[['funded_customers_m','Funded customers (m)'],['platform_assets_b','Platform assets ($b)'],
 ['net_deposits_b','Net deposits ($b)'],['reported_arpu_usd_annualized','Reported ARPU ($ annualized)'],
 ['gold_subscribers_m','Gold subscribers (m)'],['options_contracts_m','Options contracts (m)'],
 ['crypto_notional_b','Crypto notional ($b)'],['equity_notional_b','Equity notional ($b)'],
 ['event_contracts_b','Event contracts (b)'],['margin_book_b','Margin book ($b)'],
 ['cash_deposits_b','Cash/deposits ($b)'],['cash_sweep_b','Cash Sweep ($b)']];
title(sheet['Operating KPIs'],'Customer and operating metrics · ACTUAL');
actual.forEach((x,i)=>set(sheet['Operating KPIs'],`${String.fromCharCode(68+i)}7`,x.period));header(sheet['Operating KPIs'],'B7:Q7');
kpiFields.forEach(([key,label],i)=>{const r=9+i;set(sheet['Operating KPIs'],`B${r}`,label);actual.forEach((x,j)=>{const v=num(x[key]);if(v!==null)set(sheet['Operating KPIs'],`${String.fromCharCode(68+j)}${r}`,v)})});
set(sheet['Operating KPIs'],'B23','Stocks use quarter-end; net deposits and trading volume are quarterly flows.');
sheet['Operating KPIs'].freezePanes.freezeRows(7);

const A=(key,i)=>`'Assumptions'!${col(i)}${aRow[key]}`;
const R=(row,i)=>`${col(i)}${row}`;
const S=(row,column='C')=>`'Sources'!${column}${row}`;
const M=(key,column)=>S(monthRow[key],column);
const anchorsRef={customers:S(13),assets:S(14),gold:S(15),margin:S(16),cash:S(17),sweep:S(18),credit:S(19),options:S(20),equity:S(21),crypto:S(22),event:S(23)};
const rr={beginCust:10,addCust:11,endCust:12,avgCust:13,beginAssets:15,deposits:16,
 market:17,acquired:18,assetOther:19,endAssets:20,optionsPer:22,optionsUnits:23,
 optionsPrice:24,optionsRev:25,equityPer:27,equityUnits:28,equityBps:29,equityRev:30,
 appPer:32,bitPer:33,appUnits:34,bitUnits:35,cryptoUnits:36,cryptoBps:37,cryptoRev:38,
 eventPer:40,eventUnits:41,eventPrice:42,eventRev:43,otherTxnPer:45,otherTxnRev:46,txnRev:47,
 marginEnd:49,cashEnd:50,sweepEnd:51,creditAvg:52,marginAvg:54,cashAvg:55,sweepAvg:56,
 creditBalance:57,marginYield:59,cashYield:60,sweepYield:61,creditYield:62,
 marginRev:64,cashRev:65,sweepRev:66,creditRev:67,interestOther:68,nir:69,
 goldEnd:71,goldAvg:72,goldRev:73,proxy:74,resOther:75,otherRev:76,totalRev:78,
 marketMix:80,interestMix:81,recurringMix:82,unclassifiedMix:83,assetsPerCust:85};
const revenueLabels={10:'Beginning funded customers (m)',11:'Net customer additions (m)',12:'Ending funded customers (m)',13:'Average funded customers (m)',
15:'Beginning platform assets ($b)',16:'Net deposits ($b)',17:'Market / value change ($b)',18:'Acquired assets ($b)',19:'Other asset change ($b)',20:'Ending platform assets ($b)',
22:'Options contracts / customer',23:'Options contracts (m)',24:'Revenue / contract ($)',25:'Options revenue ($m)',
27:'Equity notional / customer',28:'Equity notional ($b)',29:'Equity realized bps',30:'Equities revenue ($m)',
32:'Crypto App volume / customer',33:'Bitstamp volume / customer',34:'Crypto App volume ($b)',35:'Bitstamp volume ($b)',36:'Total crypto volume ($b)',37:'Blended crypto bps',38:'Crypto revenue ($m)',
40:'Event contracts / customer',41:'Event contracts (b)',42:'Revenue / event contract ($)',43:'Event revenue ($m)',
45:'Other transaction $ / customer',46:'Other transaction revenue ($m)',47:'Transaction revenue ($m)',
49:'Margin book end ($b)',50:'Cash / deposits end ($b)',51:'Cash Sweep end ($b)',52:'Credit average balance ($b)',
54:'Margin average balance ($b)',55:'Cash average balance ($b)',56:'Sweep average balance ($b)',57:'Credit average balance ($b)',
59:'Margin realized yield (%)',60:'Cash / deposits realized yield (%)',61:'Sweep realized yield (%)',62:'Credit realized yield (%)',
64:'Margin interest revenue ($m)',65:'Cash / deposits interest ($m)',66:'Cash Sweep interest ($m)',67:'Credit card interest ($m)',68:'Other net interest ($m)',69:'Net interest revenue ($m)',
71:'Gold subscribers end (m)',72:'Gold subscribers average (m)',73:'Gold subscription revenue ($m)',74:'Proxy revenue ($m)',75:'Other residual revenue ($m)',76:'Other revenue ($m)',78:'TOTAL REVENUE ($m)',
80:'Market activity revenue ($m)',81:'Interest / balance revenue ($m)',82:'Disclosed recurring revenue ($m)',83:'Unclassified revenue ($m)',85:'Platform assets / customer ($)'};
title(sheet['Revenue Drivers'],'Revenue drivers and balance roll-forward');caseTag(sheet['Revenue Drivers']);quarterHeader(sheet['Revenue Drivers']);labeled(sheet['Revenue Drivers'],revenueLabels);
for(let i=0;i<12;i++){
 const c=col(i),p=col(i-1),q3=i===0, F=(row,expr)=>formula(sheet['Revenue Drivers'],`${c}${row}`,`=${expr}`);
 const old=(row,anchor)=>q3?anchor:`${p}${row}`;
 F(rr.beginCust,old(rr.endCust,anchorsRef.customers));
 F(rr.endCust,q3?`${M('funded_customers_m','I')}+${A('sept_net_customer_additions_m',i)}`:`${c}${rr.beginCust}+${A('net_customer_additions_m',i)}`);
 F(rr.addCust,`${c}${rr.endCust}-${c}${rr.beginCust}`);F(rr.avgCust,`(${c}${rr.beginCust}+${c}${rr.endCust})/2`);
 F(rr.beginAssets,old(rr.endAssets,anchorsRef.assets));
 F(rr.deposits,q3?`${M('net_deposits_b','H')}+${M('net_deposits_b','I')}+${A('sept_net_deposits_b',i)}`:A('net_deposits_b',i));
 F(rr.market,q3?`${M('platform_assets_b','I')}*${A('sept_asset_value_change_pct',i)}`:`${c}${rr.beginAssets}*${A('asset_value_change_pct',i)}`);
 F(rr.acquired,A('acquired_assets_b',i));
 F(rr.assetOther,q3?`${M('platform_assets_b','I')}-${c}${rr.beginAssets}-${M('net_deposits_b','H')}-${M('net_deposits_b','I')}`:A('other_asset_change_b',i));
 F(rr.endAssets,`SUM(${c}${rr.beginAssets},${c}${rr.deposits}:${c}${rr.assetOther})`);
 for(const [row,key] of [[rr.optionsPer,'options_per_customer'],[rr.optionsPrice,'option_revenue_per_contract_usd'],
  [rr.equityPer,'equity_notional_per_customer_b'],[rr.equityBps,'equity_monetization_bps'],
  [rr.appPer,'crypto_app_per_customer_b'],[rr.bitPer,'crypto_bitstamp_per_customer_b'],[rr.cryptoBps,'crypto_blended_bps'],
  [rr.eventPer,'event_contracts_per_customer_b'],[rr.eventPrice,'event_revenue_per_contract_usd'],
  [rr.otherTxnPer,'other_transaction_per_customer_usd'],[rr.marginYield,'margin_realized_yield_pct'],
  [rr.cashYield,'cash_deposit_realized_yield_pct'],[rr.sweepYield,'cash_sweep_realized_yield_pct'],
  [rr.creditYield,'credit_card_realized_yield_pct'],[rr.interestOther,'interest_remainder_m'],
  [rr.proxy,'proxy_revenue_m'],[rr.resOther,'residual_other_revenue_m']])F(row,A(key,i));
 F(rr.optionsUnits,q3?`${M('options_contracts_m','H')}+${M('options_contracts_m','I')}+${A('sept_options_contracts_m',i)}`:`${c}${rr.avgCust}*${c}${rr.optionsPer}`);
 F(rr.optionsRev,`${c}${rr.optionsUnits}*${c}${rr.optionsPrice}`);
 F(rr.equityUnits,q3?`${M('equity_notional_b','H')}+${M('equity_notional_b','I')}+${A('sept_equity_notional_b',i)}`:`${c}${rr.avgCust}*${c}${rr.equityPer}`);
 F(rr.equityRev,`${c}${rr.equityUnits}*${c}${rr.equityBps}/10`);
 F(rr.appUnits,q3?`${M('crypto_app_notional_b','H')}+${M('crypto_app_notional_b','I')}+${A('sept_crypto_app_notional_b',i)}`:`${c}${rr.avgCust}*${c}${rr.appPer}`);
 F(rr.bitUnits,q3?`${M('crypto_bitstamp_notional_b','H')}+${M('crypto_bitstamp_notional_b','I')}+${A('sept_crypto_bitstamp_notional_b',i)}`:`${c}${rr.avgCust}*${c}${rr.bitPer}`);
 F(rr.cryptoUnits,`${c}${rr.appUnits}+${c}${rr.bitUnits}`);F(rr.cryptoRev,`${c}${rr.cryptoUnits}*${c}${rr.cryptoBps}/10`);
 F(rr.eventUnits,q3?`${M('event_contracts_b','H')}+${M('event_contracts_b','I')}+${A('sept_event_contracts_b',i)}`:`${c}${rr.avgCust}*${c}${rr.eventPer}`);
 F(rr.eventRev,`${c}${rr.eventUnits}*1000*${c}${rr.eventPrice}`);
 F(rr.otherTxnRev,`${c}${rr.avgCust}*${c}${rr.otherTxnPer}`);
 F(rr.txnRev,`SUM(${c}${rr.optionsRev},${c}${rr.equityRev},${c}${rr.cryptoRev},${c}${rr.eventRev},${c}${rr.otherTxnRev})`);
 F(rr.marginEnd,q3?A('sept_margin_balance_b',i):`${c}${rr.endCust}*${A('margin_balance_per_customer_b',i)}`);
 const cashPool=q3?`${M('cash_deposits_b','I')}+${M('cash_sweep_b','I')}+${A('sept_net_deposits_b',i)}*${A('cash_capture_ratio',i)}`:
  `${p}${rr.cashEnd}+${p}${rr.sweepEnd}+${c}${rr.deposits}*${A('cash_capture_ratio',i)}`;
 F(rr.cashEnd,`(${cashPool})*${A('cash_deposit_share',i)}`);
 F(rr.sweepEnd,`(${cashPool})-${c}${rr.cashEnd}`);
 F(rr.creditAvg,`${old(rr.creditAvg,anchorsRef.credit)}*(1+${A('credit_balance_growth_pct',i)})`);
 F(rr.marginAvg,q3?`(${M('margin_book_b','H')}+${M('margin_book_b','I')}+${c}${rr.marginEnd})/3`:`(${p}${rr.marginEnd}+${c}${rr.marginEnd})/2`);
 F(rr.cashAvg,q3?`(${M('cash_deposits_b','H')}+${M('cash_deposits_b','I')}+${c}${rr.cashEnd})/3`:`(${p}${rr.cashEnd}+${c}${rr.cashEnd})/2`);
 F(rr.sweepAvg,q3?`(${M('cash_sweep_b','H')}+${M('cash_sweep_b','I')}+${c}${rr.sweepEnd})/3`:`(${p}${rr.sweepEnd}+${c}${rr.sweepEnd})/2`);
 F(rr.creditBalance,`${c}${rr.creditAvg}`);
 for(const [rev,bal,yieldRow] of [[rr.marginRev,rr.marginAvg,rr.marginYield],[rr.cashRev,rr.cashAvg,rr.cashYield],
  [rr.sweepRev,rr.sweepAvg,rr.sweepYield],[rr.creditRev,rr.creditBalance,rr.creditYield]])F(rev,`${c}${bal}*1000*${c}${yieldRow}/100/4`);
 F(rr.nir,`SUM(${c}${rr.marginRev}:${c}${rr.interestOther})`);
 F(rr.goldEnd,`${old(rr.goldEnd,anchorsRef.gold)}+${A('gold_net_subscriber_additions_m',i)}`);
 F(rr.goldAvg,`(${old(rr.goldEnd,anchorsRef.gold)}+${c}${rr.goldEnd})/2`);
 F(rr.goldRev,`${c}${rr.goldAvg}*${A('gold_revenue_per_avg_subscriber_usd',i)}`);
 F(rr.otherRev,`SUM(${c}${rr.goldRev},${c}${rr.proxy},${c}${rr.resOther})`);
 F(rr.totalRev,`SUM(${c}${rr.txnRev},${c}${rr.nir},${c}${rr.otherRev})`);
 F(rr.marketMix,`SUM(${c}${rr.optionsRev},${c}${rr.equityRev},${c}${rr.cryptoRev},${c}${rr.eventRev})`);
 F(rr.interestMix,`${c}${rr.nir}`);F(rr.recurringMix,`${c}${rr.goldRev}`);
 F(rr.unclassifiedMix,`SUM(${c}${rr.otherTxnRev},${c}${rr.proxy},${c}${rr.resOther})`);
 F(rr.assetsPerCust,`1000*${c}${rr.endAssets}/${c}${rr.endCust}`);
}
for(const r of [12,20,25,30,38,43,47,69,76,78])total(sheet['Revenue Drivers'],r);
sheet['Revenue Drivers'].getRange('H8:S85').format.numberFormat=fmtNumber;
sheet['Revenue Drivers'].freezePanes.freezeRows(7);

const er={index:10,fixed:11,variable:12,brokerage:13,tech:15,opsBase:17,opsShare:18,ops:19,
 creditRate:21,credit:22,marketingBase:24,marketingShare:25,marketing:26,general:28,total:30,ratio:31};
const expenseLabels={10:'Trading activity index (Q2=1)',11:'Brokerage fixed budget ($m)',12:'Brokerage variable budget ($m)',13:'Brokerage / transaction ($m)',
 15:'Technology / development ($m)',17:'Operations base ($m)',18:'Operations customer variable share',19:'Operations ($m)',
 21:'Credit provision / quarterly balance',22:'Credit loss provision ($m)',24:'Marketing base ($m)',25:'Marketing additions variable share',26:'Marketing ($m)',
 28:'General / administrative ($m)',30:'OPERATING EXPENSE ($m)',31:'Expense / revenue (%)'};
title(sheet['Expense Build'],'Six-category operating expense build');caseTag(sheet['Expense Build']);quarterHeader(sheet['Expense Build']);labeled(sheet['Expense Build'],expenseLabels);
for(let i=0;i<12;i++){
 const c=col(i),F=(row,expr)=>formula(sheet['Expense Build'],`${c}${row}`,`=${expr}`),v=r=>`'Revenue Drivers'!${c}${r}`;
 F(er.index,`${A('brokerage_options_weight',i)}*${v(rr.optionsUnits)}/${anchorsRef.options}+${A('brokerage_equity_weight',i)}*${v(rr.equityUnits)}/${anchorsRef.equity}+${A('brokerage_crypto_weight',i)}*${v(rr.cryptoUnits)}/${anchorsRef.crypto}+${A('brokerage_event_weight',i)}*${v(rr.eventUnits)}/${anchorsRef.event}`);
 for(const [row,key] of [[er.fixed,'brokerage_fixed_m'],[er.variable,'brokerage_variable_m'],[er.tech,'technology_base_m'],
  [er.opsBase,'operations_base_m'],[er.opsShare,'operations_customer_variable_share'],
  [er.creditRate,'credit_provision_pct'],[er.marketingBase,'marketing_base_m'],
  [er.marketingShare,'marketing_additions_variable_share'],[er.general,'general_base_m']])F(row,A(key,i));
 F(er.brokerage,`${c}${er.fixed}+${c}${er.variable}*${c}${er.index}`);
 F(er.ops,`${c}${er.opsBase}*((1-${c}${er.opsShare})+${c}${er.opsShare}*${v(rr.endCust)}/${anchorsRef.customers})`);
 F(er.credit,`${v(rr.creditAvg)}*1000*${c}${er.creditRate}`);
 F(er.marketing,`${c}${er.marketingBase}*((1-${c}${er.marketingShare})+${c}${er.marketingShare}*${v(rr.addCust)}/${A('marketing_reference_additions_m',i)})`);
 F(er.total,`SUM(${c}${er.brokerage},${c}${er.tech},${c}${er.ops},${c}${er.credit},${c}${er.marketing},${c}${er.general})`);
 F(er.ratio,`${c}${er.total}/'Revenue Drivers'!${c}${rr.totalRev}`);
}
for(const r of [13,15,19,22,26,28,30])total(sheet['Expense Build'],r);
sheet['Expense Build'].getRange('H8:S31').format.numberFormat=fmtNumber;
sheet['Expense Build'].getRange('H31:S31').format.numberFormat=fmtPct;

const fr={rev:10,expense:11,oi:12,margin:13,otherIncome:14,pretax:15,tax:16,net:17,
 sbc:18,da:19,debt:20,ebitda:21,ebitdaMargin:22,arpu:23,customers:24,assets:25,deposits:26,check:29};
const forecastLabels={10:'TOTAL REVENUE ($m)',11:'Operating expense ($m)',12:'OPERATING INCOME ($m)',13:'Operating margin (%)',
14:'Nonoperating income ($m)',15:'Pretax income ($m)',16:'Income tax expense ($m)',17:'Net income ($m)',
18:'SBC adjustment ($m)',19:'D&A adjustment ($m)',20:'Debt-interest addback ($m)',21:'ADJUSTED EBITDA ($m)',
22:'Adjusted EBITDA margin (%)',23:'Derived annualized ARPU ($)',24:'Ending funded customers (m)',
25:'Ending platform assets ($b)',26:'Net deposits ($b)',29:'Revenue less component sum (check)'};
title(sheet.Forecast,'Quarterly operating forecast · Q3 2026 is NOWCAST');caseTag(sheet.Forecast);quarterHeader(sheet.Forecast);labeled(sheet.Forecast,forecastLabels);
for(let i=0;i<12;i++){
 const c=col(i),F=(row,expr)=>formula(sheet.Forecast,`${c}${row}`,`=${expr}`),v=r=>`'Revenue Drivers'!${c}${r}`,e=r=>`'Expense Build'!${c}${r}`;
 F(fr.rev,v(rr.totalRev));F(fr.expense,e(er.total));F(fr.oi,`${c}${fr.rev}-${c}${fr.expense}`);
 F(fr.margin,`${c}${fr.oi}/${c}${fr.rev}`);F(fr.otherIncome,A('nonoperating_income_m',i));
 F(fr.pretax,`${c}${fr.oi}+${c}${fr.otherIncome}`);
 F(fr.tax,`MAX(0,${c}${fr.pretax})*${A('effective_tax_rate_pct',i)}/100`);
 F(fr.net,`${c}${fr.pretax}-${c}${fr.tax}`);
 F(fr.sbc,A('sbc_adjustment_m',i));F(fr.da,A('depreciation_adjustment_m',i));
 F(fr.debt,A('debt_interest_adjustment_m',i));
 F(fr.ebitda,`SUM(${c}${fr.net},${c}${fr.tax},${c}${fr.sbc}:${c}${fr.debt})-${c}${fr.otherIncome}`);
 F(fr.ebitdaMargin,`${c}${fr.ebitda}/${c}${fr.rev}`);
 F(fr.arpu,`4*${c}${fr.rev}/${v(rr.avgCust)}`);
 F(fr.customers,v(rr.endCust));F(fr.assets,v(rr.endAssets));F(fr.deposits,v(rr.deposits));
 F(fr.check,`${c}${fr.rev}-SUM(${v(rr.txnRev)},${v(rr.nir)},${v(rr.otherRev)})`);
}
for(const r of [10,12,17,21])total(sheet.Forecast,r);
sheet.Forecast.getRange('H8:S29').format.numberFormat=fmtNumber;
sheet.Forecast.getRange('H13:S13').format.numberFormat=fmtPct;
sheet.Forecast.getRange('H22:S22').format.numberFormat=fmtPct;
sheet.Forecast.getRange('H29:S29').format.numberFormat='0.00';
sheet.Forecast.freezePanes.freezeRows(7);

// Comparison and sensitivity are reference snapshots. They never masquerade as live cases.
title(sheet.Scenarios,'Scenario reference · refreshed by build command');
set(sheet.Scenarios,'B4','Selected live case is on Forecast; the tables below are build-time snapshots.');
const scenHeader=['Case','Year','Revenue ($m)','Operating income ($m)','Operating margin','Adjusted EBITDA ($m)','Funded customers (m)','Assets ($b)'];
sheet.Scenarios.getRange('B7:I7').values=[scenHeader];header(sheet.Scenarios,'B7:I7');
let sr=8;for(const sc of ['Base','Upside','Downside'])for(const y of ['2026','2027','2028']){
 const x=facts.model.annual[sc][y];sheet.Scenarios.getRange(`B${sr}:I${sr}`).values=[[
  sc,y,x.revenue_m,x.operating_income_m,x.operating_margin_pct/100,x.adjusted_ebitda_m,x.funded_customers_m,x.platform_assets_b]];sr++;
}
sheet.Scenarios.getRange('C8:I16').format.numberFormat=fmtNumber;
sheet.Scenarios.getRange('F8:F16').format.numberFormat=fmtPct;
set(sheet.Scenarios,'B19','2026 = two reported quarters + two forecast quarters. All 2027–2028 values are analyst scenarios.');
sheet.Scenarios.getRange('B:B').format.columnWidth=34;

title(sheet.Sensitivity,'Defined shocks · Base reference');
set(sheet.Sensitivity,'B4','These are isolated model tests, not probabilities. Rate policy excludes Cash Sweep.');
sheet.Sensitivity.getRange('B7:F7').values=[['Driver','Shock','2027 revenue Δ ($m)','2027 operating income Δ ($m)','Interpretation']];header(sheet.Sensitivity,'B7:F7');
const shocks=[
 ['Policy rate','-100 bp',facts.model.shocks.policy_rate_down_100bp_m,facts.model.shocks.policy_rate_down_100bp_m,'Analyst pass-through; Cash Sweep excluded'],
 ['All realized yields','+100 bp',facts.model.shocks.uniform_yield_up_100bp_m,facts.model.shocks.uniform_yield_up_100bp_m,'Broad unit stress; not policy exposure'],
 ['Transaction monetization','-20%',facts.model.shocks.transaction_monetization_down_20pct_m,facts.model.shocks.transaction_monetization_down_20pct_m,'All four product unit rates'],
 ['Options activity','-20%',facts.model.shocks.options_activity_down_20pct_revenue_m,facts.model.shocks.options_activity_down_20pct_oi_m,'Exact isolated model shock'],
 ['Technology expense','+10%',0,facts.model.shocks.technology_up_10pct_oi_m,'Operating income only'],
];
shocks.forEach((r,i)=>sheet.Sensitivity.getRange(`B${8+i}:F${8+i}`).values=[r]);
sheet.Sensitivity.getRange('D8:E12').format.numberFormat=fmtMoney;
sheet.Sensitivity.getRange('D:D').format.columnWidth=26;
sheet.Sensitivity.getRange('E:E').format.columnWidth=30;
sheet.Sensitivity.getRange('F:F').format.columnWidth=48;
set(sheet.Sensitivity,'B16','See data/forecast/sensitivity_results.csv for exact one- and two-variable outcomes.');

title(sheet['Strategic Analysis'],'Three paths to profitable growth');caseTag(sheet['Strategic Analysis']);
set(sheet['Strategic Analysis'],'B7','Path');set(sheet['Strategic Analysis'],'D7','Defined 2027 revenue Δ');
set(sheet['Strategic Analysis'],'F7','Operating income Δ');set(sheet['Strategic Analysis'],'H7','Dependency');
header(sheet['Strategic Analysis'],'B7:M7');
facts.model.paths.forEach((r,i)=>{const row=8+i;set(sheet['Strategic Analysis'],`B${row}`,r.path);set(sheet['Strategic Analysis'],`D${row}`,r['2027_revenue_delta_m']);
 set(sheet['Strategic Analysis'],`F${row}`,r['2027_operating_income_delta_m']);set(sheet['Strategic Analysis'],`H${row}`,r.execution_dependency)});
sheet['Strategic Analysis'].getRange('H:H').format.columnWidth=56;
set(sheet['Strategic Analysis'],'B13','What must be true?');header(sheet['Strategic Analysis'],'B13:M13');
facts.model.thresholds.forEach((r,i)=>{const row=14+i;set(sheet['Strategic Analysis'],`B${row}`,r.threshold);
 set(sheet['Strategic Analysis'],`F${row}`,r.required_input===null?'Not attainable':r.required_input);
 set(sheet['Strategic Analysis'],`H${row}`,r.unit);});
set(sheet['Strategic Analysis'],'B21','Live selected-case thresholds');header(sheet['Strategic Analysis'],'B21:M21');
set(sheet['Strategic Analysis'],'B22','Options/customer to offset -50 bp policy rate');
// Marginal options revenue less modeled variable brokerage cost, with four 2027 quarters.
formula(sheet['Strategic Analysis'],'F22',`=AVERAGE('Revenue Drivers'!J22:M22)+0.005*(SUMPRODUCT('Revenue Drivers'!J54:M54,'Assumptions'!J${aRow.margin_rate_pass_through}:M${aRow.margin_rate_pass_through})+SUMPRODUCT('Revenue Drivers'!J55:M55,'Assumptions'!J${aRow.cash_deposit_rate_pass_through}:M${aRow.cash_deposit_rate_pass_through}))*1000/4/SUMPRODUCT('Revenue Drivers'!J13:M13,'Revenue Drivers'!J24:M24-'Expense Build'!J12:M12*'Assumptions'!J${aRow.brokerage_options_weight}:M${aRow.brokerage_options_weight}/${anchorsRef.options})`);
set(sheet['Strategic Analysis'],'B23','2027 expense ceiling before profit growth stops');
formula(sheet['Strategic Analysis'],'F23',`=SUM(Forecast!J10:M10)-SUM('Historical Financials'!P${histRow.operating_income_m}:Q${histRow.operating_income_m})-SUM(Forecast!H12:I12)`);
set(sheet['Strategic Analysis'],'B24','2027 revenue required to hold 2026 margin');
formula(sheet['Strategic Analysis'],'F24',`=SUM(Forecast!J11:M11)/(1-(SUM('Historical Financials'!P${histRow.operating_income_m}:Q${histRow.operating_income_m})+SUM(Forecast!H12:I12))/(SUM('Historical Financials'!P${histRow.revenue_m}:Q${histRow.revenue_m})+SUM(Forecast!H10:I10)))`);
set(sheet['Strategic Analysis'],'B27','Priorities');header(sheet['Strategic Analysis'],'B27:M27');
facts.recommendation.priorities.forEach((x,i)=>set(sheet['Strategic Analysis'],`B${28+i}`,`${i+1}. ${x}`));
set(sheet['Strategic Analysis'],'B32','Major risks');header(sheet['Strategic Analysis'],'B32:M32');
facts.recommendation.risks.forEach((x,i)=>set(sheet['Strategic Analysis'],`B${33+i}`,`${i+1}. ${x}`));
set(sheet['Strategic Analysis'],'B36','Thresholds are conditional tests. Public data do not support initiative ROI or product margins.');
sheet['Strategic Analysis'].getRange('B:B').format.columnWidth=49;
sheet['Strategic Analysis'].getRange('D8:F24').format.numberFormat=fmtNumber;

title(sheet['Executive Dashboard'],'Robinhood: growth needs engagement, balances, and cost conversion');caseTag(sheet['Executive Dashboard']);
const dash=sheet['Executive Dashboard'];
set(dash,'B7','2027 selected case');header(dash,'B7:N7');
const dashMetrics=[
 ['Revenue ($m)',`=SUM(Forecast!J10:M10)`],
 ['Revenue growth vs 2026',`=E9/(SUM('Historical Financials'!P${histRow.revenue_m}:Q${histRow.revenue_m})+SUM(Forecast!H10:I10))-1`],
 ['Funded customers (m)',`='Revenue Drivers'!M12`],
 ['Platform assets ($b)',`='Revenue Drivers'!M20`],
 ['Net deposits ($b)',`=SUM('Revenue Drivers'!J16:M16)`],
 ['Derived ARPU ($)',`=E9/AVERAGE('Revenue Drivers'!J13:M13)`],
 ['Operating margin',`=SUM(Forecast!J12:M12)/E9`],
 ['Adjusted EBITDA margin',`=SUM(Forecast!J21:M21)/E9`]
];
dashMetrics.forEach(([label,f],i)=>{const r=9+i;set(dash,`B${r}`,label);formula(dash,`E${r}`,f)});
dash.getRange('E9:E16').format.numberFormat=fmtNumber;
for(const r of [10,15,16])dash.getRange(`E${r}`).format.numberFormat=fmtPct;
set(dash,'G9','2027 revenue mix');header(dash,'G9:N9');
const mixRows=[['Market activity',rr.marketMix],['Interest / balance',rr.interestMix],
 ['Disclosed Gold',rr.recurringMix],['Unclassified',rr.unclassifiedMix]];
mixRows.forEach(([label,row],i)=>{const r=10+i;set(dash,`G${r}`,label);formula(dash,`J${r}`,`=SUM('Revenue Drivers'!J${row}:M${row})/E9`)});
dash.getRange('J10:J13').format.numberFormat=fmtPct;
set(dash,'G16','2027 downside / upside reference');
set(dash,'G17',`${Math.round(facts.model.annual.Downside['2027'].revenue_m).toLocaleString()} / ${Math.round(facts.model.annual.Upside['2027'].revenue_m).toLocaleString()} ($m)`);
set(dash,'B20','Financial exposures');header(dash,'B20:N20');
set(dash,'B21','Transaction monetization -20%');set(dash,'E21',facts.model.shocks.transaction_monetization_down_20pct_m);
set(dash,'B22','Policy rate -100 bp');set(dash,'E22',facts.model.shocks.policy_rate_down_100bp_m);
set(dash,'B23','Options activity -20% (operating income)');set(dash,'E23',facts.model.shocks.options_activity_down_20pct_oi_m);
dash.getRange('E21:E23').format.numberFormat=fmtMoney;
set(dash,'B27','Three priorities');header(dash,'B27:N27');
['Protect options activity and realized pricing','Grow earning balances and Gold depth',
 'Gate spending to revenue conversion'].forEach((x,i)=>set(dash,`B${28+i}`,`${i+1}. ${x}`));
set(dash,'B32','Two risks');header(dash,'B32:N32');
['Trading and crypto demand normalize','Rate and credit costs weaken margin'].forEach((x,i)=>set(dash,`B${33+i}`,`${i+1}. ${x}`));
set(dash,'B36','2026 Q3 is forecast/nowcast. Reference shocks are frozen at build time.');
dash.getRange('B:B').format.columnWidth=51;
dash.getRange('G:G').format.columnWidth=30;

// A small range-backed historical + selected forecast revenue chart.
dash.getRange('Q7:R7').values=[['Quarter','Revenue ($m)']];
for(let i=0;i<14;i++){const row=8+i;set(dash,`Q${row}`,actual[i].period);formula(dash,`R${row}`,`='Historical Financials'!${String.fromCharCode(68+i)}${histRow.revenue_m}`)}
for(let i=0;i<12;i++){const row=22+i;set(dash,`Q${row}`,periods[i]);formula(dash,`R${row}`,`=Forecast!${col(i)}10`)}
const chart=dash.charts.add('line',dash.getRange('Q7:R33'));
chart.title='Quarterly revenue: actual + selected case';chart.titleTextStyle.typeface='Arial';
chart.titleTextStyle.fontSize=11;chart.hasLegend=false;
chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:9}};
chart.yAxis={numberFormatCode:'$#,##0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:9}};
chart.setPosition('H19','N26');

// Bounded working-area formats and compact screenshot crops.
for(const name of names){
 const sh=sheet[name];
 sh.getRange('B2:S3').format.rowHeight=23;
}
wb.recalculate();
for(const [selector,scenario] of [[2,'Upside'],[3,'Downside'],[1,'Base']]){
 set(sheet.Assumptions,'D4',selector); wb.recalculate();
 const actualRevenue=Number(dash.getRange('E9').values[0][0]);
 const expectedRevenue=facts.model.annual[scenario]['2027'].revenue_m;
 if(Math.abs(actualRevenue-expectedRevenue)>0.01)throw new Error(`${scenario} selector mismatch: ${actualRevenue} vs ${expectedRevenue}`);
 for(let i=0;i<12;i++){
  const c=col(i),reference=data.forecast[scenario][i];
  for(const [tab,row,key] of [
   ['Forecast',fr.rev,'revenue_m'],['Forecast',fr.expense,'operating_expense_m'],
   ['Forecast',fr.oi,'operating_income_m'],['Forecast',fr.ebitda,'adjusted_ebitda_m'],
   ['Revenue Drivers',rr.endCust,'funded_customers_m'],
   ['Revenue Drivers',rr.endAssets,'platform_assets_b'],
   ['Revenue Drivers',rr.optionsUnits,'options_contracts_m'],
   ['Revenue Drivers',rr.cryptoUnits,'crypto_notional_b'],
   ['Revenue Drivers',rr.nir,'net_interest_revenue_m'],
   ['Revenue Drivers',rr.otherRev,'other_revenue_m']]){
    const got=Number(sheet[tab].getRange(`${c}${row}`).values[0][0]);
    if(!Number.isFinite(got)||Math.abs(got-reference[key])>0.01)
      throw new Error(`${scenario} ${reference.period} ${tab}!${c}${row}: ${got} vs ${reference[key]}`);
  }
 }
 if(Number(sheet['Historical Financials'].getRange(`Q${histRow.revenue_m}`).values[0][0])!==1308)
   throw new Error('Case selector changed history');
}
const checks=[['Forecast','J10',data.forecast.Base[2].revenue_m],
 ['Revenue Drivers','H78',data.forecast.Base[0].revenue_m],
 ['Executive Dashboard','E9',facts.model.annual.Base['2027'].revenue_m]];
for(const [name,addr,expected] of checks){
 const got=Number(sheet[name].getRange(addr).values[0][0]);
 if(!Number.isFinite(got)||Math.abs(got-expected)>0.01)
  throw new Error(`${name}!${addr} mismatch: ${got} vs ${expected}`);
}
const errorScan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!',
 options:{useRegex:true,maxResults:50},summary:'formula errors'});
if(errorScan.ndjson.includes('"match"'))throw new Error(`Workbook formula error: ${errorScan.ndjson}`);
const out=path.join(root,'models');await fs.mkdir(out,{recursive:true});
const file=await SpreadsheetFile.exportXlsx(wb);
await file.save(path.join(out,'Robinhood_Strategic_Finance_Model.xlsx'));
const screenshots={
 'Executive Dashboard':['Executive Dashboard','B2:N36'],
 'Historical Financials':['Historical Financials','B2:Q24'],
 'Revenue Driver Analysis':['Revenue Drivers','B2:M47'],
 'Forecast':['Forecast','B2:S29'],
 'Sensitivity Analysis':['Sensitivity','B2:F18'],
 'Strategic Analysis':['Strategic Analysis','B2:M36']
};
const screenshotDir=path.join(root,'assets/screenshots');await fs.mkdir(screenshotDir,{recursive:true});
for(const [label,[name,range]] of Object.entries(screenshots)){
 const image=await wb.render({sheetName:name,range,scale:1.25,format:'png'});
 await fs.writeFile(path.join(screenshotDir,label.toLowerCase().replaceAll(' ','_')+'.png'),new Uint8Array(await image.arrayBuffer()));
}
console.log('Workbook exported; Base forecast and dashboard checks passed.');
