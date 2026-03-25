/* tla2langgraph — frontend application */

(function () {
  'use strict';

  let cy = null;

  // ---------------------------------------------------------------------------
  // Initialise
  // ---------------------------------------------------------------------------

  document.addEventListener('DOMContentLoaded', function () {
    cytoscape.use(cytoscapeDagre);

    fetch('/api/graph')
      .then(function (r) {
        if (!r.ok) return r.json().then(function (d) { throw new Error(d.error || r.statusText); });
        return r.json();
      })
      .then(initGraph)
      .catch(showError);
  });

  // ---------------------------------------------------------------------------
  // Build Cytoscape graph
  // ---------------------------------------------------------------------------

  function initGraph(data) {
    const elements = [];

    data.nodes.forEach(function (n) {
      elements.push({
        data: { id: n.id, label: n.label, is_initial: n.is_initial,
                tla_source: n.tla_source, source_line: n.source_line },
      });
    });

    data.edges.forEach(function (e, i) {
      elements.push({
        data: { id: 'e' + i, source: e.source_id, target: e.target_id,
                label: e.label, variable: e.variable, value: e.value },
      });
    });

    cy = cytoscape({
      container: document.getElementById('cy'),
      elements: elements,
      layout: { name: 'dagre', rankDir: 'LR', padding: 30, spacingFactor: 1.3 },
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'background-color': '#e8f4fd',
            'border-color': '#2196f3',
            'border-width': 2,
            shape: 'roundrectangle',
            width: 'label',
            height: 'label',
            padding: '10px',
            'font-size': '13px',
          },
        },
        {
          selector: 'node[?is_initial]',
          style: {
            'border-width': 4,
            'border-color': '#0d47a1',
            'background-color': '#bbdefb',
          },
        },
        {
          selector: 'node:selected',
          style: { 'background-color': '#fff3e0', 'border-color': '#ff9800' },
        },
        {
          selector: 'edge',
          style: {
            label: 'data(label)',
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.2,
            'line-color': '#78909c',
            'target-arrow-color': '#78909c',
            'font-size': '11px',
            color: '#546e7a',
            'text-background-color': '#fff',
            'text-background-opacity': 1,
            'text-background-padding': '3px',
          },
        },
        {
          selector: 'edge:selected',
          style: { 'line-color': '#ff9800', 'target-arrow-color': '#ff9800' },
        },
      ],
    });

    // Click handlers
    cy.on('tap', 'node', function (evt) { showNodeInspector(evt.target.data()); });
    cy.on('tap', 'edge', function (evt) { showEdgeInspector(evt.target.data()); });
    cy.on('tap', function (evt) {
      if (evt.target === cy) clearInspector();
    });

    // Enable export buttons
    document.getElementById('btn-export-skeleton').disabled = false;
    document.getElementById('btn-export-png').disabled = false;
    document.getElementById('btn-export-svg').disabled = false;

    wireExportButtons();
  }

  // ---------------------------------------------------------------------------
  // Inspector panel
  // ---------------------------------------------------------------------------

  function showNodeInspector(data) {
    const panel = document.getElementById('inspector');
    panel.innerHTML = '<h2>Node</h2>' +
      field('ID', data.id) +
      field('TLA+ action', data.tla_source) +
      field('Source line', data.source_line) +
      field('Initial state', data.is_initial ? 'Yes' : 'No');
  }

  function showEdgeInspector(data) {
    const panel = document.getElementById('inspector');
    panel.innerHTML = '<h2>Edge</h2>' +
      field('From', data.source) +
      field('To', data.target) +
      field('Pattern', data.label) +
      field('Variable', data.variable) +
      field('Value', data.value);
  }

  function clearInspector() {
    document.getElementById('inspector').innerHTML =
      '<h2>Inspector</h2><p class="placeholder">Click a node or edge to inspect it.</p>';
  }

  function field(label, value) {
    return '<div class="field"><label>' + label + '</label><span>' + value + '</span></div>';
  }

  // ---------------------------------------------------------------------------
  // Export buttons
  // ---------------------------------------------------------------------------

  function wireExportButtons() {
    document.getElementById('btn-export-skeleton').addEventListener('click', exportSkeleton);
    document.getElementById('btn-export-png').addEventListener('click', exportPng);
    document.getElementById('btn-export-svg').addEventListener('click', exportSvg);
  }

  function exportSkeleton() {
    fetch('/api/export/skeleton')
      .then(function (r) {
        if (!r.ok) throw new Error('Export failed: ' + r.statusText);
        const disposition = r.headers.get('content-disposition') || '';
        const match = disposition.match(/filename="([^"]+)"/);
        const filename = match ? match[1] : 'graph.py';
        return r.blob().then(function (blob) { return { blob: blob, filename: filename }; });
      })
      .then(function (d) { triggerDownload(URL.createObjectURL(d.blob), d.filename); })
      .catch(function (e) { alert('Skeleton export failed: ' + e.message); });
  }

  function exportPng() {
    if (!cy) return;
    cy.png({ output: 'blob', bg: 'white', scale: 2 }, function (blob) {
      triggerDownload(URL.createObjectURL(blob), 'diagram.png');
    });
    // Fallback for synchronous return
    const result = cy.png({ output: 'blob', bg: 'white', scale: 2 });
    if (result instanceof Blob) {
      triggerDownload(URL.createObjectURL(result), 'diagram.png');
    }
  }

  function exportSvg() {
    if (!cy) return;
    const svgStr = cy.svg({ scale: 1, full: true });
    const blob = new Blob([svgStr], { type: 'image/svg+xml' });
    triggerDownload(URL.createObjectURL(blob), 'diagram.svg');
  }

  function triggerDownload(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  // ---------------------------------------------------------------------------
  // Error display
  // ---------------------------------------------------------------------------

  function showError(err) {
    const panel = document.getElementById('error-panel');
    panel.style.display = 'block';
    panel.innerHTML = '<strong>Error loading specification</strong><br>' + err.message;
    document.getElementById('cy').style.display = 'none';
  }

}());
