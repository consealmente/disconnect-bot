const snowflake = value => typeof value === 'string' && /^[1-9]\d{14,19}$/.test(value) && BigInt(value) < 2n ** 64n;

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'private, no-store');
  if (req.method !== 'POST') return res.status(405).end();
  const { app, session, action, trigger, targets } = req.body || {};
  if (!snowflake(app) || typeof session !== 'string' || !/^[A-Za-z0-9_.-]{20,500}$/.test(session))
    return res.status(400).json({error:'Open your private link from /dashboard.'});
  const url = 'https://discord.com/api/v10/webhooks/' + app + '/' + session + '/messages/@original';
  try {
    const current = await fetch(url);
    if (!current.ok) return res.status(current.status).json({error:current.status === 429 ? 'Discord is busy. Try again shortly.' : 'Session unavailable. Run /dashboard again.'});
    const rule = JSON.parse((await current.json()).content);
    if (action === 'read') return res.json(rule);
    if (action !== 'save' || rule.state !== 'open') return res.status(409).json({error:'Open a new dashboard session.'});
    if (!Array.isArray(targets) || targets.length > 75 || !targets.every(snowflake) ||
        (targets.length && (!snowflake(trigger) || targets.includes(trigger))))
      return res.status(400).json({error:'Check the joining ID and target IDs. Choose up to 75 different targets.'});
    const edit = {state:'pending', trigger:targets.length ? trigger : '', targets:[...new Set(targets)]};
    const reply = await fetch(url, {method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:JSON.stringify(edit),allowed_mentions:{parse:[]}})});
    if (!reply.ok) return res.status(502).json({error:'Discord could not accept this change. Try again.'});
    return res.json(edit);
  } catch {
    return res.status(502).json({error:'The dashboard could not read this Discord session.'});
  }
};
