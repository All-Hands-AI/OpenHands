import { spawnSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";
const [run, phase, mode="all"] = process.argv.slice(2);
if (!run?.includes("/openhands-verify/agentic-colors-")) throw new Error("Expected this task's isolated verification run.");
const cli=resolve(".agents/skills/verify-openhands/scripts/control-openhands");
function command(args) {
 const p=spawnSync(cli,[...args,"--run",run],{encoding:"utf8",maxBuffer:8*1024*1024,timeout:45000});
 if(p.status!==0) throw new Error(args.slice(0,3).join(" ")+": "+p.stdout+" "+p.stderr);
 return JSON.parse(p.stdout);
}
const inspect="(() => { const form = document.querySelector('[data-testid=\"add-mcp-server-form\"]'); const messages = [...form.querySelectorAll('p')].filter(e => /invalid|format|connected|failed|connection/i.test(e.textContent)); const rgb = color => { const c = new OffscreenCanvas(1,1); const ctx=c.getContext('2d'); ctx.fillStyle=color;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].slice(0,3); };const luminance=color=>rgb(color).map(c=>{const n=c/255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4;}).reduce((l,c,i)=>l+c*[.2126,.7152,.0722][i],0); return messages.map(e=>{const color=getComputedStyle(e).color;let parent=e;while(parent&&getComputedStyle(parent).backgroundColor==='rgba(0, 0, 0, 0)')parent=parent.parentElement;const background=getComputedStyle(parent).backgroundColor;const a=luminance(color),b=luminance(background);return {text:e.textContent,color,background,contrast:Number(((Math.max(a,b)+.05)/(Math.min(a,b)+.05)).toFixed(2)),theme:document.querySelector('[data-color-theme]')?.getAttribute('data-color-theme'),width:innerWidth};});})()";
const installInspect=inspect.replace('[data-testid="add-mcp-server-form"]','[data-testid="mcp-install-modal"]');
const themes=mode==="install-only"?[["light-plus","Light+"]]:[["openhands-deepsea","OpenHands-DeepSea"],["openhands-neutral","OpenHands-Neutral"],["openhands-neo","OpenHands-Neo"],["light-plus","Light+"],["solarized-light","Solarized Light"]];
const fixture=mode==="install-only"?null:command(["fixture","mcp-server","--name","qa-feedback"]);
const records=[];
for(const [key,label] of themes){
 command(["browser","viewport","desktop"]);
 command(["browser","goto","/settings/app"]);
 command(["browser","choose","testid=color-theme-input",label]);
 command(["browser","goto","/mcp"]);
 const record={key,error:[],success:[],install:[],images:[]};
 if(fixture){
  command(["browser","click","testid=mcp-add-custom-server"]);
  command(["browser","choose",'testid=mcp-custom-editor >> role=combobox[name="Server Type"]',"STDIO"]);
  command(["browser","fill","testid=add-mcp-server-form >> testid=name-input","qa-feedback"]);
  command(["browser","fill","testid=add-mcp-server-form >> testid=command-input",fixture.command]);
  command(["browser","fill","testid=add-mcp-server-form >> testid=args-input",fixture.args.join("\n")]);
  command(["browser","fill","testid=add-mcp-server-form >> testid=env-input","INVALID"]);
  command(["browser","click","testid=add-mcp-server-form >> testid=submit-button"]);
  record.error=command(["browser","eval",inspect]).value;
  record.images.push(command(["browser","screenshot","--feature","F17.custom-validation","--name",phase+"-"+key+"-desktop"]).path);
  command(["browser","viewport","phone"]);
  record.images.push(command(["browser","screenshot","--feature","F17.custom-validation","--name",phase+"-"+key+"-phone"]).path);
  command(["browser","fill","testid=add-mcp-server-form >> testid=env-input",""]);
  command(["browser","click","testid=add-mcp-server-form >> testid=mcp-test-connection"]);
  command(["browser","wait-text","Connected — 1 tool(s) available","--timeout","10000"]);
  record.success=command(["browser","eval",inspect]).value;
  record.images.push(command(["browser","screenshot","--feature","F17.custom-test","--name",phase+"-"+key+"-success-phone"]).path);
  command(["browser","viewport","desktop"]);
  record.images.push(command(["browser","screenshot","--feature","F17.custom-test","--name",phase+"-"+key+"-success-desktop"]).path);
 }
 command(["browser","goto","/mcp"]);
 command(["browser","click","testid=mcp-marketplace-card-github"]);

 command(["browser","fill","testid=mcp-install-field-api_key","qa-not-a-real-token"]);
 command(["browser","click","testid=mcp-install-submit"]);
 command(["browser","wait","testid=mcp-install-modal-error","--timeout","10000"]);
 record.install=command(["browser","eval",installInspect]).value;
 record.images.push(command(["browser","screenshot","--feature","F17.install-error","--name",phase+"-"+key+"-install-desktop"]).path);
 command(["browser","viewport","phone"]);
 record.images.push(command(["browser","screenshot","--feature","F17.install-error","--name",phase+"-"+key+"-install-phone"]).path);
 if(phase==="after" && [...record.error,...record.success,...record.install].some(row=>row.contrast<4.5)) throw new Error("Feedback contrast below 4.5: "+JSON.stringify(record));
 records.push(record);
 mkdirSync(run+"/evidence",{recursive:true});
 writeFileSync(run+"/evidence/"+phase+"-feedback-measurements.json",JSON.stringify(records,null,2));
 console.log(JSON.stringify({theme:key,error:record.error,success:record.success,install:record.install}));
}
command(["browser","goto","/mcp"]);
console.log(JSON.stringify({completed:records.length,report:run+"/evidence/"+phase+"-feedback-measurements.json"}));
