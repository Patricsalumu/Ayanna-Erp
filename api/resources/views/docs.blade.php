<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ayanna ERP — Documentation API</title>
    <style>
        :root {
            --primary: #1a56db;
            --primary-dark: #1e40af;
            --accent: #0ea5e9;
            --bg: #f8fafc;
            --sidebar-bg: #1e293b;
            --sidebar-text: #cbd5e1;
            --sidebar-active: #38bdf8;
            --code-bg: #0f172a;
            --code-border: #1e3a5f;
            --text: #1e293b;
            --muted: #64748b;
            --border: #e2e8f0;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
            --tag-get: #10b981;
            --tag-post: #3b82f6;
            --tag-put: #f59e0b;
            --tag-delete: #ef4444;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            display: flex;
            min-height: 100vh;
        }

        /* ── Sidebar ── */
        #sidebar {
            width: 260px;
            min-width: 260px;
            background: var(--sidebar-bg);
            position: fixed;
            top: 0; left: 0; bottom: 0;
            overflow-y: auto;
            z-index: 100;
            display: flex;
            flex-direction: column;
        }

        .sidebar-logo {
            padding: 24px 20px 16px;
            border-bottom: 1px solid #334155;
        }

        .sidebar-logo h1 {
            color: #f1f5f9;
            font-size: 17px;
            font-weight: 700;
            letter-spacing: -0.3px;
        }

        .sidebar-logo span {
            color: var(--sidebar-active);
            font-size: 11px;
            font-weight: 500;
            display: block;
            margin-top: 2px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .sidebar-nav { padding: 12px 0 24px; flex: 1; }

        .nav-group { margin-bottom: 4px; }

        .nav-group-title {
            color: #475569;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            padding: 10px 20px 4px;
        }

        .nav-link {
            display: block;
            color: var(--sidebar-text);
            text-decoration: none;
            padding: 7px 20px 7px 28px;
            font-size: 13px;
            border-left: 2px solid transparent;
            transition: all 0.15s;
            line-height: 1.4;
        }

        .nav-link:hover {
            color: #f1f5f9;
            background: #273548;
            border-left-color: #334155;
        }

        .nav-link.active {
            color: var(--sidebar-active);
            background: #162032;
            border-left-color: var(--sidebar-active);
            font-weight: 500;
        }

        /* ── Main content ── */
        #main {
            margin-left: 260px;
            flex: 1;
            min-width: 0;
        }

        /* Top bar */
        .topbar {
            background: #fff;
            border-bottom: 1px solid var(--border);
            padding: 14px 40px;
            display: flex;
            align-items: center;
            gap: 12px;
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .topbar-badge {
            background: #eff6ff;
            color: var(--primary);
            border: 1px solid #bfdbfe;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .topbar-url {
            font-family: 'Consolas', monospace;
            font-size: 13px;
            color: var(--muted);
            background: var(--bg);
            border: 1px solid var(--border);
            padding: 4px 12px;
            border-radius: 6px;
        }

        .topbar-label {
            font-size: 13px;
            color: var(--muted);
            margin-left: auto;
        }

        /* Content area */
        .content {
            max-width: 860px;
            margin: 0 auto;
            padding: 40px 40px 80px;
        }

        /* Sections */
        .doc-section {
            margin-bottom: 60px;
            scroll-margin-top: 80px;
        }

        .section-title {
            font-size: 22px;
            font-weight: 700;
            color: var(--text);
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .section-title .num {
            background: var(--primary);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 700;
            flex-shrink: 0;
        }

        .subsection-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text);
            margin: 28px 0 12px;
        }

        p { color: #374151; line-height: 1.7; margin-bottom: 14px; }

        /* Callout boxes */
        .callout {
            border-radius: 8px;
            padding: 14px 18px;
            margin: 16px 0;
            border-left: 4px solid;
            font-size: 14px;
            line-height: 1.6;
        }
        .callout.info    { background: #eff6ff; border-color: var(--info); color: #1e40af; }
        .callout.success { background: #f0fdf4; border-color: var(--success); color: #065f46; }
        .callout.warning { background: #fffbeb; border-color: var(--warning); color: #92400e; }
        .callout.danger  { background: #fef2f2; border-color: var(--danger); color: #991b1b; }

        /* HTTP Method tags */
        .method {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            font-family: monospace;
            margin-right: 6px;
        }
        .method.get    { background: #d1fae5; color: #065f46; }
        .method.post   { background: #dbeafe; color: #1e40af; }
        .method.put    { background: #fef3c7; color: #92400e; }
        .method.delete { background: #fee2e2; color: #991b1b; }

        /* Endpoint cards */
        .endpoint {
            background: #fff;
            border: 1px solid var(--border);
            border-radius: 10px;
            margin-bottom: 12px;
            overflow: hidden;
        }

        .endpoint-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 14px 18px;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            background: #f8fafc;
            border-bottom: 1px solid var(--border);
        }

        .endpoint-desc {
            padding: 14px 18px;
            font-size: 13.5px;
            color: #374151;
            line-height: 1.6;
        }

        .endpoint-desc code {
            background: #f1f5f9;
            border: 1px solid var(--border);
            padding: 1px 5px;
            border-radius: 4px;
            font-size: 12px;
            font-family: 'Consolas', monospace;
        }

        /* Code blocks */
        pre {
            background: var(--code-bg);
            border: 1px solid var(--code-border);
            border-radius: 8px;
            padding: 18px 20px;
            overflow-x: auto;
            margin: 14px 0;
            font-size: 13px;
            line-height: 1.6;
        }

        pre code {
            color: #94a3b8;
            font-family: 'Consolas', 'Fira Code', monospace;
            background: none;
            border: none;
            padding: 0;
            font-size: inherit;
        }

        /* JSON syntax highlight helpers */
        .json-key   { color: #7dd3fc; }
        .json-str   { color: #86efac; }
        .json-num   { color: #fbbf24; }
        .json-bool  { color: #f472b6; }
        .json-null  { color: #fb7185; }
        .json-comment { color: #475569; font-style: italic; }
        .http-verb  { color: #f472b6; font-weight: bold; }
        .http-path  { color: #7dd3fc; }
        .http-comment { color: #475569; }
        .py-kw  { color: #c084fc; }
        .py-fn  { color: #60a5fa; }
        .py-str { color: #86efac; }
        .py-comment { color: #475569; font-style: italic; }
        .py-cls { color: #fbbf24; font-weight: bold; }

        /* Tables */
        .table-wrap { overflow-x: auto; margin: 16px 0; }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
        }

        thead th {
            background: #f1f5f9;
            padding: 10px 14px;
            text-align: left;
            font-weight: 600;
            color: #475569;
            border-bottom: 2px solid var(--border);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        tbody td {
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
            line-height: 1.5;
        }

        tbody tr:last-child td { border-bottom: none; }
        tbody tr:hover td { background: #f8fafc; }

        code {
            background: #f1f5f9;
            border: 1px solid var(--border);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            font-family: 'Consolas', monospace;
        }

        /* Status code badges */
        .status {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 700;
            font-family: monospace;
        }
        .status-2xx { background: #d1fae5; color: #065f46; }
        .status-4xx { background: #fee2e2; color: #991b1b; }
        .status-5xx { background: #fce7f3; color: #9d174d; }

        /* Architecture diagram */
        .arch-box {
            background: var(--code-bg);
            border: 1px solid var(--code-border);
            border-radius: 10px;
            padding: 24px;
            margin: 16px 0;
            text-align: center;
        }

        .arch-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0;
            flex-wrap: wrap;
        }

        .arch-node {
            background: #1e3a5f;
            border: 1px solid #2d5fa6;
            border-radius: 8px;
            padding: 14px 20px;
            min-width: 170px;
        }

        .arch-node .node-title {
            color: #7dd3fc;
            font-weight: 700;
            font-size: 14px;
            margin-bottom: 4px;
        }

        .arch-node .node-sub {
            color: #64748b;
            font-size: 12px;
        }

        .arch-arrow {
            color: #38bdf8;
            font-size: 22px;
            padding: 0 16px;
            font-weight: bold;
        }

        .arch-label {
            color: #475569;
            font-size: 12px;
            margin-top: 16px;
            font-family: monospace;
        }

        /* Flow steps */
        .flow {
            background: var(--code-bg);
            border: 1px solid var(--code-border);
            border-radius: 10px;
            padding: 20px 24px;
            margin: 16px 0;
        }

        .flow-step {
            display: flex;
            gap: 14px;
            padding: 10px 0;
            border-bottom: 1px solid #1e3a5f;
            align-items: flex-start;
        }

        .flow-step:last-child { border-bottom: none; }

        .flow-num {
            background: #1e3a5f;
            color: var(--sidebar-active);
            border-radius: 50%;
            width: 26px;
            height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            flex-shrink: 0;
            margin-top: 1px;
        }

        .flow-text {
            color: #94a3b8;
            font-size: 13.5px;
            line-height: 1.6;
        }

        .flow-text strong { color: #cbd5e1; }
        .flow-text code {
            background: #1e3a5f;
            border: none;
            color: #7dd3fc;
            font-size: 12px;
        }

        /* Tag pill */
        .tag {
            display: inline-block;
            padding: 1px 7px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .tag-lock { background: #fef3c7; color: #92400e; }
        .tag-pub  { background: #dcfce7; color: #166534; }

        /* Responsive */
        @media (max-width: 768px) {
            #sidebar { transform: translateX(-260px); }
            #main { margin-left: 0; }
            .content { padding: 24px 20px 60px; }
            .topbar { padding: 12px 20px; }
        }

        /* Scrollbar */
        #sidebar::-webkit-scrollbar { width: 4px; }
        #sidebar::-webkit-scrollbar-track { background: transparent; }
        #sidebar::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }

        hr { border: none; border-top: 1px solid var(--border); margin: 32px 0; }
    </style>
</head>
<body>

<!-- ═══════════════════════════ SIDEBAR ═══════════════════════════ -->
<nav id="sidebar">
    <div class="sidebar-logo">
        <h1>Ayanna ERP</h1>
        <span>API Documentation</span>
    </div>

    <div class="sidebar-nav">
        <div class="nav-group">
            <div class="nav-group-title">Démarrage</div>
            <a class="nav-link" href="#architecture">Architecture</a>
            <a class="nav-link" href="#auth">Authentification</a>
        </div>

        <div class="nav-group">
            <div class="nav-group-title">Communication</div>
            <a class="nav-link" href="#push-crud">Envoyer (CRUD direct)</a>
            <a class="nav-link" href="#push-sync">Envoyer (Sync Push)</a>
            <a class="nav-link" href="#pull-crud">Lire (CRUD direct)</a>
            <a class="nav-link" href="#pull-sync">Lire (Sync Pull)</a>
        </div>

        <div class="nav-group">
            <div class="nav-group-title">Synchronisation</div>
            <a class="nav-link" href="#sync-flow">Flux complet</a>
            <a class="nav-link" href="#sync-tables">Tables supportées</a>
        </div>

        <div class="nav-group">
            <div class="nav-group-title">Exemples Python</div>
            <a class="nav-link" href="#py-client">Classe ApiClient</a>
            <a class="nav-link" href="#py-push">Envoyer des données</a>
            <a class="nav-link" href="#py-pull">Lire des données</a>
            <a class="nav-link" href="#py-full">Cycle complet</a>
        </div>

        <div class="nav-group">
            <div class="nav-group-title">Référence</div>
            <a class="nav-link" href="#ref-core">Core</a>
            <a class="nav-link" href="#ref-compta">Comptabilité</a>
            <a class="nav-link" href="#ref-stock">Achats & Stock</a>
            <a class="nav-link" href="#ref-boutique">Boutique</a>
            <a class="nav-link" href="#ref-restau">Restaurant</a>
            <a class="nav-link" href="#ref-hotel">Hôtel</a>
            <a class="nav-link" href="#ref-event">Salle de Fête</a>
        </div>

        <div class="nav-group">
            <div class="nav-group-title">Références</div>
            <a class="nav-link" href="#errors">Codes d'erreur</a>
            <a class="nav-link" href="#deploy">Déploiement</a>
        </div>
    </div>
</nav>

<!-- ═══════════════════════════ MAIN ═══════════════════════════ -->
<div id="main">
    <div class="topbar">
        <span class="topbar-badge">v1.0</span>
        <span class="topbar-url">{{ config('app.url') }}/api</span>
        <span class="topbar-label">Bearer Token (Sanctum) · JSON · UTF-8</span>
    </div>

    <div class="content">

        <!-- ══════════════════ 1. ARCHITECTURE ══════════════════ -->
        <section class="doc-section" id="architecture">
            <h2 class="section-title"><span class="num">1</span> Architecture générale</h2>

            <div class="arch-box">
                <div class="arch-row">
                    <div class="arch-node">
                        <div class="node-title">App locale</div>
                        <div class="node-sub">Python + SQLite</div>
                        <div class="node-sub">(fonctionne hors-ligne)</div>
                    </div>
                    <div class="arch-arrow">⟺</div>
                    <div class="arch-node">
                        <div class="node-title">Ayanna API</div>
                        <div class="node-sub">Laravel · JSON</div>
                        <div class="node-sub">{{ config('app.url') }}/api</div>
                    </div>
                    <div class="arch-arrow">⟺</div>
                    <div class="arch-node">
                        <div class="node-title">Base centrale</div>
                        <div class="node-sub">MySQL</div>
                        <div class="node-sub">(source de vérité)</div>
                    </div>
                </div>
                <div class="arch-label">HTTP/HTTPS · PUSH/PULL · Last-write-wins</div>
            </div>

            <div class="table-wrap">
                <table>
                    <thead><tr><th>Scénario</th><th>Comportement</th></tr></thead>
                    <tbody>
                        <tr><td>App locale <strong>sans connexion</strong></td><td>Travaille sur SQLite local normalement</td></tr>
                        <tr><td>Connexion disponible</td><td>L'app pousse (<code>push</code>) ses changements locaux</td></tr>
                        <tr><td>Après un push</td><td>L'app tire (<code>pull</code>) les données nouvelles du serveur</td></tr>
                        <tr><td>Conflit</td><td><strong>Le client gagne</strong> — tout conflit est loggé dans <code>sync_audit_logs</code></td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- ══════════════════ 2. AUTH ══════════════════ -->
        <section class="doc-section" id="auth">
            <h2 class="section-title"><span class="num">2</span> Authentification</h2>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method post">POST</span>
                    <span>/api/auth/login</span>
                    <span class="tag tag-pub" style="margin-left:auto">public</span>
                </div>
                <div class="endpoint-desc">Obtenir un token Bearer. À appeler en premier.</div>
            </div>

            <pre><code><span class="json-comment">// Corps de la requête</span>
{
  <span class="json-key">"email"</span>: <span class="json-str">"admin@ayanna.com"</span>,
  <span class="json-key">"password"</span>: <span class="json-str">"secret123"</span>
}

<span class="json-comment">// Réponse 200</span>
{
  <span class="json-key">"user"</span>: {
    <span class="json-key">"id"</span>: <span class="json-str">"550e8400-e29b-41d4-a716-446655440000"</span>,
    <span class="json-key">"name"</span>: <span class="json-str">"Admin"</span>,
    <span class="json-key">"role"</span>: <span class="json-str">"admin"</span>,
    <span class="json-key">"enterprise_id"</span>: <span class="json-str">"..."</span>
  },
  <span class="json-key">"token"</span>: <span class="json-str">"1|abcdefghij1234567890"</span>
}</code></pre>

            <div class="callout info">
                <strong>Stocker ce token.</strong> L'inclure dans <strong>tous</strong> les appels suivants :<br>
                <code>Authorization: Bearer 1|abcdefghij1234567890</code>
            </div>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method post">POST</span>
                    <span>/api/auth/register</span>
                    <span class="tag tag-pub" style="margin-left:auto">public</span>
                </div>
                <div class="endpoint-desc">Créer un compte. Retourne aussi un token.</div>
            </div>

            <pre><code>{
  <span class="json-key">"name"</span>: <span class="json-str">"Jean Dupont"</span>,
  <span class="json-key">"email"</span>: <span class="json-str">"jean@example.com"</span>,
  <span class="json-key">"password"</span>: <span class="json-str">"secret123"</span>,
  <span class="json-key">"password_confirmation"</span>: <span class="json-str">"secret123"</span>,
  <span class="json-key">"enterprise_id"</span>: <span class="json-str">"&lt;uuid&gt;"</span>,
  <span class="json-key">"role"</span>: <span class="json-str">"admin"</span>
}</code></pre>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method post">POST</span>
                    <span>/api/auth/logout</span>
                    <span class="tag tag-lock" style="margin-left:auto">🔒 token requis</span>
                </div>
                <div class="endpoint-desc">Révoquer le token actuel.</div>
            </div>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method get">GET</span>
                    <span>/api/auth/me</span>
                    <span class="tag tag-lock" style="margin-left:auto">🔒 token requis</span>
                </div>
                <div class="endpoint-desc">Retourne l'utilisateur connecté avec son entreprise.</div>
            </div>
        </section>

        <!-- ══════════════════ 3. ENVOYER ══════════════════ -->
        <section class="doc-section" id="push-crud">
            <h2 class="section-title"><span class="num">3</span> Envoyer des données — CRUD direct</h2>

            <p>Pour envoyer des données en temps réel, utiliser les endpoints CRUD standards. Chaque ressource expose quatre opérations.</p>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method post">POST</span>
                    <span>/api/{ressource}</span>
                    <span class="tag tag-lock" style="margin-left:auto">🔒</span>
                </div>
                <div class="endpoint-desc">Créer un enregistrement. Retourne <code>201</code> avec la ressource créée.</div>
            </div>

            <pre><code><span class="http-comment">// Exemple : créer un client boutique</span>
<span class="http-verb">POST</span> <span class="http-path">/api/shop/clients</span>
Authorization: Bearer &lt;token&gt;
Content-Type: application/json

{
  <span class="json-key">"pos_id"</span>: <span class="json-str">"uuid-du-pos"</span>,
  <span class="json-key">"nom"</span>: <span class="json-str">"Marie Kamga"</span>,
  <span class="json-key">"prenom"</span>: <span class="json-str">"Marie"</span>,
  <span class="json-key">"telephone"</span>: <span class="json-str">"+237 6XX XXX XXX"</span>,
  <span class="json-key">"ville"</span>: <span class="json-str">"Douala"</span>,
  <span class="json-key">"type_client"</span>: <span class="json-str">"Particulier"</span>,
  <span class="json-key">"pays"</span>: <span class="json-str">"Cameroun"</span>
}

<span class="json-comment">// Réponse 201</span>
{
  <span class="json-key">"id"</span>: <span class="json-str">"nouveau-uuid"</span>,
  <span class="json-key">"nom"</span>: <span class="json-str">"Marie Kamga"</span>,
  <span class="json-key">"created_at"</span>: <span class="json-str">"2026-05-01T10:00:00.000000Z"</span>
}</code></pre>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method put">PUT</span>
                    <span>/api/{ressource}/{id}</span>
                    <span class="tag tag-lock" style="margin-left:auto">🔒</span>
                </div>
                <div class="endpoint-desc">Modifier. Envoyer uniquement les champs à modifier (patch partiel accepté).</div>
            </div>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method delete">DELETE</span>
                    <span>/api/{ressource}/{id}</span>
                    <span class="tag tag-lock" style="margin-left:auto">🔒</span>
                </div>
                <div class="endpoint-desc">Soft-delete : la ressource n'est pas physiquement supprimée. <code>deleted_at</code> est renseigné.</div>
            </div>
        </section>

        <!-- ══════════════════ 4. SYNC PUSH ══════════════════ -->
        <section class="doc-section" id="push-sync">
            <h2 class="section-title"><span class="num">4</span> Envoyer des données — Sync Push</h2>

            <div class="callout success">
                <strong>Méthode recommandée</strong> pour synchroniser l'app locale. Envoie un lot d'opérations en une seule requête.
            </div>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method post">POST</span>
                    <span>/api/sync/push</span>
                    <span class="tag tag-lock" style="margin-left:auto">🔒</span>
                </div>
                <div class="endpoint-desc">Envoyer un lot d'opérations <code>INSERT</code>, <code>UPDATE</code> ou <code>DELETE</code> en une seule requête.</div>
            </div>

            <pre><code>{
  <span class="json-key">"operations"</span>: [
    {
      <span class="json-key">"table"</span>: <span class="json-str">"shop_clients"</span>,
      <span class="json-key">"operation"</span>: <span class="json-str">"INSERT"</span>,
      <span class="json-key">"data"</span>: {
        <span class="json-key">"id"</span>: <span class="json-str">"uuid-genere-cote-client"</span>,
        <span class="json-key">"pos_id"</span>: <span class="json-str">"uuid-pos"</span>,
        <span class="json-key">"nom"</span>: <span class="json-str">"Marie Kamga"</span>,
        <span class="json-key">"type_client"</span>: <span class="json-str">"Particulier"</span>
      },
      <span class="json-key">"client_updated_at"</span>: <span class="json-str">"2026-05-01T09:45:00Z"</span>
    },
    {
      <span class="json-key">"table"</span>: <span class="json-str">"shop_paniers"</span>,
      <span class="json-key">"operation"</span>: <span class="json-str">"UPDATE"</span>,
      <span class="json-key">"data"</span>: { <span class="json-key">"id"</span>: <span class="json-str">"uuid-panier"</span>, <span class="json-key">"statut"</span>: <span class="json-str">"ferme"</span> },
      <span class="json-key">"client_updated_at"</span>: <span class="json-str">"2026-05-01T09:50:00Z"</span>
    },
    {
      <span class="json-key">"table"</span>: <span class="json-str">"shop_paniers"</span>,
      <span class="json-key">"operation"</span>: <span class="json-str">"DELETE"</span>,
      <span class="json-key">"data"</span>: { <span class="json-key">"id"</span>: <span class="json-str">"uuid-panier-annule"</span> },
      <span class="json-key">"client_updated_at"</span>: <span class="json-str">"2026-05-01T09:52:00Z"</span>
    }
  ]
}</code></pre>

            <h3 class="subsection-title">Champs d'une opération</h3>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Champ</th><th>Type</th><th>Obligatoire</th><th>Description</th></tr></thead>
                    <tbody>
                        <tr><td><code>table</code></td><td>string</td><td>✅</td><td>Nom de la table (voir section Sync)</td></tr>
                        <tr><td><code>operation</code></td><td>string</td><td>✅</td><td><code>INSERT</code>, <code>UPDATE</code> ou <code>DELETE</code></td></tr>
                        <tr><td><code>data</code></td><td>object</td><td>✅</td><td>Données. Le champ <code>id</code> est toujours obligatoire</td></tr>
                        <tr><td><code>client_updated_at</code></td><td>ISO 8601</td><td>✅</td><td>Timestamp de modification côté client</td></tr>
                    </tbody>
                </table>
            </div>

            <h3 class="subsection-title">Réponses</h3>
            <pre><code><span class="json-comment">// 200 — tout succès</span>
{ <span class="json-key">"success"</span>: <span class="json-num">3</span>, <span class="json-key">"errors"</span>: [] }

<span class="json-comment">// 207 — succès partiel</span>
{
  <span class="json-key">"success"</span>: <span class="json-num">2</span>,
  <span class="json-key">"errors"</span>: [
    {
      <span class="json-key">"table"</span>: <span class="json-str">"shop_paniers"</span>,
      <span class="json-key">"id"</span>: <span class="json-str">"uuid-panier-annule"</span>,
      <span class="json-key">"operation"</span>: <span class="json-str">"DELETE"</span>,
      <span class="json-key">"error"</span>: <span class="json-str">"Record not found"</span>
    }
  ]
}</code></pre>

            <div class="callout warning">
                <strong>207 — succès partiel :</strong> les opérations réussies sont commitées même s'il y a des erreurs. Traiter le tableau <code>errors</code> localement avant de retenter.
            </div>
        </section>

        <!-- ══════════════════ 5. LIRE CRUD ══════════════════ -->
        <section class="doc-section" id="pull-crud">
            <h2 class="section-title"><span class="num">5</span> Lire des données — CRUD direct</h2>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method get">GET</span>
                    <span>/api/{ressource}</span>
                    <span class="tag tag-lock" style="margin-left:auto">🔒</span>
                </div>
                <div class="endpoint-desc">Liste paginée. Accepte des filtres en query string.</div>
            </div>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method get">GET</span>
                    <span>/api/{ressource}/{id}</span>
                    <span class="tag tag-lock" style="margin-left:auto">🔒</span>
                </div>
                <div class="endpoint-desc">Un seul enregistrement par UUID.</div>
            </div>

            <pre><code><span class="http-comment">// Exemple : liste des produits filtrée + paginée</span>
<span class="http-verb">GET</span> <span class="http-path">/api/products?enterprise_id=uuid&amp;page=1</span>

<span class="json-comment">// Réponse 200</span>
{
  <span class="json-key">"data"</span>: [
    { <span class="json-key">"id"</span>: <span class="json-str">"..."</span>, <span class="json-key">"name"</span>: <span class="json-str">"Eau minerale"</span>, <span class="json-key">"price_unit"</span>: <span class="json-num">500.00</span> }
  ],
  <span class="json-key">"current_page"</span>: <span class="json-num">1</span>,
  <span class="json-key">"last_page"</span>: <span class="json-num">4</span>,
  <span class="json-key">"total"</span>: <span class="json-num">87</span>
}</code></pre>

            <h3 class="subsection-title">Filtres disponibles</h3>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Paramètre</th><th>Endpoints concernés</th></tr></thead>
                    <tbody>
                        <tr><td><code>enterprise_id</code></td><td>products, product-categories, pos-points…</td></tr>
                        <tr><td><code>pos_id</code></td><td>shop/paniers, restau/paniers, hotel/rooms…</td></tr>
                        <tr><td><code>statut</code></td><td>paniers, reservations…</td></tr>
                        <tr><td><code>warehouse_id</code></td><td>stock/mouvements, stock/produits</td></tr>
                        <tr><td><code>date_from</code> / <code>date_to</code></td><td>compta/journaux, achat/commandes</td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- ══════════════════ 6. SYNC PULL ══════════════════ -->
        <section class="doc-section" id="pull-sync">
            <h2 class="section-title"><span class="num">6</span> Lire des données — Sync Pull</h2>

            <div class="callout success">
                <strong>Méthode recommandée</strong> pour récupérer tous les changements du serveur depuis une date donnée.
            </div>

            <div class="endpoint">
                <div class="endpoint-header">
                    <span class="method get">GET</span>
                    <span>/api/sync/pull?last_sync=2026-05-01T00:00:00Z</span>
                    <span class="tag tag-lock" style="margin-left:auto">🔒</span>
                </div>
                <div class="endpoint-desc">
                    Retourne toutes les tables modifiées depuis <code>last_sync</code>.
                    Omettre <code>last_sync</code> pour une synchronisation complète (premier lancement).
                </div>
            </div>

            <pre><code><span class="json-comment">// Réponse 200</span>
{
  <span class="json-key">"server_time"</span>: <span class="json-str">"2026-05-01T12:00:00+00:00"</span>,
  <span class="json-key">"data"</span>: {
    <span class="json-key">"core_products"</span>: [
      { <span class="json-key">"id"</span>: <span class="json-str">"..."</span>, <span class="json-key">"name"</span>: <span class="json-str">"Eau minerale"</span>, <span class="json-key">"deleted_at"</span>: <span class="json-null">null</span> }
    ],
    <span class="json-key">"shop_paniers"</span>: [
      {
        <span class="json-key">"id"</span>: <span class="json-str">"..."</span>,
        <span class="json-key">"statut"</span>: <span class="json-str">"ferme"</span>,
        <span class="json-key">"deleted_at"</span>: <span class="json-str">"2026-05-01T11:45:00Z"</span>
        <span class="json-comment">// deleted_at non null = supprimer localement</span>
      }
    ]
  }
}</code></pre>

            <div class="callout info">
                Stocker <code>server_time</code> comme nouvelle valeur de <code>last_sync</code> pour le prochain pull. Seules les tables ayant des changements apparaissent dans <code>data</code>.
            </div>
        </section>

        <!-- ══════════════════ 7. SYNC FLOW ══════════════════ -->
        <section class="doc-section" id="sync-flow">
            <h2 class="section-title"><span class="num">7</span> Flux de synchronisation</h2>

            <div class="flow">
                <div class="flow-step">
                    <div class="flow-num">1</div>
                    <div class="flow-text"><strong>Travailler localement</strong> — l'app fonctionne sans connexion sur SQLite</div>
                </div>
                <div class="flow-step">
                    <div class="flow-num">2</div>
                    <div class="flow-text"><strong>Connexion disponible → PUSH</strong><br>
                        <code>POST /api/sync/push</code> — envoyer toutes les modifications locales depuis le dernier push</div>
                </div>
                <div class="flow-step">
                    <div class="flow-num">3</div>
                    <div class="flow-text"><strong>PULL</strong><br>
                        <code>GET /api/sync/pull?last_sync=&lt;timestamp&gt;</code> — récupérer les changements du serveur et les appliquer localement (upsert SQLite)</div>
                </div>
                <div class="flow-step">
                    <div class="flow-num">4</div>
                    <div class="flow-text"><strong>Sauvegarder</strong> <code>server_time</code> reçu comme nouveau <code>last_sync</code></div>
                </div>
                <div class="flow-step">
                    <div class="flow-num">5</div>
                    <div class="flow-text"><strong>Répéter</strong> à chaque reconnexion ou périodiquement</div>
                </div>
            </div>
        </section>

        <!-- ══════════════════ 8. TABLES ══════════════════ -->
        <section class="doc-section" id="sync-tables">
            <h2 class="section-title"><span class="num">8</span> Tables synchronisables</h2>

            <div class="table-wrap">
                <table>
                    <thead><tr><th>Module</th><th>Tables</th></tr></thead>
                    <tbody>
                        <tr><td>Core</td><td><code>core_enterprises</code> <code>core_users</code> <code>modules</code> <code>core_pos_points</code> <code>core_payment_modes</code> <code>core_product_categories</code> <code>core_products</code> <code>pos_product_access</code></td></tr>
                        <tr><td>Comptabilité</td><td><code>compta_classes</code> <code>compta_comptes</code> <code>compta_journaux</code> <code>compta_ecritures</code> <code>compta_config</code></td></tr>
                        <tr><td>Achats/Stock</td><td><code>core_fournisseurs</code> <code>achat_commandes</code> <code>achat_commande_lignes</code> <code>achat_depenses</code> <code>stock_warehouses</code> <code>stock_produits_entrepot</code> <code>stock_mouvements</code> <code>stock_config</code> <code>stock_inventaire</code> <code>stock_inventaire_items</code></td></tr>
                        <tr><td>Boutique</td><td><code>shop_clients</code> <code>shop_services</code> <code>shop_paniers</code> <code>shop_panier_products</code> <code>shop_panier_services</code> <code>shop_payments</code> <code>shop_expenses</code></td></tr>
                        <tr><td>Restaurant</td><td><code>restau_salles</code> <code>restau_tables</code> <code>restau_paniers</code> <code>restau_produit_panier</code> <code>restau_payments</code> <code>restau_expenses</code> <code>restau_printed_invoices</code></td></tr>
                        <tr><td>Hôtel</td><td><code>hotel_categories</code> <code>hotel_rooms</code> <code>hotel_reservations</code> <code>hotel_payments</code></td></tr>
                        <tr><td>Salle de Fête</td><td><code>event_clients</code> <code>event_services</code> <code>event_products</code> <code>event_reservations</code> <code>event_reservation_services</code> <code>event_reservation_products</code> <code>event_payments</code> <code>event_stock_movements</code></td></tr>
                        <tr><td>Licences</td><td><code>licences</code></td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- ══════════════════ 9. PYTHON ══════════════════ -->
        <section class="doc-section" id="py-client">
            <h2 class="section-title"><span class="num">9</span> Exemples Python — Classe ApiClient</h2>

            <pre><code><span class="py-comment"># ayanna_erp/utils/api_client.py</span>
<span class="py-kw">import</span> requests
<span class="py-kw">from</span> datetime <span class="py-kw">import</span> datetime, timezone

<span class="py-kw">class</span> <span class="py-cls">AyannaApiClient</span>:
    <span class="py-kw">def</span> <span class="py-fn">__init__</span>(self, base_url: str, token: str = <span class="py-kw">None</span>):
        self.base_url = base_url.rstrip(<span class="py-str">'/'</span>)
        self.token = token
        self.session = requests.Session()

    <span class="py-kw">def</span> <span class="py-fn">_headers</span>(self):
        h = {<span class="py-str">'Content-Type'</span>: <span class="py-str">'application/json'</span>, <span class="py-str">'Accept'</span>: <span class="py-str">'application/json'</span>}
        <span class="py-kw">if</span> self.token:
            h[<span class="py-str">'Authorization'</span>] = <span class="py-str">f'Bearer {self.token}'</span>
        <span class="py-kw">return</span> h

    <span class="py-kw">def</span> <span class="py-fn">login</span>(self, email: str, password: str) -> str:
        <span class="py-str">"""Retourne le token. Leve une exception si echec."""</span>
        resp = self.session.post(
            <span class="py-str">f'{self.base_url}/api/auth/login'</span>,
            json={<span class="py-str">'email'</span>: email, <span class="py-str">'password'</span>: password},
        )
        resp.raise_for_status()
        self.token = resp.json()[<span class="py-str">'token'</span>]
        <span class="py-kw">return</span> self.token

    <span class="py-kw">def</span> <span class="py-fn">push</span>(self, operations: list) -> dict:
        <span class="py-str">"""Envoie un lot d'operations. Retourne {success, errors}."""</span>
        resp = self.session.post(
            <span class="py-str">f'{self.base_url}/api/sync/push'</span>,
            json={<span class="py-str">'operations'</span>: operations},
            headers=self._headers()
        )
        resp.raise_for_status()
        <span class="py-kw">return</span> resp.json()

    <span class="py-kw">def</span> <span class="py-fn">pull</span>(self, last_sync: str = <span class="py-kw">None</span>) -> dict:
        <span class="py-str">"""Recupere les changements depuis last_sync (ISO 8601)."""</span>
        params = {}
        <span class="py-kw">if</span> last_sync:
            params[<span class="py-str">'last_sync'</span>] = last_sync
        resp = self.session.get(
            <span class="py-str">f'{self.base_url}/api/sync/pull'</span>,
            params=params,
            headers=self._headers()
        )
        resp.raise_for_status()
        <span class="py-kw">return</span> resp.json()</code></pre>
        </section>

        <section class="doc-section" id="py-push">
            <h2 class="section-title"><span class="num">10</span> Exemples Python — Envoyer des données</h2>

            <pre><code><span class="py-kw">import</span> uuid
<span class="py-kw">from</span> datetime <span class="py-kw">import</span> datetime, timezone

client = <span class="py-cls">AyannaApiClient</span>(<span class="py-str">'http://votre-serveur'</span>)
client.login(<span class="py-str">'admin@ayanna.com'</span>, <span class="py-str">'secret123'</span>)

now = datetime.now(timezone.utc).isoformat()

operations = [
    {
        <span class="py-str">'table'</span>: <span class="py-str">'shop_clients'</span>,
        <span class="py-str">'operation'</span>: <span class="py-str">'INSERT'</span>,
        <span class="py-str">'data'</span>: {
            <span class="py-str">'id'</span>: str(uuid.uuid4()),    <span class="py-comment"># UUID genere cote client</span>
            <span class="py-str">'pos_id'</span>: <span class="py-str">'uuid-du-pos'</span>,
            <span class="py-str">'nom'</span>: <span class="py-str">'Marie Kamga'</span>,
            <span class="py-str">'telephone'</span>: <span class="py-str">'+237 6XX XXX XXX'</span>,
            <span class="py-str">'type_client'</span>: <span class="py-str">'Particulier'</span>,
            <span class="py-str">'pays'</span>: <span class="py-str">'Cameroun'</span>,
            <span class="py-str">'is_active'</span>: <span class="py-bool">True</span>,
        },
        <span class="py-str">'client_updated_at'</span>: now,
    },
]

result = client.push(operations)
<span class="py-fn">print</span>(<span class="py-str">f"Succes: {result['success']}, Erreurs: {len(result['errors'])}"</span>)

<span class="py-kw">for</span> err <span class="py-kw">in</span> result[<span class="py-str">'errors'</span>]:
    <span class="py-fn">print</span>(<span class="py-str">f"  ERREUR {err['table']} [{err['id']}] -- {err['error']}"</span>)</code></pre>
        </section>

        <section class="doc-section" id="py-pull">
            <h2 class="section-title"><span class="num">11</span> Exemples Python — Lire des données</h2>

            <pre><code><span class="py-kw">from</span> sqlalchemy <span class="py-kw">import</span> text

<span class="py-kw">def</span> <span class="py-fn">sync_depuis_serveur</span>(db_session, api_client, last_sync: str):
    result = api_client.pull(last_sync=last_sync)
    server_time = result[<span class="py-str">'server_time'</span>]
    data = result.get(<span class="py-str">'data'</span>, {})

    <span class="py-kw">for</span> table_name, records <span class="py-kw">in</span> data.items():
        <span class="py-kw">for</span> record <span class="py-kw">in</span> records:
            <span class="py-kw">if</span> record.get(<span class="py-str">'deleted_at'</span>):
                <span class="py-comment"># Supprimer localement</span>
                db_session.execute(
                    text(<span class="py-str">f"DELETE FROM {table_name} WHERE id = :id"</span>),
                    {<span class="py-str">'id'</span>: record[<span class="py-str">'id'</span>]}
                )
            <span class="py-kw">else</span>:
                <span class="py-comment"># Upsert SQLite</span>
                cols = list(record.keys())
                placeholders = <span class="py-str">', '</span>.join([<span class="py-str">f':{c}'</span> <span class="py-kw">for</span> c <span class="py-kw">in</span> cols])
                updates = <span class="py-str">', '</span>.join([<span class="py-str">f'{c} = :{c}'</span> <span class="py-kw">for</span> c <span class="py-kw">in</span> cols <span class="py-kw">if</span> c != <span class="py-str">'id'</span>])
                db_session.execute(
                    text(<span class="py-str">f"""
                        INSERT INTO {table_name} ({', '.join(cols)})
                        VALUES ({placeholders})
                        ON CONFLICT(id) DO UPDATE SET {updates}
                    """</span>),
                    record
                )

    db_session.commit()
    <span class="py-kw">return</span> server_time  <span class="py-comment"># Stocker comme nouveau last_sync</span></code></pre>
        </section>

        <section class="doc-section" id="py-full">
            <h2 class="section-title"><span class="num">12</span> Exemples Python — Cycle complet</h2>

            <pre><code><span class="py-kw">def</span> <span class="py-fn">synchroniser</span>(db_session, base_url, email, password, last_sync_file=<span class="py-str">'last_sync.txt'</span>):
    <span class="py-str">"""Cycle complet : login -> push -> pull."""</span>

    client = <span class="py-cls">AyannaApiClient</span>(base_url)
    <span class="py-kw">try</span>:
        client.login(email, password)
    <span class="py-kw">except</span> Exception <span class="py-kw">as</span> e:
        <span class="py-fn">print</span>(<span class="py-str">f"Connexion impossible: {e}"</span>)
        <span class="py-kw">return</span>

    <span class="py-comment"># Push des modifications locales</span>
    operations = get_pending_local_operations(db_session)
    <span class="py-kw">if</span> operations:
        result = client.push(operations)
        <span class="py-fn">print</span>(<span class="py-str">f"Push: {result['success']} envoyes, {len(result['errors'])} erreurs"</span>)
        mark_operations_synced(db_session, operations, result[<span class="py-str">'errors'</span>])

    <span class="py-comment"># Pull des changements serveur</span>
    <span class="py-kw">try</span>:
        <span class="py-kw">with</span> <span class="py-fn">open</span>(last_sync_file) <span class="py-kw">as</span> f:
            last_sync = f.read().strip()
    <span class="py-kw">except</span> FileNotFoundError:
        last_sync = <span class="py-kw">None</span>  <span class="py-comment"># sync complete au premier run</span>

    new_last_sync = sync_depuis_serveur(db_session, client, last_sync)

    <span class="py-kw">with</span> <span class="py-fn">open</span>(last_sync_file, <span class="py-str">'w'</span>) <span class="py-kw">as</span> f:
        f.write(new_last_sync)

    <span class="py-fn">print</span>(<span class="py-str">f"Sync terminee. Prochain last_sync: {new_last_sync}"</span>)</code></pre>
        </section>

        <!-- ══════════════════ RÉFÉRENCE ══════════════════ -->
        <section class="doc-section" id="ref-core">
            <h2 class="section-title"><span class="num">13</span> Référence — Core</h2>
            <div class="callout info">Toutes les routes ci-dessous nécessitent <code>Authorization: Bearer &lt;token&gt;</code>. Format CRUD complet : GET / GET/{id} / POST / PUT/{id} / DELETE/{id}.</div>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Ressource</th><th>Endpoint</th><th>Champs principaux</th></tr></thead>
                    <tbody>
                        <tr><td>Entreprises</td><td><code>/api/entreprises</code></td><td><code>nom</code> <code>adresse</code> <code>telephone</code> <code>email</code> <code>devise</code> <code>pays</code> <code>secteur</code></td></tr>
                        <tr><td>Utilisateurs</td><td><code>/api/users</code></td><td><code>name</code> <code>email</code> <code>password</code> <code>enterprise_id</code> <code>pos_id</code> <code>role</code></td></tr>
                        <tr><td>Points de vente</td><td><code>/api/pos-points</code></td><td><code>enterprise_id</code> <code>nom</code> <code>type</code> (boutique|restaurant|hotel|salle_fete) <code>actif</code></td></tr>
                        <tr><td>Catégories produits</td><td><code>/api/product-categories</code></td><td><code>enterprise_id</code> <code>name</code> <code>description</code> <code>parent_id</code> <code>is_active</code></td></tr>
                        <tr><td>Produits</td><td><code>/api/products</code></td><td><code>enterprise_id</code> <code>category_id</code> <code>code</code> <code>name</code> <code>barcode</code> <code>cost</code> <code>price_unit</code> <code>unit</code> <code>is_active</code></td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <section class="doc-section" id="ref-compta">
            <h2 class="section-title"><span class="num">14</span> Référence — Comptabilité</h2>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Ressource</th><th>Endpoint</th><th>Champs principaux</th></tr></thead>
                    <tbody>
                        <tr><td>Classes</td><td><code>/api/compta/classes</code></td><td><code>code</code> <code>nom</code> <code>type</code> <code>document</code> <code>enterprise_id</code></td></tr>
                        <tr><td>Comptes</td><td><code>/api/compta/comptes</code></td><td><code>numero</code> <code>nom</code> <code>libelle</code> <code>actif</code> <code>classe_comptable_id</code></td></tr>
                        <tr><td>Journaux</td><td><code>/api/compta/journaux</code></td><td><code>date_operation</code> <code>libelle</code> <code>montant</code> <code>type_operation</code> <code>enterprise_id</code><br>Filtres : <code>?enterprise_id=&date_from=&date_to=</code></td></tr>
                        <tr><td>Config</td><td><code>/api/compta/config</code></td><td>GET/{id} · GET/pos/{pos_id} · POST · PUT/{id}</td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <section class="doc-section" id="ref-stock">
            <h2 class="section-title"><span class="num">15</span> Référence — Achats & Stock</h2>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Ressource</th><th>Endpoint</th><th>Champs principaux</th></tr></thead>
                    <tbody>
                        <tr><td>Fournisseurs</td><td><code>/api/fournisseurs</code></td><td><code>nom</code> <code>telephone</code> <code>adresse</code> <code>email</code></td></tr>
                        <tr><td>Commandes achat</td><td><code>/api/achat/commandes</code></td><td><code>numero</code> <code>fournisseur_id</code> <code>entrepot_id</code> <code>date_commande</code> <code>montant_total</code> <code>etat</code></td></tr>
                        <tr><td>Entrepôts</td><td><code>/api/stock/warehouses</code></td><td><code>entreprise_id</code> <code>code</code> <code>name</code> <code>type</code> <code>is_default</code></td></tr>
                        <tr><td>Stock produits</td><td><code>/api/stock/produits</code></td><td><code>product_id</code> <code>warehouse_id</code> <code>quantity</code> <code>reserved_quantity</code> <code>unit_cost</code></td></tr>
                        <tr><td>Mouvements <em>(pas de PUT)</em></td><td><code>/api/stock/mouvements</code></td><td><code>product_id</code> <code>warehouse_id</code> <code>type_mouvement</code> <code>quantity</code> <code>date_mouvement</code></td></tr>
                        <tr><td>Inventaires</td><td><code>/api/stock/inventaires</code></td><td><code>warehouse_id</code> <code>reference</code> <code>date_inventaire</code> <code>statut</code></td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <section class="doc-section" id="ref-boutique">
            <h2 class="section-title"><span class="num">16</span> Référence — Boutique</h2>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Ressource</th><th>Endpoint</th><th>Champs principaux</th></tr></thead>
                    <tbody>
                        <tr><td>Clients</td><td><code>/api/shop/clients</code></td><td><code>pos_id</code> <code>nom</code> <code>prenom</code> <code>telephone</code> <code>email</code> <code>adresse</code> <code>ville</code> <code>pays</code> <code>type_client</code> <code>credit_limit</code> <code>balance</code> <code>carte_identite</code> <code>type_carte</code> <code>is_active</code></td></tr>
                        <tr><td>Paniers/Ventes</td><td><code>/api/shop/paniers</code></td><td><code>pos_id</code> <code>client_id</code> <code>montant_total</code> <code>montant_paye</code> <code>remise</code> <code>statut</code> <code>date_vente</code><br>Filtres : <code>?pos_id=&statut=</code></td></tr>
                        <tr><td>Dépenses</td><td><code>/api/shop/depenses</code></td><td><code>pos_id</code> <code>user_id</code> <code>libelle</code> <code>montant</code> <code>date_depense</code></td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <section class="doc-section" id="ref-restau">
            <h2 class="section-title"><span class="num">17</span> Référence — Restaurant</h2>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Ressource</th><th>Endpoint</th></tr></thead>
                    <tbody>
                        <tr><td>Salles</td><td><code>/api/restau/salles</code></td></tr>
                        <tr><td>Tables</td><td><code>/api/restau/tables</code></td></tr>
                        <tr><td>Paniers/Commandes</td><td><code>/api/restau/paniers</code> — Filtres : <code>?pos_id=&statut=</code></td></tr>
                        <tr><td>Dépenses</td><td><code>/api/restau/depenses</code></td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <section class="doc-section" id="ref-hotel">
            <h2 class="section-title"><span class="num">18</span> Référence — Hôtel</h2>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Ressource</th><th>Endpoint</th></tr></thead>
                    <tbody>
                        <tr><td>Catégories chambres</td><td><code>/api/hotel/categories</code></td></tr>
                        <tr><td>Chambres</td><td><code>/api/hotel/rooms</code> — Filtres : <code>?pos_id=&statut=</code></td></tr>
                        <tr><td>Réservations</td><td><code>/api/hotel/reservations</code> — Filtres : <code>?pos_id=&statut=</code></td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <section class="doc-section" id="ref-event">
            <h2 class="section-title"><span class="num">19</span> Référence — Salle de Fête</h2>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Ressource</th><th>Endpoint</th></tr></thead>
                    <tbody>
                        <tr><td>Clients</td><td><code>/api/event/clients</code></td></tr>
                        <tr><td>Services</td><td><code>/api/event/services</code></td></tr>
                        <tr><td>Réservations</td><td><code>/api/event/reservations</code> — Filtres : <code>?pos_id=&statut=</code></td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- ══════════════════ ERREURS ══════════════════ -->
        <section class="doc-section" id="errors">
            <h2 class="section-title"><span class="num">20</span> Codes d'erreur</h2>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Code HTTP</th><th>Signification</th><th>Action recommandée</th></tr></thead>
                    <tbody>
                        <tr><td><span class="status status-2xx">200</span></td><td>Succès</td><td>—</td></tr>
                        <tr><td><span class="status status-2xx">201</span></td><td>Créé</td><td>—</td></tr>
                        <tr><td><span class="status status-2xx">207</span></td><td>Multi-status (sync partielle)</td><td>Traiter le tableau <code>errors</code></td></tr>
                        <tr><td><span class="status status-4xx">401</span></td><td>Token absent ou invalide</td><td>Re-authentifier</td></tr>
                        <tr><td><span class="status status-4xx">403</span></td><td>Accès refusé</td><td>Vérifier les droits du rôle</td></tr>
                        <tr><td><span class="status status-4xx">404</span></td><td>Ressource introuvable</td><td>Vérifier l'UUID</td></tr>
                        <tr><td><span class="status status-4xx">422</span></td><td>Erreur de validation</td><td>Lire le champ <code>errors</code></td></tr>
                        <tr><td><span class="status status-5xx">500</span></td><td>Erreur serveur</td><td>Contacter l'admin</td></tr>
                    </tbody>
                </table>
            </div>

            <pre><code><span class="json-comment">// Format erreur 422</span>
{
  <span class="json-key">"message"</span>: <span class="json-str">"The nom field is required."</span>,
  <span class="json-key">"errors"</span>: {
    <span class="json-key">"nom"</span>: [<span class="json-str">"The nom field is required."</span>]
  }
}</code></pre>
        </section>

        <!-- ══════════════════ DEPLOY ══════════════════ -->
        <section class="doc-section" id="deploy">
            <h2 class="section-title"><span class="num">21</span> Déploiement & configuration</h2>

            <pre><code><span class="http-comment"># 1. Installer les dépendances</span>
cd api
composer install

<span class="http-comment"># 2. Configurer .env</span>
cp .env.example .env
php artisan key:generate

<span class="http-comment"># Paramètres DB dans .env :</span>
<span class="http-comment"># DB_CONNECTION=mysql</span>
<span class="http-comment"># DB_HOST=127.0.0.1</span>
<span class="http-comment"># DB_DATABASE=ayanna_erp</span>
<span class="http-comment"># DB_USERNAME=root</span>
<span class="http-comment"># DB_PASSWORD=</span>

<span class="http-comment"># 3. Créer la base</span>
mysql -u root -e "CREATE DATABASE IF NOT EXISTS ayanna_erp CHARACTER SET utf8mb4;"

<span class="http-comment"># 4. Migrations</span>
php artisan migrate

<span class="http-comment"># 5. Démarrer</span>
php artisan serve --port=8000</code></pre>

            <div class="callout success">
                <strong>Première utilisation :</strong><br>
                1. <code>POST /api/auth/register</code> → créer le premier compte admin<br>
                2. Récupérer le token dans la réponse<br>
                3. Premier sync pull <em>(sans last_sync)</em> pour charger toutes les données
            </div>

            <div class="callout warning">
                <strong>Production :</strong> HTTPS obligatoire. Utiliser Nginx/Apache + PHP-FPM. Configurer <code>APP_URL</code> et <code>SANCTUM_STATEFUL_DOMAINS</code> dans <code>.env</code>.
            </div>
        </section>

    </div><!-- /content -->
</div><!-- /main -->

<script>
    // Active nav link on scroll
    const sections = document.querySelectorAll('.doc-section');
    const navLinks = document.querySelectorAll('.nav-link');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                navLinks.forEach(l => l.classList.remove('active'));
                const id = entry.target.getAttribute('id');
                const active = document.querySelector(`.nav-link[href="#${id}"]`);
                if (active) active.classList.add('active');
            }
        });
    }, { rootMargin: '-20% 0px -70% 0px' });

    sections.forEach(s => observer.observe(s));
</script>
</body>
</html>
