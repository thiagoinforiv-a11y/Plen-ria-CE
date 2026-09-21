# Baixar Vídeo — app web (Flask)

App web de página única, mobile-first, para baixar vídeos do Instagram e
Facebook direto pelo navegador do iPhone: cole o link, toque em **Buscar**
e o app mostra o perfil (@) e a legenda original, com botões para copiar
cada um e para baixar o vídeo em MP4.

- Protegido por senha simples (HTTP Basic Auth), lida da variável de
  ambiente `APP_PASSWORD`.
- Nenhum arquivo fica salvo no servidor depois do download: cada vídeo é
  baixado numa pasta temporária, enviado ao navegador e apagado logo em
  seguida (ou após 10 minutos, se a pessoa nunca clicar em "Baixar vídeo").
- Não tenta contornar captchas ou logins — se a plataforma bloquear o
  acesso, o app mostra uma mensagem clara e um botão para abrir o link
  original.

## Rodando localmente

Requer Python 3.10+ e `ffmpeg` instalado no sistema.

```bash
cd webapp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export APP_PASSWORD=escolha_uma_senha
python app.py
```

Acesse `http://localhost:5000` — o navegador vai pedir usuário (qualquer
valor) e senha (o valor de `APP_PASSWORD`).

Para simular o ambiente de produção (gunicorn):

```bash
export PORT=8000
gunicorn app:app --bind 0.0.0.0:$PORT
```

## Deploy no Render

O app já vem pronto para deploy via Docker (garante que o `ffmpeg` esteja
disponível).

### Opção A — pelo painel do Render (recomendado, só cliques)

1. Acesse [render.com](https://render.com), crie conta e conecte sua conta
   do GitHub.
2. **New** → **Web Service** → selecione o repositório `Plen-ria-CE`.
3. Em **Root Directory**, informe `webapp`.
4. Em **Runtime**, escolha **Docker** (o Render detecta o `Dockerfile`
   automaticamente).
5. Em **Instance Type**, escolha o plano **Free**.
6. Em **Environment Variables**, adicione:
   - `APP_PASSWORD` = a senha que você quer usar
7. Clique em **Create Web Service** e aguarde o build.

### Opção B — Blueprint (`render.yaml`)

O repositório inclui um `render.yaml` na raiz. No painel do Render, use
**New** → **Blueprint**, aponte para o repositório, e o Render lê o
`render.yaml` automaticamente (ele já aponta para `webapp/` e usa Docker).
Você só precisa preencher o valor de `APP_PASSWORD` quando solicitado.

### Sobre a porta

O Render injeta a variável `PORT` automaticamente — o `Dockerfile` já usa
`gunicorn app:app --bind 0.0.0.0:${PORT:-10000}`, então não é preciso
configurar nada manualmente.

### Sobre o plano gratuito

No plano Free do Render, o serviço "dorme" depois de um tempo sem uso e
leva alguns segundos para acordar na primeira requisição seguinte — normal
para esse tipo de uso pessoal.

## Autenticação no Instagram

O Instagram costuma bloquear downloads anônimos vindos de servidores/nuvem
(como o Render), mesmo em posts públicos. Para contornar isso, o app pode
autenticar o yt-dlp com uma conta do Instagram.

**Recomendação:** use uma conta secundária, não a sua principal, já que
logins automatizados a partir de um servidor podem levar o Instagram a
sinalizar a conta.

### Opção A — usuário e senha (mais simples)

No painel do serviço no Render, vá em **Environment** e adicione:

- KEY: `INSTAGRAM_USERNAME` / VALUE: o usuário do Instagram
- KEY: `INSTAGRAM_PASSWORD` / VALUE: a senha

Salve — o Render faz um novo deploy automaticamente. O yt-dlp faz login
automaticamente na primeira requisição e reaproveita a sessão nas
seguintes (evitando logins repetidos), enquanto o serviço continuar no ar.

### Opção B — cookies exportados

Se preferir não guardar a senha no Render, é possível usar cookies de uma
sessão já logada em vez disso, através da variável `INSTAGRAM_COOKIES`
(conteúdo no formato Netscape). Na prática, exportar cookies pelo iPhone
esbarra numa limitação conhecida das extensões Safari no iOS (não
conseguem ler cookies de sessão) — esse caminho funciona melhor exportando
de um navegador de computador (Chrome/Firefox com a extensão "Get
cookies.txt LOCALLY", por exemplo), se você tiver acesso a um em algum
momento.

Os cookies (de qualquer uma das opções) expiram de tempos em tempos; se o
app voltar a falhar depois de um tempo, repita o processo.

## Estrutura

```
webapp/
  app.py           # rotas Flask (login, busca, download)
  downloader.py    # download do vídeo e extração de legenda/autor via yt-dlp
  templates/
    index.html     # página única (HTML + CSS + JS inline)
  requirements.txt
  Dockerfile
  .dockerignore
```
