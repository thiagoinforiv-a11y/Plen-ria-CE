# Deploy no Oracle Cloud Free Tier (gratuito para sempre)

Guia para colocar o bot rodando 24h num servidor gratuito, configurado
inteiramente pelo navegador e por um app de SSH no iPhone.

## Fase 1 — Criar a conta e o servidor (Oracle Cloud)

1. Acesse https://www.oracle.com/cloud/free/ pelo Safari e crie a conta
   ("Start for free"). Vai pedir e-mail, endereço e um cartão para
   verificação de identidade — os recursos "Always Free" não são cobrados.
2. Depois de logado, vá no menu (≡) → **Compute** → **Instances** →
   **Create instance**.
3. Em "Image and shape", clique em **Edit** ao lado de "Shape" e escolha
   uma opção marcada como **Always Free eligible** — recomendado:
   `VM.Standard.A1.Flex` (1 OCPU / 6 GB RAM).
4. Em "Image", escolha **Canonical Ubuntu** (22.04 ou mais recente).
5. Em "Add SSH keys", selecione **"Generate a key pair for me"** e clique
   em **"Save private key"** — isso baixa um arquivo `.key` para o seu
   iPhone. Guarde esse arquivo, ele é a "senha" de acesso ao servidor.
6. Clique em **Create** e aguarde o status ficar **Running**.
7. Anote o **Public IP Address** que aparece na página da instância.

Quando tiver o IP público e o arquivo `.key` salvo, me avisa que seguimos
para a Fase 2.

## Fase 2 — Conectar via SSH pelo iPhone

1. Instale o app **Termius** (grátis) na App Store.
2. Em Termius, vá em **Keys** → importe o arquivo `.key` baixado da Oracle.
3. Crie um novo Host:
   - Address: o Public IP anotado
   - Username: `ubuntu`
   - Key: selecione a chave importada
4. Conecte. Na primeira vez ele vai pedir para confirmar o "fingerprint" —
   aceite.

## Fase 3 — Instalar o bot no servidor

Depois de conectado via Termius, rode estes comandos (um de cada vez):

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip git ffmpeg

git clone https://github.com/thiagoinforiv-a11y/Plen-ria-CE.git
cd Plen-ria-CE
git checkout claude/telegram-video-downloader-bot-rubwqh

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
nano .env
```

No `nano`, substitua a linha `TELEGRAM_BOT_TOKEN=...` pelo token real do
seu bot (obtido com o @BotFather). Salve com `Ctrl+O`, `Enter`, e saia com
`Ctrl+X`.

## Fase 4 — Rodar como serviço permanente (systemd)

Isso garante que o bot volte a funcionar sozinho se o servidor reiniciar
ou o processo cair.

```bash
sudo cp ~/Plen-ria-CE/deploy/telegram-bot.service /etc/systemd/system/telegram-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-bot
sudo systemctl status telegram-bot
```

Para ver os logs em tempo real (útil para depurar):

```bash
journalctl -u telegram-bot -f
```

## Fase 5 — Testar

No Telegram, abra a conversa com o seu bot e envie `/start`, depois um
link público de um Reels do Instagram ou vídeo do Facebook.

## Comandos úteis depois

```bash
sudo systemctl restart telegram-bot   # reiniciar
sudo systemctl stop telegram-bot      # parar
cd ~/Plen-ria-CE && git pull && sudo systemctl restart telegram-bot  # atualizar código
```
