const UNIT = 58;  // pixels per KLE unit
const GAP = 4;    // gap between keys
const KEY_SIZE = UNIT - GAP;

// Shift/secondary labels for basic keys (Swedish-ish layout shown in Vial)
const SHIFT_LABELS = {
  '1': '!', '2': '"', '3': '#', '4': '$', '5': '%',
  '6': '&', '7': '/', '8': '(', '9': ')', '0': '=',
  '-': '?', '=': '`',
  '[': '\u00c5', ']': '^',  // Å, ^
  ';': '\u00d6', "'": '\u00c4',  // Ö, Ä
  '\\': "'", '/': '-',
  ',': ';', '.': ':',
  '`': '\u00bd',  // ½
};

// Keys that should be styled as modifiers
const MODIFIER_KEYS = new Set([
  'LCTL', 'RCTL', 'LSFT', 'RSFT', 'LALT', 'AltGr', 'LGUI', 'RGUI',
  'LCTL', 'Tab', 'TAB', 'ESC', 'ENT', 'BSPC', 'DEL', 'SPC',
  'CAPS', 'INS', 'HOME', 'END', 'PGUP', 'PGDN',
]);

// Keys that are layer switches
function isLayerKey(name) {
  return /^(MO|TG|TO|DF|PDF|LT|TT|OSL)\(/.test(name) ||
         /^LT\d/.test(name);
}

let data = null;
let currentLayer = 0;

async function init() {
  const resp = await fetch('/api/keymap');
  data = await resp.json();
  buildLayerTabs(data.layer_count);
  renderKeyboard();
}

function buildLayerTabs(count) {
  const container = document.getElementById('layer-tabs');
  for (let i = 0; i < count; i++) {
    const tab = document.createElement('div');
    tab.className = 'layer-tab' + (i === 0 ? ' active' : '');
    tab.textContent = i;
    tab.onclick = () => {
      currentLayer = i;
      document.querySelectorAll('.layer-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      renderKeyboard();
    };
    container.appendChild(tab);
  }
}

function renderKeyboard() {
  const container = document.getElementById('keyboard');
  container.innerHTML = '';

  const layout = data.layout;
  const layerData = data.layers[currentLayer];

  // Calculate container size
  let maxX = 0, maxY = 0;
  for (const key of layout) {
    maxX = Math.max(maxX, (key.x + key.w) * UNIT);
    maxY = Math.max(maxY, (key.y + key.h) * UNIT);
  }
  container.style.width = (maxX + 40) + 'px';
  container.style.height = (maxY + 40) + 'px';

  for (const key of layout) {
    const matrixKey = key.row + ',' + key.col;
    const kc = layerData[matrixKey];
    if (!kc) continue;

    const name = kc.name;
    const el = document.createElement('div');
    el.className = 'key';

    // Position and size
    const px = key.x * UNIT;
    const py = key.y * UNIT;
    const pw = key.w * UNIT - GAP;
    const ph = key.h * UNIT - GAP;

    el.style.left = px + 'px';
    el.style.top = py + 'px';
    el.style.width = pw + 'px';
    el.style.height = ph + 'px';

    // Classify key type
    const isTransparent = name === 'TRNS';
    const isEmpty = name === 'KC_NO';

    if (isTransparent) {
      el.classList.add('transparent');
    } else if (isLayerKey(name)) {
      el.classList.add('layer-key');
    } else if (MODIFIER_KEYS.has(name)) {
      el.classList.add('modifier');
    }

    // Build inner content
    const inner = document.createElement('div');
    inner.className = 'key-inner';

    if (isTransparent) {
      const label = document.createElement('span');
      label.className = 'key-label';
      label.textContent = '\u25bd';  // ▽
      inner.appendChild(label);
    } else if (isEmpty) {
      // Show nothing for KC_NO
    } else {
      // Secondary (shift) label
      const shiftChar = SHIFT_LABELS[name];
      if (shiftChar) {
        const sec = document.createElement('span');
        sec.className = 'key-label-secondary';
        sec.textContent = shiftChar;
        inner.appendChild(sec);
      }

      // Main label
      const label = document.createElement('span');
      label.className = 'key-label';

      // Size the text based on name length
      if (name.length > 8) {
        label.classList.add('xsmall');
      } else if (name.length > 5) {
        label.classList.add('small');
      }

      label.textContent = name;
      inner.appendChild(label);
    }

    el.appendChild(inner);
    container.appendChild(el);
  }
}

init();
