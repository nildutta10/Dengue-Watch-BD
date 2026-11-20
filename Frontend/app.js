const API = "/api";
let districtChart, forecastChart, map, markers = [];
const fmt = n => Number(n || 0).toLocaleString("en-US");
const el = id => document.getElementById(id);

async function api(path, options={}) {
  const response = await fetch(API + path, {
    headers: {"Content-Type":"application/json", ...(options.headers || {})},
    ...options
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

async function loadDashboard() {
  try {
    const [summary, districts, reports, prediction] = await Promise.all([
      api("/summary"), api("/districts"), api("/reports"), api("/prediction")
    ]);
    el("totalAffected").textContent = fmt(summary.affected);
    el("totalDeaths").textContent = fmt(summary.deaths);
    el("totalRecovered").textContent = fmt(summary.recovered);
    el("totalActive").textContent = fmt(summary.active_cases);
    el("lastUpdated").textContent = "Updated " + new Date().toLocaleString();
    el("todayLabel").textContent = "● " + new Date().toLocaleDateString();
    renderDistricts(districts);
    renderReports(reports);
    renderCharts(districts, prediction);
    renderPrediction(prediction);
    renderMap(districts);
  } catch (error) {
    console.error(error);
    alert("Could not load dashboard. Is the Flask server running?");
  }
}

function renderDistricts(data) {
  el("districtRows").innerHTML = data.map(d => `
    <tr><td class="district-name">${escapeHtml(d.district)}</td><td>${fmt(d.affected)}</td>
    <td>${fmt(d.deaths)}</td><td>${fmt(d.recovered)}</td><td>${fmt(d.active_cases)}</td>
    <td>${escapeHtml(d.last_updated || "—")}</td></tr>`).join("") || emptyRow(6);
  el("districtSearch").oninput = e => {
    const q = e.target.value.toLowerCase();
    [...el("districtRows").rows].forEach(row => row.hidden = !row.cells[0].textContent.toLowerCase().includes(q));
  };
}

function renderReports(data) {
  el("reportRows").innerHTML = data.map(r => `
    <tr><td>${escapeHtml(r.report_date)}</td><td class="district-name">${escapeHtml(r.district)}</td>
    <td>${escapeHtml(r.area)}</td><td>${fmt(r.affected)}</td><td>${fmt(r.deaths)}</td>
    <td><button class="secondary-btn" onclick="editReport(${r.id})">Edit</button>
    <button class="secondary-btn" onclick="deleteReport(${r.id})">Delete</button></td></tr>`).join("") || emptyRow(6);
  el("reportSearch").oninput = e => {
    const q = e.target.value.toLowerCase();
    [...el("reportRows").rows].forEach(row => row.hidden = !row.textContent.toLowerCase().includes(q));
  };
}

function emptyRow(n){return `<tr><td colspan="${n}">No records found.</td></tr>`}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

function renderCharts(districts, prediction) {
  if (districtChart) districtChart.destroy();
  districtChart = new Chart(el("districtChart"), {
    type:"bar",
    data:{labels:districts.map(d=>d.district),datasets:[{label:"Affected cases",data:districts.map(d=>d.affected),backgroundColor:"#e75b60",borderRadius:5,maxBarThickness:34}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{font:{size:9}}},y:{beginAtZero:true,grid:{color:"#eef2f4"},ticks:{font:{size:9}}}}}
  });
  if (forecastChart) forecastChart.destroy();
  forecastChart = new Chart(el("forecastChart"), {
    type:"line",
    data:{labels:(prediction.weeks||[]).map(w=>w.week),datasets:[{data:(prediction.weeks||[]).map(w=>w.illustrative_cases),borderColor:"#168c83",backgroundColor:"#168c8318",fill:true,tension:.35,pointRadius:4}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false}},y:{beginAtZero:true,grid:{color:"#eef2f4"}}}}
  });
}
function renderPrediction(p) {
  el("riskPercent").textContent = p.risk_percent == null ? "—" : p.risk_percent + "%";
  el("riskLevel").textContent = p.risk_level;
  el("riskText").textContent = p.outlook + " " + p.basis;
  el("riskLevel").style.background = p.risk_level === "High" ? "#fff0f0" : p.risk_level === "Low" ? "#eaf7f1" : "#fff3df";
  el("riskLevel").style.color = p.risk_level === "High" ? "#c94b50" : p.risk_level === "Low" ? "#168c83" : "#b77b20";
}

function renderMap(districts) {
  if (!map) {
    map = L.map("map").setView([23.8, 90.3], 6);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {attribution:"© OpenStreetMap"}).addTo(map);
  }
  markers.forEach(m=>m.remove()); markers=[];
  const coords = {
    Dhaka:[23.8103,90.4125],Chattogram:[22.3569,91.7832],Khulna:[22.8456,89.5403],
    Rajshahi:[24.3745,88.6042],Barishal:[22.7010,90.3535],Sylhet:[24.8949,91.8687],
    Rangpur:[25.7439,89.2752],Mymensingh:[24.7471,90.4203],Comilla:[23.4607,91.1809]
  };
  districts.forEach(d=>{
    if (!coords[d.district]) return;
    const marker = L.circleMarker(coords[d.district], {radius:Math.max(7,Math.min(17,6+d.affected/70)),color:"#d94d55",fillColor:"#e75b60",fillOpacity:.65,weight:1})
      .bindPopup(`<b>${escapeHtml(d.district)}</b><br>Affected: ${fmt(d.affected)}<br>Deaths: ${fmt(d.deaths)}`).addTo(map);
    markers.push(marker);
  });
}

async function editReport(id) {
  try {
    const reports = await api("/reports");
    const r = reports.find(x=>x.id===id); if(!r) return;
    el("reportId").value=r.id; el("district").value=r.district; el("area").value=r.area;
    el("reportDate").value=r.report_date; el("affected").value=r.affected;
    el("deaths").value=r.deaths; el("recovered").value=r.recovered;
    el("source").value=r.source||""; el("notes").value=r.notes||"";
    el("formTitle").textContent="Edit case report #"+id; el("submitBtn").textContent="Update report";
    scrollToForm();
  } catch(e){alert(e.message)}
}
async function deleteReport(id) {
  if (!confirm("Delete this report? This cannot be undone.")) return;
  try { await api("/reports/"+id,{method:"DELETE"}); await loadDashboard(); }
  catch(e){alert(e.message)}
}
function resetForm(){
  el("reportForm").reset();el("reportId").value="";el("formTitle").textContent="Add a case report";
  el("submitBtn").textContent="Save report";el("formMessage").textContent="";
  el("reportDate").value=new Date().toISOString().slice(0,10);
}
function scrollToForm(){el("manage").scrollIntoView({behavior:"smooth",block:"start"})}

el("reportForm").addEventListener("submit",async e=>{
  e.preventDefault();
  const id=el("reportId").value;
  const payload={
    district:el("district").value.trim(),area:el("area").value.trim(),report_date:el("reportDate").value,
    affected:Number(el("affected").value),deaths:Number(el("deaths").value),recovered:Number(el("recovered").value),
    source:el("source").value.trim(),notes:el("notes").value.trim()
  };
  try {
    await api(id?"/reports/"+id:"/reports",{method:id?"PUT":"POST",body:JSON.stringify(payload)});
    el("formMessage").textContent=id?"Report updated successfully.":"Report added successfully.";
    resetForm();await loadDashboard();
  } catch(err){el("formMessage").textContent=err.message;el("formMessage").style.color="#d94d55"}
});
resetForm();
loadDashboard();
