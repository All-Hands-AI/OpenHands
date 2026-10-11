import { spawnSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";
const [run, phase] = process.argv.slice(2);
if (!run?.includes("/openhands-verify/agentic-secret-colors-") || !["before", "after"].includes(phase)) throw new Error("Use this task's isolated run and before/after phase.");
const cli = resolve(".agents/skills/verify-openhands/scripts/control-openhands");
function command(args) {
  const p = spawnSync(cli, [...args, "--run", run], { encoding: "utf8", maxBuffer: 8 * 1024 * 1024, timeout: 45000 });
  if (p.status !== 0) throw new Error(args.slice(0, 3).join(" ") + ": " + p.stdout + " " + p.stderr);
  return JSON.parse(p.stdout);
}
const row = "testid=mcp-install-save-secret-GITHUB_PERSONAL_ACCESS_TOKEN";
// @spec MCP-005 — Credential selection follows the theme and stays readable
const inspect = `(() => {
  const row = document.querySelector('[data-testid="mcp-install-save-secret-GITHUB_PERSONAL_ACCESS_TOKEN"]');
  const checkbox = row.querySelector('input');
  const track = row.querySelector('[aria-hidden="true"]');
  const thumb = track.firstElementChild;
  const label = [...row.children].find(e => e.tagName === 'SPAN' && !e.hasAttribute('aria-hidden'));
  const code = row.querySelector('code');
  const help = row.querySelector('button');
  const canvas = new OffscreenCanvas(1, 1), ctx = canvas.getContext('2d');
  const rgba = color => { ctx.clearRect(0,0,1,1);ctx.fillStyle=color;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].map((c,i)=>i===3?c/255:c); };
  const over = (fg,bg) => fg.slice(0,3).map((c,i)=>c*fg[3]+bg[i]*(1-fg[3]));
  const background = element => { const layers=[];for(let e=element;e;e=e.parentElement)layers.push(rgba(getComputedStyle(e).backgroundColor));return layers.reverse().reduce((bg,fg)=>over(fg,bg),[255,255,255]); };
  const luminance = rgb => rgb.map(c=>{const n=c/255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4;}).reduce((sum,c,i)=>sum+c*[.2126,.7152,.0722][i],0);
  const ratio = (a,b) => {const x=luminance(a),y=luminance(b);return Number(((Math.max(x,y)+.05)/(Math.min(x,y)+.05)).toFixed(2));};
  const text = element => {const color=getComputedStyle(element).color,bg=background(element);return {color,background:bg.map(Math.round),contrast:ratio(over(rgba(color),bg),bg)};};
  const box=row.getBoundingClientRect(), style=getComputedStyle(row);
  return {checked:checkbox.checked,theme:document.querySelector('[data-color-theme]')?.getAttribute('data-color-theme'),width:innerWidth,label:text(label),code:text(code),help:text(help),trackColor:getComputedStyle(track).backgroundColor,thumbColor:getComputedStyle(thumb).backgroundColor,trackContrast:ratio(background(track),background(row)),thumbContrast:ratio(background(thumb),background(track)),rowInsideViewport:box.left>=0&&box.right<=innerWidth,rowContentOverflow:row.scrollWidth>row.clientWidth+1,focusWithin:row.contains(document.activeElement),outline:{style:style.outlineStyle,width:style.outlineWidth,color:style.outlineColor}};
})()`;
const themes = [["openhands-deepsea","OpenHands-DeepSea"],["openhands-neutral","OpenHands-Neutral"],["openhands-neo","OpenHands-Neo"],["light-plus","Light+"],["solarized-light","Solarized Light"]];
const records=[];
for (const [key,label] of themes) {
  command(["browser","viewport","desktop"]);
  command(["browser","goto","/settings/app"]);
  command(["browser","choose","testid=color-theme-input",label]);
  command(["browser","goto","/mcp"]);
  command(["browser","click","testid=mcp-marketplace-card-github"]);
  const record={key,states:[],images:[]};
  for (const viewport of ["desktop", "phone"]) {
    command(["browser","viewport",viewport]);
    const checked = command(["browser","eval",inspect]).value;
    if (!checked.checked) throw new Error("Hosted credential must start checked.");
    record.states.push({...checked,viewport});
    record.images.push(command(["browser","screenshot","--feature","F17.save-as-secret","--name",phase+"-"+key+"-checked-"+viewport]).path);
    command(["browser","click",row+" >> text=Also save as secret"]);
    const unchecked=command(["browser","eval",inspect]).value;
    if (unchecked.checked) throw new Error("Label did not uncheck its native checkbox.");
    record.states.push({...unchecked,viewport});
    record.images.push(command(["browser","screenshot","--feature","F17.save-as-secret","--name",phase+"-"+key+"-unchecked-"+viewport]).path);
    command(["browser","focus",row+" >> role=checkbox"]);
    command(["browser","press","Space"]);
    if (!command(["browser","eval",inspect]).value.checked) throw new Error("Space did not restore checked state.");
  }
  command(["browser","viewport","desktop"]);
  const focused=command(["browser","eval",inspect]).value;
  record.focus=focused.outline;
  record.images.push(command(["browser","screenshot","--feature","F17.save-as-secret","--name",phase+"-"+key+"-keyboard-focus"]).path);
  command(["browser","press","Tab"]);
  command(["browser","press","Space"]);
  record.helpLeavesChecked=command(["browser","eval",inspect]).value.checked;
  if (!record.helpLeavesChecked) throw new Error("Help button changed the checkbox.");
  record.help=command(["browser","tooltip",row+" >> role=button"]).text;
  records.push(record);
  mkdirSync(run+"/evidence",{recursive:true});
  writeFileSync(run+"/evidence/"+phase+"-secret-selection.json",JSON.stringify(records,null,2));
  console.log(JSON.stringify({theme:key,checked:record.states.filter(s=>s.checked).map(s=>({width:s.width,label:s.label.contrast,code:s.code.contrast,thumb:s.thumbContrast,track:s.trackContrast,overflow:s.rowContentOverflow})),focus:record.focus}));
}
command(["browser","goto","/mcp"]);
const failures=records.flatMap(r=>r.states.flatMap(s=>[...Object.entries({label:s.label.contrast,code:s.code.contrast,help:s.help.contrast}).filter(([,v])=>v<4.5).map(([role,contrast])=>({theme:r.key,checked:s.checked,width:s.width,role,contrast})),...(s.checked&&s.thumbContrast<3?[{theme:r.key,role:"selected thumb",contrast:s.thumbContrast}]:[])]));
console.log(JSON.stringify({report:run+"/evidence/"+phase+"-secret-selection.json",failures}));
if (phase === "after") {
  if (failures.length) throw new Error("Selection readability contract failed.");
  if (records.some(r=>r.states.some(s=>s.rowContentOverflow || !s.rowInsideViewport))) throw new Error("Secret row overflows its viewport.");
  if (records.some(r=>r.focus.style==='none' || parseFloat(r.focus.width)<2)) throw new Error("Native checkbox focus is invisible.");
}
