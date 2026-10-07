# 🛡️ SolShield · o firewall da carteira

Ferramenta que **intercepta uma transação antes de o usuário assinar**, explica em linguagem simples o que ela faz, dá um **Risk Score (0–100)** com os motivos e **bloqueia** as perigosas. Inclui um dashboard de proteção e um modo de apresentação.

> Este README foi escrito para quem vai **rodar ou continuar o projeto**. Leia de cima para baixo. Cada seção diz o que fazer, o comando exato e o que esperar ver.

---

## 0. Estado atual (leia primeiro)

| Parte | Estado |
|---|---|
| Site publicado | ✅ No ar em https://solshield-seven.vercel.app/ (página e API no mesmo endereço) |
| `index.html` (frontend + dashboard + modo apresentação) | ✅ Testado no navegador |
| `risk_engine.py` com `tx_001`, `tx_002`, `tx_003` | ✅ Funciona, mas são **dados fictícios de demonstração** |
| `api/index.py` + `app.py` (API Flask) | ✅ Testada localmente e na Vercel |
| `solana_rpc.py`: leitura de transação real pela Signature | ✅ Testada na Devnet |
| Transferência protegida (análise antes da assinatura + reputação do destino) | ✅ Testada na Devnet com a Phantom, incluindo a assinatura |
| `denuncias.py`: lista de sanções do OFAC, baixada ao vivo | ✅ Testada (bloqueio com nota 90) |
| Banco de dados | ❌ Não existe. É opcional (seção 7) |

**Regra de ouro para a banca:** o que for demonstração tem que ser apresentado como demonstração. O frontend já avisa na tela ("detalhes ilustrativos", "API offline · modo demonstração"). Não digam que os cenários `tx_001–003` são análises reais.

---

## 1. Estrutura dos arquivos

```
hackathon/
├── index.html        Frontend completo (HTML + CSS + JS num arquivo só)
├── guia.html         Guia para quem nunca usou cripto (abre em /guia)
├── app.py            Roda a API na sua máquina (python app.py)
├── api/
│   └── index.py      A API Flask de verdade (a Vercel usa este arquivo)
├── risk_engine.py    Motor de risco: calcular_risco(id) -> dicionário
├── solana_rpc.py     Consulta a rede Solana: transações reais e reputação de carteiras
├── denuncias.py      Lista de endereços denunciados (OFAC ao vivo + lista do time)
├── tests/            Testes automáticos (python -m unittest discover -s tests)
├── requirements.txt  Dependências Python (Flask, CORS, gunicorn)
├── vercel.json       Configuração do deploy na Vercel
├── .gitignore
└── README.md         Este arquivo
```

Como as peças se conectam:

```
index.html ──fetch──▶  /api/score/<id>  ──▶ api/index.py ──▶ risk_engine.calcular_risco(id)
(navegador)                                                        │
                                                                   ├─ id = tx_001/002/003 → cenários de demonstração
                                                                   └─ id = assinatura real → solana_rpc.analisar() → rede Solana
```

---

## 2. Quem faz o quê

- **Dados e regras de risco:** `risk_engine.py`, `solana_rpc.py` e `denuncias.py` (seções 4 e 6).
- **Backend:** rodar a API local (seção 3) e publicar na Vercel (seção 5).
- **Design:** textos e cores no `index.html` (seção 9 diz onde mexer).
- **Frontend e integração:** `index.html`. Se algo quebrar, o erro aparece no console do navegador (F12 → Console).

### Checklist geral (marquem conforme avançam)

- [ ] Instalar Python e rodar a API local (seção 3)
- [ ] Abrir o `index.html` e ver o indicador **verde** "API conectada"
- [ ] Rodar o **Modo apresentação** e ver os 3 estados
- [ ] Subir o projeto no GitHub (seção 5.1)
- [ ] Publicar na Vercel e testar a URL pública (seção 5)
- [ ] Testar uma transação real da Solana (seção 6)
- [ ] Ensaiar a apresentação duas vezes

---

## 3. Rodar tudo no seu computador

