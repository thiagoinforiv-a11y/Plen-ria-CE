# Plen-ria-CE

Bot do Telegram que baixa vídeos públicos do Instagram e do Facebook e
responde no chat com:

- 🎬 o arquivo de vídeo;
- 📝 a legenda original do post;
- 👤 o perfil (usuário) que publicou.

## Como funciona

1. Envie ao bot uma mensagem contendo um link de um post/reel/vídeo do
   Instagram ou do Facebook.
2. O bot usa o [yt-dlp](https://github.com/yt-dlp/yt-dlp) para baixar o
   vídeo e extrair os metadados (legenda e autor).
3. O bot responde com o vídeo e uma legenda formatada:

   ```
   👤 Perfil: @usuario
   📝 Legenda:
   texto da legenda original...
   ```

## Requisitos

- Python 3.10+
- Um token de bot do Telegram, criado com o [@BotFather](https://t.me/BotFather)
- `ffmpeg` instalado no sistema (necessário para o yt-dlp mesclar áudio/vídeo)

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edite .env e preencha TELEGRAM_BOT_TOKEN
```

## Executando

```bash
python run.py
```

O bot roda em modo *polling* (não precisa de servidor público/webhook).

## Configuração (arquivo `.env`)

| Variável            | Descrição                                                                 | Padrão      |
|---------------------|-----------------------------------------------------------------------------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token do bot, obtido com o @BotFather                                      | obrigatório |
| `MAX_FILE_SIZE_MB`   | Tamanho máximo de vídeo que o bot tenta enviar                             | `50`        |
| `DOWNLOAD_DIR`       | Pasta temporária onde os vídeos são baixados antes do envio               | `downloads` |
| `COOKIES_FILE`       | (Opcional) Arquivo de cookies (formato Netscape) para conteúdo que exige login | não definido |

### Sobre limites e conteúdo privado

- O Instagram e o Facebook frequentemente exigem login para acessar
  conteúdo, ou aplicam limites de taxa para acessos anônimos. Se o bot
  falhar ao baixar vídeos, exporte os cookies de uma sessão logada (por
  exemplo, com a extensão "Get cookies.txt") e configure `COOKIES_FILE`.
- O limite padrão de envio de arquivos por bots do Telegram é 50MB. Para
  enviar vídeos maiores é necessário rodar um
  [Bot API Server local](https://github.com/tdlib/telegram-bot-api).

## Estrutura do projeto

```
bot/
  config.py      # leitura das variáveis de ambiente
  downloader.py  # download do vídeo e extração de metadados via yt-dlp
  handlers.py    # handlers do Telegram (comandos e mensagens)
  main.py        # inicialização da aplicação
run.py           # ponto de entrada
```
