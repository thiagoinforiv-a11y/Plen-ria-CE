import logging
import os
import secrets
import shutil
import tempfile
import threading
import time
import uuid

from flask import Flask, Response, after_this_request, jsonify, render_template, request, send_file

from downloader import DownloadError, download_video

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

APP_PASSWORD = os.environ.get("APP_PASSWORD")
TOKEN_TTL_SECONDS = 10 * 60

_lock = threading.Lock()
_downloads: dict[str, dict] = {}  # token -> {"path": str, "dir": str, "created": float}


def _remove_dir(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


def _cleanup_expired() -> None:
    now = time.time()
    with _lock:
        expired = [t for t, info in _downloads.items() if now - info["created"] > TOKEN_TTL_SECONDS]
        for token in expired:
            info = _downloads.pop(token)
            _remove_dir(info["dir"])


@app.before_request
def _require_password():
    _cleanup_expired()

    if not APP_PASSWORD:
        return Response("Configuração inválida: defina a variável de ambiente APP_PASSWORD no servidor.", 500)

    auth = request.authorization
    if not auth or not secrets.compare_digest(auth.password or "", APP_PASSWORD):
        return Response(
            "Autenticação necessária.",
            401,
            {"WWW-Authenticate": 'Basic realm="Video Downloader"'},
        )


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/buscar")
def buscar():
    payload = request.get_json(silent=True) or {}
    url = (payload.get("url") or "").strip()

    if not url.lower().startswith(("http://", "https://")):
        return jsonify(ok=False, error="Cole um link válido (começando com http:// ou https://).", original_url=url), 400

    tmp_dir = tempfile.mkdtemp(prefix="vd_")

    try:
        result = download_video(url, tmp_dir)
    except DownloadError as exc:
        _remove_dir(tmp_dir)
        logger.warning("Falha ao baixar %s: %s", url, exc)
        return jsonify(
            ok=False,
            error=(
                "Não foi possível baixar esse vídeo. O post pode ser privado, "
                "ter sido removido, ou a plataforma bloqueou o acesso no momento."
            ),
            original_url=url,
        ), 422
    except Exception:
        _remove_dir(tmp_dir)
        logger.exception("Erro inesperado ao baixar %s", url)
        return jsonify(
            ok=False,
            error="Ocorreu um erro inesperado ao processar esse link. Tente novamente.",
            original_url=url,
        ), 500

    token = uuid.uuid4().hex
    with _lock:
        _downloads[token] = {"path": result.file_path, "dir": tmp_dir, "created": time.time()}

    author = result.author or "desconhecido"
    author_display = author if author.startswith("@") else f"@{author}"

    return jsonify(
        ok=True,
        token=token,
        author=author_display,
        caption=result.caption or "(sem legenda)",
    )


@app.get("/api/baixar/<token>")
def baixar(token):
    with _lock:
        info = _downloads.pop(token, None)

    if not info or not os.path.exists(info["path"]):
        return jsonify(ok=False, error="Arquivo não encontrado ou expirado. Busque o link novamente."), 404

    path = info["path"]
    directory = info["dir"]

    @after_this_request
    def _cleanup(response):
        _remove_dir(directory)
        return response

    return send_file(path, mimetype="video/mp4", as_attachment=True, download_name="video.mp4")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