### 3.1 Instalar o Python (uma vez só)
1. Baixe em https://www.python.org/downloads/ (versão 3.10 ou mais nova).
2. No instalador, **marque a caixa "Add python.exe to PATH"** antes de clicar em Install.
3. Feche e abra de novo o VS Code. Teste no terminal:
   ```bash
   python --version
   ```
   Se aparecer "Python was not found", o Python não está no PATH: reinstale marcando a caixa.

### 3.2 Instalar as dependências
No terminal do VS Code, **dentro da pasta do projeto**:
```bash
pip install -r requirements.txt
```

### 3.3 Subir a API
```bash
python app.py
```
Deve aparecer `Running on http://127.0.0.1:5000`. **Deixe este terminal aberto.**

### 3.4 Testar a API
Abra no navegador: http://localhost:5000/api/score/tx_003

Resposta esperada (resumida):
```json
{"status": "Red", "score": 97, "site": "free-airdrop-sol.xyz", "motivos": [ ... ]}
```

### 3.5 Abrir o frontend
Dê dois cliques no `index.html`. O indicador no topo deve mostrar:
- 🟢 **API conectada** → está usando a API real.
- 🟡 **API offline · modo demonstração** → não achou a API (ela não está rodando, ou deu erro). Os cenários de exemplo continuam funcionando, mas **não é a API de verdade**.

Clique em **▶ Modo apresentação** para ver o roteiro completo.

---

## 4. Ligar o motor de risco real (pessoa de dados)

Tudo passa pela função `calcular_risco(id_transacao)` em `risk_engine.py`. Ela recebe o ID digitado e devolve um dicionário. **Só `status` é obrigatório**; o resto melhora a tela:

```python
{
  "status": "Green",            # obrigatório: "Green" | "Yellow" | "Red"
  "score": 8,                   # 0-100, alimenta o medidor e o gráfico
  "site": "jup.ag",
  "acao": "Enviar 0.05 SOL para ...",   # frase simples do que a transação faz
  "permissao": "Transfer(0.05 SOL)",    # instrução técnica
  "taxa": "0.000005 SOL",
  "saldo_antes": 12.40,         # em SOL
  "saldo_depois": 12.35,
  "motivos": [                  # por que o sistema decidiu isso
    {"nivel": "alto", "texto": "Troca o dono da carteira."}   # nivel: alto | medio | baixo | ok
  ]
}
```

- Campos que faltarem aparecem na tela como **"ilustrativos"** (valores de exemplo).
- Se vier só um texto em `reason` (em vez de `motivos`), ele vira um motivo automaticamente.
- `status` aceita qualquer capitalização (`red`, `RED`).
- Para usar o motor real: importe o código dela dentro de `calcular_risco` e devolva o dicionário acima. Não precisa mexer em mais nada.

---

## 5. Publicar na Vercel (site no ar com link público)

A Vercel hospeda o `index.html` **e** roda a API Flask (pasta `api/`) no mesmo endereço. Quando o site está publicado, o frontend usa `/api/score/...` sozinho (não precisa mudar código).

### 5.1 Subir o código para o GitHub
1. Crie um repositório vazio em https://github.com/new (ex.: `solshield`).
2. No terminal, dentro da pasta do projeto:
   ```bash
   git init
   git add .
   git commit -m "SolShield: firewall da carteira"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/solshield.git
   git push -u origin main
   ```

### 5.2 Conectar na Vercel
1. Entre em https://vercel.com com a conta do GitHub.
2. **Add New → Project** → escolha o repositório `solshield` → **Import**.
3. Não precisa mudar nenhuma configuração (Framework Preset: *Other*). Clique **Deploy**.
4. Aguarde ~1 minuto. A Vercel mostra o link, tipo `https://solshield.vercel.app`.

Alternativa sem GitHub (pelo terminal; precisa de Node.js):
```bash
npx vercel
```
Responda as perguntas com Enter. Para publicar de vez: `npx vercel --prod`.

### 5.3 Variáveis de ambiente (só se for usar)
Na Vercel: **Project → Settings → Environment Variables**.

| Nome | Valor | Para quê |
|---|---|---|
| `SOLANA_RPC` | `https://api.devnet.solana.com` (padrão) ou outro | Qual rede Solana consultar |

Depois de adicionar uma variável, é preciso **fazer redeploy** (Deployments → ⋯ → Redeploy).

