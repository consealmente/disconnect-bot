const el = id => document.getElementById(id);
if (location.hostname === 'disconnect-bot.vercel.app') {
  location.replace('https://disconnect-bot-death16.vercel.app/' + location.hash);
} else {
  startEditor();
}

function startEditor() {
  const draftKey = 'voice-control.local-draft.v1';
  function getDraft() {
    try {
      const draft = JSON.parse(localStorage.getItem(draftKey));
      if (typeof draft?.trigger === 'string' && typeof draft?.targets === 'string') return draft;
    } catch {}
  }
  function displayDraft(draft) {
    el('trigger').value = draft.trigger;
    el('targets').value = draft.targets;
    counts();
  }
  const params = new URLSearchParams(location.hash.slice(1));
  const app = params.get('app'), session = params.get('session');
  history.replaceState(null, '', location.pathname);
  const ids = () => [...new Set(el('targets').value.trim().split(/[\s,]+/).filter(Boolean))];
  const status = msg => { el('status').textContent = msg; };
  const counts = () => { el('count').textContent = ids().length + ' / 75'; };
  el('targets').addEventListener('input', counts);
  function lock(value) {
    for (const id of ['save','off','trigger','targets']) el(id).disabled = value;
  }
  async function call(action, data = {}) {
    const response = await fetch('/api/session',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({app,session,action,...data})});
    const result = await response.json();
    if (!response.ok) throw Error(result.error || 'Request failed.');
    return result;
  }
  async function refresh() {
    lock(true);
    try {
      const rule = await call('read');
      if (rule.state === 'pending') {
        status('Waiting for the bot to apply your change…');
        setTimeout(refresh, 2500);
      } else if (rule.state === 'done') status(rule.message);
      else if (rule.state === 'open') {
        el('trigger').value = rule.trigger;
        el('targets').value = rule.targets.join('\n');
        counts(); lock(false);
        status('Connected to your private Discord session.');
        const draft = getDraft();
        if (draft && !el('use-draft')) {
          const button = document.createElement('button');
          button.type = 'button';
          button.id = 'use-draft';
          button.textContent = 'Use my draft';
          button.onclick = () => {
            displayDraft(draft);
            button.remove();
            status('Draft loaded. Choose Save rule to apply it to this server.');
          };
          el('status').after(button);
        }
      }
    } catch (err) { status(err.message); }
  }
  async function submit(targets) {
    lock(true);
    try {
      await call('save',{trigger:el('trigger').value.trim(),targets});
      await refresh();
    } catch (err) { status(err.message); lock(false); }
  }
  document.querySelector('form').onsubmit = event => {
    event.preventDefault();
    if (!ids().length) return status('Enter at least one target ID.');
    if (!app || !session) {
      try {
        localStorage.setItem(draftKey, JSON.stringify({trigger:el('trigger').value, targets:el('targets').value}));
        status('Draft saved in this browser. Run /dashboard in Discord, open the private link in this browser, then choose Use my draft.');
      } catch { status('Browser storage is unavailable. Copy your IDs before opening /dashboard.'); }
      return;
    }
    submit(ids());
  };
  el('off').onclick = () => { if (confirm('Disable this server’s disconnect rule?')) submit([]); };
  lock(true);
  if (app && session) {
    refresh();
  } else {
    lock(false);
    el('off').hidden = true;
    el('save').textContent = 'Save draft';
    const draft = getDraft();
    if (draft) displayDraft(draft);
    status('Enter IDs and save a draft on this device. Use /dashboard in Discord to apply it to your server.');
  }
}
