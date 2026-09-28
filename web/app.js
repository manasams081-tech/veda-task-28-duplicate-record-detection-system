const $ = (id) => document.getElementById(id);

let csvText = "";
let currentColumns = [];

$("threshold").addEventListener("input", (e) => {
  $("thresholdValue").textContent = `${e.target.value}%`;
});

$("fileInput").addEventListener("change", handleFile);

const dropZone = $("dropZone");
["dragenter", "dragover"].forEach(evt => dropZone.addEventListener(evt, e => {
  e.preventDefault(); dropZone.classList.add("drag");
}));
["dragleave", "drop"].forEach(evt => dropZone.addEventListener(evt, e => {
  e.preventDefault(); dropZone.classList.remove("drag");
}));
dropZone.addEventListener("drop", e => {
  const file = e.dataTransfer.files[0];
  if (file && file.name.toLowerCase().endsWith(".csv")) loadFile(file);
});

function handleFile(e) {
  const file = e.target.files[0];
  if (file) loadFile(file);
}

function loadFile(file) {
  $("status").textContent = "Reading CSV…";
  const reader = new FileReader();
  reader.onload = () => {
    csvText = reader.result;
    $("fileName").textContent = file.name;
    $("filenameBadge").textContent = file.name;
    currentColumns = parseHeader(csvText);
    renderFields(currentColumns);
    $("analyzeBtn").disabled = currentColumns.length === 0;
    $("status").textContent = `${currentColumns.length} columns detected. Select identity fields and run the scan.`;
  };
  reader.onerror = () => $("status").textContent = "Could not read this file.";
  reader.readAsText(file);
}

function parseHeader(text) {
  const first = text.split(/\r?\n/)[0] || "";
  // Basic CSV header parser with quoted field support.
  const cols = [];
  let cur = "", quoted = false;
  for (let i = 0; i < first.length; i++) {
    const ch = first[i];
    if (ch === '"') {
      if (quoted && first[i + 1] === '"') { cur += '"'; i++; }
      else quoted = !quoted;
    } else if (ch === "," && !quoted) { cols.push(cur.trim()); cur = ""; }
    else cur += ch;
  }
  cols.push(cur.trim());
  return cols.filter(Boolean);
}

function preferredColumns(columns) {
  const aliases = {
    name: ["name", "customer_name", "full_name"],
    email: ["email", "email_address"],
    phone: ["phone", "phone_number", "mobile", "mobile_number"],
    city: ["city", "location"]
  };
  const picks = [];
  for (const aliasesForField of Object.values(aliases)) {
    const found = columns.find(c => aliasesForField.includes(c.toLowerCase().trim()));
    if (found) picks.push(found);
  }
  return picks;
}

function renderFields(columns) {
  const box = $("fieldList");
  box.innerHTML = "";
  if (!columns.length) {
    box.innerHTML = `<div class="muted-box">No usable columns found.</div>`;
    return;
  }
  const picks = preferredColumns(columns);
  columns.forEach((col, idx) => {
    const label = document.createElement("label");
    label.className = "field-item" + (picks.includes(col) ? " selected" : "");
    label.innerHTML = `<input type="checkbox" value="${escapeHtml(col)}" ${picks.includes(col) ? "checked" : ""}> <span>${escapeHtml(col)}</span>`;
    label.querySelector("input").addEventListener("change", () => label.classList.toggle("selected"));
    box.appendChild(label);
  });
}

$("analyzeBtn").addEventListener("click", async () => {
  const fields = [...$("fieldList").querySelectorAll("input:checked")].map(x => x.value);
  if (!fields.length) {
    $("status").textContent = "Select at least one matching field.";
    return;
  }
  $("analyzeBtn").disabled = true;
  $("status").textContent = "Comparing records…";
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        csv: csvText,
        filename: $("fileName").textContent,
        fields,
        threshold: Number($("threshold").value) / 100
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Analysis failed.");
    renderResults(data);
    $("status").textContent = "Scan complete. Review potential matches before making any deletion decision.";
  } catch (err) {
    $("status").textContent = err.message;
  } finally {
    $("analyzeBtn").disabled = false;
  }
});

function renderResults(data) {
  $("emptyState").classList.add("hidden");
  $("results").classList.remove("hidden");
  $("mRows").textContent = formatNumber(data.rows);
  $("mExact").textContent = formatNumber(data.exact_pair_count);
  $("mPotential").textContent = formatNumber(data.potential_pair_count);
  $("mRemoved").textContent = formatNumber(data.removed_exact_rows);

  $("exactDownload").href = data.downloads.exact;
  $("potentialDownload").href = data.downloads.potential;
  $("cleanedDownload").href = data.downloads.cleaned;

  $("exactTable").innerHTML = buildTable(data.exact, ["row_a","row_b","match_fields","match_type"]);
  $("potentialTable").innerHTML = buildTable(data.potential, ["row_a","row_b","score","match_fields","match_type"], "score");
  $("cleanedTable").innerHTML = buildTable(data.cleaned_preview);

  $("methodText").textContent =
    `Compared ${data.rows.toLocaleString()} rows using ${data.fields.join(", ")}. Exact matches use normalized equality; potential matches use difflib similarity at ${Math.round(data.threshold * 100)}% or above. Potential matches are reported, never automatically removed.`;
}

function buildTable(rows, preferred = null, scoreKey = null) {
  if (!rows || !rows.length) return `<div class="empty-table">No records in this report.</div>`;
  const keys = preferred || Object.keys(rows[0]);
  const head = keys.map(k => `<th>${escapeHtml(k.replaceAll("_"," "))}</th>`).join("");
  const body = rows.map(row => `<tr>${keys.map(k => {
    let value = row[k] ?? "";
    const cls = scoreKey === k ? " class=\"score\"" : "";
    return `<td${cls}>${escapeHtml(String(value))}</td>`;
  }).join("")}</tr>`).join("");
  return `<table class="data-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function formatNumber(n) {
  return Number(n).toLocaleString();
}

function escapeHtml(value) {
  return value.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
}