### 5.4 Testar o site publicado
1. Abra `https://SEU-SITE.vercel.app/api/health` → deve mostrar `{"ok": true}`.
2. Abra `https://SEU-SITE.vercel.app/api/score/tx_003` → deve mostrar o JSON vermelho.
3. Abra `https://SEU-SITE.vercel.app/` → o indicador deve ficar 🟢 **API conectada · seu-site.vercel.app**.

### 5.5 Se a API na Vercel não funcionar (plano B)
Hospede só o frontend na Vercel (ele funciona sozinho) e a API em outro lugar, por exemplo o **Render** (https://render.com, plano gratuito):
1. New → Web Service → conecte o mesmo repositório.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn app:app`
4. Quando estiver no ar, abra o site assim para apontar para essa API:
   `https://SEU-SITE.vercel.app/?api=https://SEU-APP.onrender.com/api/score/`

(O plano gratuito do Render "dorme" depois de um tempo parado: abra a URL da API uns minutos antes da apresentação.)

---

## 6. Solana de verdade (o evento exige Solana/blockchain)

O projeto é feito para a **Solana** e já tem integração real com a rede, em `solana_rpc.py`:

- Quando o ID digitado é uma **assinatura real de transação** (texto com ~88 caracteres), a API busca a transação na rede Solana (RPC público) e analisa as instruções.
- Regras atuais (heurísticas, ajustem se quiserem):
  - Troca de dono/autoridade de conta de token → risco **alto**
  - Aprovação de valor praticamente ilimitado → risco **alto**
  - Envio de mais de 90% do saldo → risco **alto** (acima de 50% → médio)
  - Interação com programas desconhecidos → risco **médio**
- Usa a **devnet** por padrão (rede de testes, sem dinheiro real). Para mainnet, defina `SOLANA_RPC=https://api.mainnet-beta.solana.com`. O RPC público tem limite de requisições; para a demo, uma URL gratuita da Helius (https://www.helius.dev) ou QuickNode é mais estável.

### Como testar com uma transação real
1. Abra https://explorer.solana.com/?cluster=devnet
2. Clique em qualquer transação recente e copie a **Signature** (o texto grande).
3. Cole no campo "ID da transação" do SolShield e clique em **Simular Assinatura**.
4. A tela mostra score, motivos, taxa real e saldo antes/depois dessa transação.

> Testado na Devnet: a leitura de uma transação real pela Signature funcionou no site publicado.

### Transferência protegida: análise ANTES da assinatura
No pop-up, o bloco **"Transferência protegida · Devnet"** faz o fluxo real:
1. Você digita a carteira de destino e o valor em SOL e clica em **Analisar antes de assinar**.
2. O site conecta a Phantom (só para saber o endereço) e chama `/api/prever`.
3. A API consulta a Devnet (`prever()` em `solana_rpc.py`): saldo de quem envia e histórico de quem recebe.
4. Regras sobre o valor: mais de 90% do saldo → +70; mais da metade → +30.
   Regras sobre o destino: na lista de sanções do OFAC ou na lista do time → +80; quem financiou a carteira está na lista → +40; é um programa → +40; nunca usado → +25; criado há menos de 24h → +15; pouco histórico → +10; menos de 7 dias → +5; vocês já transacionaram antes → −15.
5. Se o risco for crítico (70 ou mais), o botão **Assinar** fica travado. Senão, clicar em **Assinar** abre a Phantom e envia a transação de verdade na Devnet.

Precisa abrir o site pelo link (Vercel) ou por `http://localhost:5000/`: a Phantom não funciona em página aberta por dois cliques no arquivo.

> Testado na Devnet com a Phantom real. Depois de clicar em Assinar, confirmem na Phantom em menos de um minuto: a transação tem validade curta e, se vencer, a carteira mostra "Unexpected error".

---

## 7. Banco de dados (opcional)

**Para a demo não precisa.** O dashboard guarda as análises na própria página (zera ao recarregar). Só faz sentido banco se vocês quiserem histórico permanente. Opção mais rápida: **Supabase** (https://supabase.com, plano gratuito).

1. Crie um projeto e, em **SQL Editor**, rode:
   ```sql
   create table analises (
     id bigint generated always as identity primary key,
     criado_em timestamptz default now(),
     tx_id text not null,
     status text not null,
     score int,
     site text,
     motivos jsonb
   );
   ```
2. Em **Project Settings → API**, copie a `URL` e a chave `service_role` (**secreta: nunca coloque no `index.html` nem no GitHub**).
3. Na Vercel, adicione as variáveis `SUPABASE_URL` e `SUPABASE_KEY`.
4. No `api/index.py`, dentro da função `score`, salve cada análise (usa só a biblioteca padrão):
   ```python
   import json, os, urllib.request

   def salvar(tx_id, r):
       url, chave = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
       if not url or not chave:
           return
       corpo = json.dumps({"tx_id": tx_id, "status": r.get("status"), "score": r.get("score"),
                           "site": r.get("site"), "motivos": r.get("motivos")}).encode()
       req = urllib.request.Request(url + "/rest/v1/analises", data=corpo, method="POST",
             headers={"apikey": chave, "Authorization": "Bearer " + chave, "Content-Type": "application/json"})
       try:
           urllib.request.urlopen(req, timeout=5)
       except Exception:
           pass  # nunca derrubar a API por causa do banco
   ```
   E em `score()`: `r = calcular_risco(id_transacao); salvar(id_transacao, r); return jsonify(r)`.

> ⚠️ Não testado. Mostrar o histórico do banco no dashboard exigiria também uma rota de leitura (`GET /rest/v1/analises?order=criado_em.desc`) e alterar o JS. Só façam se sobrar tempo.

---

## 8. Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| Indicador 🟡 "API offline" | A API não está rodando. Rode `python app.py`, veja se o terminal mostra erro, recarregue a página |
| `Python was not found` | Instale o Python marcando "Add to PATH" (seção 3.1) |
| `ModuleNotFoundError: No module named 'flask'` | Rode `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'api'` | Rode `python app.py` **dentro da pasta do projeto** (onde está o `app.py`) |
| `Address already in use` / porta 5000 ocupada | Feche o outro programa ou troque a porta no `app.py` (e a URL no `index.html`) |
| "Failed to fetch" no console, API está rodando | Falta CORS: confira `CORS(app)` no `api/index.py`; ou a API caiu |
| Vercel: erro 404 em `/api/...` | Confira que `vercel.json` e a pasta `api/` foram para o GitHub (`git status`) e faça Redeploy |
| Vercel: `ModuleNotFoundError: risk_engine` | Mova `risk_engine.py` e `solana_rpc.py` para dentro da pasta `api/` e dê push |
| Vercel: erro 500 na API | Vercel → Project → **Logs** mostra o erro Python |
| Transação Solana "não encontrada" | Rede errada: signature da devnet precisa de `SOLANA_RPC` devnet, e da mainnet precisa de mainnet |
| Erro `429` do RPC Solana | Limite do RPC público. Use uma URL gratuita da Helius/QuickNode em `SOLANA_RPC` |
| Alterei o `risk_engine.py` e nada mudou | Pare (Ctrl+C) e rode `python app.py` de novo |

---

## 9. Onde mexer no `index.html`

Tudo está em um arquivo só. Procurem por estes nomes (Ctrl+F):

| O que mudar | Procure por |
|---|---|
| Cores do tema | `:root {` (variáveis `--purple`, `--green`, `--yellow`, `--red`) |
| Textos de cada estado (título e mensagem) | `const TEXTOS` |
| Cenários de exemplo usados quando falta dado da API | `const FIX` |
| Respostas quando a API está offline | `const DEMO` |
| Textos das etapas da análise | `const PASSOS` |
| URL da API | `const API` |
| Roteiro do Modo apresentação | `async function apresentacao` |
| Painel de emergência (vermelho) | `#emergencia` (CSS e HTML) |

---

## 10. Guia para iniciantes (`/guia`)

`guia.html` é uma página única, sem dependências, com o passo a passo para quem nunca usou cripto: instalar a Phantom, ligar o modo de teste, pegar SOL de teste e fazer a transferência protegida.

- No ar: `https://SEU-SITE.vercel.app/guia` (se não abrir, tente `/guia.html`).
- No computador: `http://localhost:5000/guia`.
- O endereço de destino sugerido no passo 4 é a carteira de teste do time. Para trocar, procure `id="endereco"` no `guia.html`.
