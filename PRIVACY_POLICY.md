# Política de privacidade / Privacy policy

Versão 2 · 2026-11-18.

## Português

**Resumo:** o Livingplay roda no seu computador e **não envia dados ao autor**. Não há conta, telemetria, anúncios nem servidor do autor.

**O que fica no seu computador** (pasta do seu usuário):
- `.livingplay.json`: idioma, tema, pasta de vídeos, playlists, última sessão, preferências da aba Arquivados, código de acesso do controle pelo celular e confirmação do aviso inicial.
- `.livingplay.log` (e `.livingplay.log.old`): registro de erros, limitado a cerca de 1 MB.
- `.livingplay.lock`: arquivo vazio que impede abrir o programa duas vezes.
- `.livingplay_window/`: perfil separado do navegador usado no modo Computador.
- Pasta de vídeos (`LivingplayCache` ou a que você escolher): vídeos e áudios baixados ou convertidos, legendas e telas de capa temporárias.
- Arquivo de backup, **só se você exportar** (no local que escolher).
- Opcional: se você ativar o uso de `cookies.txt`, o programa lê esse arquivo para enviá-lo ao site de onde baixa.

**Com quem o programa se comunica:**
- **Sites que você pede** (por exemplo, o link que você cola) e as miniaturas desses vídeos. Esses sites têm políticas próprias e podem ver seu endereço IP.
- **Sua TV e seu celular, na rede local:** os servidores locais só aceitam endereços da rede local.
- **PyPI:** ao instalar ou atualizar bibliotecas (`pip`), inclusive o `yt-dlp` (no máximo 1 vez a cada 24 horas).
- Nada é enviado ao autor.

**Seus direitos:** os dados ficam só com você. Para apagar tudo, feche o programa e exclua os arquivos e pastas acima.

**Segurança:** o controle pelo celular usa HTTP sem criptografia dentro da sua rede. Use só em rede doméstica confiável (veja `SECURITY.md`).

Esta política vale para a versão original deste repositório. Versões modificadas podem se comportar de outra forma e são de responsabilidade de quem as modificou. Este texto descreve o funcionamento do programa conforme o código e não é aconselhamento jurídico.

## English

**Summary:** Livingplay runs on your computer and **does not send data to the author**. There is no account, telemetry, ads or author-run server.

**Stored on your computer:** `.livingplay.json` (settings, playlists, last session, Archived tab preferences, phone remote access code), `.livingplay.log`/`.log.old` (error log, about 1 MB max), `.livingplay.lock` (single-instance lock), `.livingplay_window/` (separate browser profile for computer mode), the video folder (downloads, conversions, subtitles, temporary cover screens), a backup file **only if you export one**, and, if you turn it on, `cookies.txt` is read and sent to the site you download from.

**Who the program talks to:** sites you ask for and their thumbnails (they can see your IP address); your TV and phone on the local network; PyPI when installing or updating libraries (`yt-dlp` at most once every 24 hours). Nothing is sent to the author.

**Your rights:** the data stays with you; delete the files and folders above to erase everything.

**Security:** the phone remote uses unencrypted HTTP on your network; use it only on a trusted home network (see `SECURITY.md`).

This policy applies to the original version in this repository. Modified versions may behave differently and are the responsibility of whoever modified them.
