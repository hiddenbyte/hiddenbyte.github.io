const captured = { pins:[], html:{}, svgAttrs:{}, appended:[], polylines:[], markers:[], tooltips:[], text:{}, fit:null };
function mkEl(tag,id){
  const e = {
    tagName:tag, _a:{}, style:{}, classList:{add(){},remove(){}},
    setAttribute(k,v){ this._a[k]=v; if(tag==='svg') captured.svgAttrs[k]=v; },
    getAttribute(k){return this._a[k]},
    appendChild(c){ captured.appended.push(c); return c; },
    addEventListener(){}, getBoundingClientRect(){return {left:0,width:1000}},
  };
  Object.defineProperty(e,'innerHTML',{set(v){captured.html[id]=v},get(){return captured.html[id]}});
  Object.defineProperty(e,'textContent',{set(v){captured.text[id]=v; e._t=v},get(){return e._t}});
  Object.defineProperty(e,'href',{set(v){captured.text[id+'#href']=v},get(){return captured.text[id+'#href']}});
  return e;
}
const nodes={};
this.document = {
  documentElement:{},
  getElementById(id){ return nodes[id] || (nodes[id]=mkEl(id==='profile'?'svg':'div',id)); },
  createElementNS(ns,tag){ return mkEl(tag,'svg:'+tag); },
  querySelectorAll(){ return []; },
};
this.getComputedStyle = () => ({ getPropertyValue(p){ return p==='--day1' ? ' #0077c0' : ' #b85c00'; } });
const chain={addTo(){return chain},remove(){return chain},setLatLng(){return chain},bindTooltip(t,o){captured.tooltips.push(t);return chain}};
this.L = {
  map:()=>({ fitBounds:(b)=>{captured.fit=b} }),
  tileLayer:()=>({addTo:()=>chain}),
  polyline:(ll,o)=>{ captured.polylines.push({n:ll.length,color:o.color,first:ll[0],last:ll[ll.length-1]}); return {addTo:()=>chain}; },
  circleMarker:(ll,o)=>{ captured.markers.push({at:ll,fill:o.fillColor,r:o.radius}); return chain; },
  latLngBounds:(a)=>{ captured.boundPts=a.length; return 'BOUNDS('+a.length+')'; },
  divIcon:(o)=>({div:o.className}),
  marker:(ll,o)=>{ captured.pins.push({at:ll,icon:o.icon.div}); return chain; },
};
this.captured=captured;
