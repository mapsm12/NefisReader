"use strict";

const byId = (id) => document.getElementById(id);
const controls = ["case", "variable", "record", "layer"].map(byId);
const [caseSelect, variableSelect, recordSelect, layerSelect] = controls;
const language = document.documentElement.lang;
const copy = NEFIS_TEXT[language] || NEFIS_TEXT.en;
const names = copy.names;
const fmt = new Intl.NumberFormat(language, { maximumFractionDigits: 3 });
let plane = [];

function options(select, values, label = (value) => value) {
  select.replaceChildren(...values.map((value) => new Option(label(value), value)));
}

function setupCase() {
  const data = NEFIS_DEMO[caseSelect.value];
  options(variableSelect, Object.keys(data), (key) => key + " · " + names[key]);
  const first = Object.values(data)[0];
  options(recordSelect, first.values.map((_, i) => i));
  const layers = first.shape.length === 4;
  byId("layer-control").hidden = !layers;
  options(layerSelect, layers ? first.values[0].map((_, i) => i) : [0]);
  render();
}

function render() {
  const name = variableSelect.value;
  const { shape, units, values } = NEFIS_DEMO[caseSelect.value][name];
  const depth = shape.length === 4;
  plane = depth ? values[recordSelect.value][layerSelect.value] : values[recordSelect.value];
  const flat = plane.flat(), lo = Math.min(...flat), hi = Math.max(...flat);
  byId("variable-title").textContent = names[name];
  byId("shape").textContent = name + " · " + units + " · " + copy.shape + " (" + shape.join(" × ") + ")";
  byId("min").textContent = fmt.format(lo) + " " + units;
  byId("max").textContent = fmt.format(hi) + " " + units;
  byId("status").textContent = copy.record + " " + recordSelect.value +
    (depth ? ", " + copy.layer + " " + layerSelect.value : "") + ". " + copy.scale;
  const table = byId("matrix");
  table.replaceChildren();
  const header = table.createTHead().insertRow();
  const th = (row, label, scope) => {
    const cell = document.createElement("th");
    cell.scope = scope;
    cell.textContent = label;
    row.append(cell);
  };
  th(header, copy.row, "col");
  plane[0].forEach((_, i) => th(header, "C" + i, "col"));
  const body = table.createTBody();
  plane.forEach((line, j) => {
    const row = body.insertRow();
    th(row, j, "row");
    line.forEach((value) => {
      const cell = row.insertCell();
      const x = lo === hi ? 0.5 : (value - lo) / (hi - lo);
      const rgb = [17 + 104 * x, 59 + 164 * x, 101 + 97 * x].map(Math.round);
      cell.style.backgroundColor = "rgb(" + rgb.join(",") + ")";
      cell.style.color = x < 0.43 ? "#fff" : "#092231";
      cell.textContent = fmt.format(value);
    });
  });
  byId("csv").disabled = false;
}

function download() {
  const name = variableSelect.value;
  const text = ["fila," + plane[0].map((_, i) => "col_" + i).join(","),
    ...plane.map((row, i) => i + "," + row.join(","))].join("\n") + "\n";
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  const layer = byId("layer-control").hidden ? "" : "-k" + layerSelect.value;
  a.download = "nefisreader-demo-" + name + "-r" + recordSelect.value + layer + ".csv";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

if (typeof NEFIS_DEMO !== "undefined") {
  caseSelect.addEventListener("change", setupCase);
  controls.slice(1).forEach((control) => control.addEventListener("change", render));
  byId("csv").addEventListener("click", download);
  setupCase();
} else {
  byId("status").textContent = copy.unavailable;
}

document.querySelectorAll("[data-copy]").forEach((button) => button.addEventListener("click", async () => {
  const target = byId(button.dataset.copy);
  try {
    await navigator.clipboard.writeText(target.textContent.trim());
    button.textContent = copy.copied;
  } catch {
    const range = document.createRange();
    range.selectNodeContents(target);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    button.textContent = copy.selected;
  }
}));
