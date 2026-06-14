# Sintonia — Site institucional (Cloudflare Pages)

Site estático, leve e responsivo para a plataforma de interoperabilidade em saúde.
Sem build, sem framework — HTML + CSS + um JS mínimo. Pronto para o **Cloudflare Pages**.

## 📁 Estrutura
```
landing/
├── index.html              # Home (página de vendas)
├── solucao.html            # A Solução
├── sobre.html              # Sobre
├── 404.html                # Página de erro
├── robots.txt              # Crawlers (inclui GPTBot, PerplexityBot, ClaudeBot)
├── sitemap.xml             # Mapa do site
├── llms.txt                # Padrão para LLMs / GEO
├── manifest.webmanifest    # PWA
├── favicon.svg
├── _headers                # Segurança (HSTS, CSP) + cache (Cloudflare)
├── _redirects              # Redirects amigáveis (Cloudflare)
└── assets/
    ├── css/styles.css
    └── js/main.js
```

## 🚀 Deploy no Cloudflare Pages
1. **Git**: faça push deste repositório. No painel Cloudflare → *Workers & Pages* → *Create application* → *Pages* → *Connect to Git*.
2. **Build settings**:
   - Framework preset: **None**
   - Build command: *(vazio)*
   - **Build output directory: `landing`**
3. Salve e publique. A URL inicial será `https://<projeto>.pages.dev`.
4. **Domínio custom**: *Custom domains* → adicione `sintoniasaude.com.br` e `www`. O HTTPS/SSL é automático.
5. **WWW vs apex**: defina um canônico (recomendado `www`) e crie uma *Redirect Rule* do apex para o `www` (ou vice-versa). Atualize os `<link rel="canonical">` se mudar.

> Alternativa rápida sem Git: `npx wrangler pages deploy landing` (Wrangler CLI).

## 🏷️ Trocar o nome da marca
O nome **"Sintonia"** e o domínio `www.sintoniasaude.com.br` aparecem nos arquivos. Para renomear:
1. Substitua `Sintonia` / `Sinton<b>ia</b>` nos `.html`.
2. Substitua `www.sintoniasaude.com.br` em todos os `canonical`, OG, `sitemap.xml`, `robots.txt`, `llms.txt`.
3. Ajuste o e-mail `contato@sintoniasaude.com.br`.
4. (Opcional) atualize as cores no `:root` de `assets/css/styles.css`.

## 🖼️ Imagens (banco gratuito)
As fotos usam **Unsplash** via URL otimizada (`images.unsplash.com/...?auto=format&fit=crop&w=&q=70`), com fundo na cor da marca como *fallback*. Para trocar por outras (Unsplash/Pexels — uso livre):
- Busque termos como: `doctor tablet`, `telemedicine`, `hospital team`, `medical data dashboard`.
- Baixe e coloque em `assets/img/` e troque o `src` (melhor para performance/privacidade), **ou** cole a URL direta do Unsplash.
- Mantenha `width`/`height` e `alt` descritivo (SEO + acessibilidade).
- **OG image**: para compartilhamento perfeito, exporte uma imagem 1200×630 e aponte `og:image` para um arquivo local.

## 📱 WhatsApp
Todos os CTAs usam `https://wa.me/5511911293075` com mensagem pré-preenchida. Para mudar o número, faça find/replace de `5511911293075`.

## ✅ SEO já implementado (on-page + técnico)
- **Title tags** únicas (< 60 caracteres) e **meta descriptions** (< 155) por página, com a palavra-chave alvo.
- **Hierarquia de headings** (um H1 por página, H2/H3 lógicos) e palavra-chave nas primeiras 100 palavras.
- **URLs** limpas, **canonical**, **Open Graph** e **Twitter Cards**.
- **Dados estruturados (JSON-LD)**: `Organization`, `WebSite`, `Service`, `FAQPage`, `BreadcrumbList`.
- **robots.txt** (libera buscadores e crawlers de IA) + **sitemap.xml** + **llms.txt**.
- **HTTPS/HSTS** e **CSP** via `_headers`; **cache** de assets `immutable`.
- **Core Web Vitals**: sem framework, CSS enxuto, JS `defer`, imagens `lazy` com `width/height` (evita CLS), fontes com `preconnect`.
- **Acessibilidade**: HTML semântico, `aria-*`, foco navegável, `prefers-reduced-motion`, contraste cuidado.
- **Mobile-first** responsivo.
- **Links internos** descritivos entre Home ⇄ Solução ⇄ Sobre.

## 🔜 Próximos passos de SEO (off-page / monitoramento)
- Enviar `sitemap.xml` no **Google Search Console** e **Bing Webmaster Tools**.
- Configurar **Google Analytics 4** e **Google Business Profile** (NAP consistente).
- Backlinks: diretórios de health tech, PR, parcerias; reviews em plataformas terceiras.
- GEO: validar `llms.txt`, monitorar menções da marca (Google Alerts) e manter fatos no Wikidata.

---
Feito com a paleta `#CDEDFB · #89C2D9 · #E7F9FF · #EA4D50 · #FFA7A6`.
