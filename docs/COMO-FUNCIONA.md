# Como o Livingplay funciona

Documento técnico para quem quer entender, revisar ou modificar o código. Para usar o programa, veja o `README.md`.

## Visão geral

O Livingplay é um programa de desktop em **Python + Tkinter**. Ele junta quatro peças:

1. **Interface** (Tkinter) com quatro abas: Reproduzir, Playlists, Arquivados e Ajustes.
2. **Obtenção do conteúdo:** links passam pelo [yt-dlp](https://github.com/yt-dlp/yt-dlp), que baixa o arquivo para a pasta de cache. Arquivos do computador são usados direto ou convertidos com o ffmpeg quando a TV não aceita o formato.
3. **Entrega:** um pequeno servidor HTTP local entrega o arquivo à TV (Chromecast, via [PyChromecast](https://github.com/home-assistant-libs/pychromecast)) ou a uma janela do Edge/Chrome em modo aplicativo (modo Computador).
4. **Controle pelo celular:** outro servidor local serve uma página que o celular abre lendo um QR code.

Nada é enviado ao autor. Não há conta, telemetria nem servidor externo do projeto.

## Módulos

| Arquivo | Papel |
| --- | --- |
| `livingplay.py` | Programa principal: janela, abas, fila, downloads, cache, servidores locais, atalhos. |
| `app_info.py` | Nome, versão e identificador do programa (mude aqui para renomear um fork). |
| `i18n.py` | Todos os textos, em português e inglês. |
| `ui_widgets.py` | Botões arredondados, ícones desenhados, áreas com rolagem, fontes e paleta de cores. |
| `winframe.py` | Barra de título própria (minimizar, maximizar, fechar) e montagem das janelas sem piscar. |
| `dialogs.py` | Janelas de pergunta no visual do programa (confirmar, digitar um nome, aviso). |
| `terms.py` | Boas-vindas da primeira execução e janela de Avisos. |
| `tutorial.py` | Tutorial passo a passo. |
| `mediatools.py` | Legendas (SRT/VTT, embutidas ou do site), volume uniforme (loudnorm) e leitura do codec. |
| `visuals.py` | Tela de “Capa” para itens só de áudio (imagem gerada + áudio, em MP4). |
| `pc_player.py` | Modo Computador: abre e controla a janela do navegador em modo aplicativo. |
| `remote_page.py` | Página HTML do controle pelo celular. |
| `tests/` | Testes automatizados com TV simulada (veja abaixo). |

## Caminho de um vídeo, do link até a TV

1. Você cola um link. Só endereços `http(s)` comuns são aceitos.
2. O programa procura o vídeo **já baixado**, sem consultar o site, pelo código do vídeo: primeiro o arquivo de controle (`<código>.<modo>.json`), depois arquivos soltos com o código no nome (`Título [código].mp4` ou o formato antigo `<código>.mp4`), também na pasta da versão antiga.
3. Se não achar, o yt-dlp baixa com o nome `Título [código].ext`. Há um intervalo entre pedidos ao site, e o programa **não tenta contornar bloqueios**: se o site pedir login, ele avisa e espera 15 minutos antes de tentar de novo.
4. Opcional: volume uniforme (`loudnorm`) e legenda no idioma escolhido.
5. O servidor de arquivos registra o arquivo com um **código aleatório** e passa à TV um endereço `http://<IP do PC>:<porta>/f/<código>/<nome>`. A TV busca o arquivo com pedidos parciais (Range), o que permite pular para qualquer ponto.
6. Para itens só de áudio, a TV recebe a tela de **Capa** (gerada uma vez, apagada depois).
7. Os próximos itens da fila são baixados em segundo plano (3 por padrão).

## Arquivos gravados no computador

| Onde | O quê |
| --- | --- |
| `~/.livingplay.json` | Configurações, playlists, última sessão, código de acesso do celular. Gravado de forma atômica (arquivo temporário + troca). Valores inválidos são descartados ao abrir. |
| `~/.livingplay.log` e `.log.old` | Registro de erros, limitado a cerca de 1 MB (guarda só a versão anterior). |
| `~/.livingplay.lock` | Trava que impede dois Livingplay abertos ao mesmo tempo. |
| `~/.livingplay_window/` | Perfil separado do navegador usado no modo Computador. |
| `~/LivingplayCache/` (ou a pasta escolhida) | Vídeos e áudios baixados, arquivos de controle `.json`, `subs/` (legendas), `visuals/` (telas de Capa temporárias) e cópias convertidas `local_*.mp4`. |

### Regras de segurança da pasta

- O programa só apaga o que **ele mesmo criou**: arquivos com arquivo de controle próprio, sobras de download reconhecíveis (`.part`, `.ytdl`, `.fNNN`), conversões `local_*.mp4` e telas em `visuals/`.
- Arquivos que você colocou na pasta aparecem em Arquivados, mas **nunca** entram nas limpezas automáticas nem no “Excluir todos”. Só saem se você excluir um por um, com confirmação.
- Pastas sensíveis (raiz do disco, pasta do usuário, Windows, Arquivos de Programas, ProgramData) são recusadas como pasta de cache.
- O limite de espaço apaga primeiro os vídeos usados há mais tempo e nunca o que está tocando ou está na fila.

## Servidores locais e segurança

| Servidor | Porta | Quem pode acessar | Proteção |
| --- | --- | --- | --- |
| Arquivos para a TV | aleatória | só IPs de rede local/loopback | código aleatório por arquivo na URL; só arquivos registrados; conexão parada fecha em 120 s |
| Controle pelo celular | 8765 (ou aleatória se ocupada) | só IPs de rede local/loopback | código de acesso de 24 caracteres (comparação em tempo constante); bloqueio de 1 min após 8 erros; corpo limitado a 64 KB; cabeçalhos de segurança e CSP; conexão parada fecha em 20 s |
| Janela do modo Computador | a do controle, rota `/pc` | só `127.0.0.1` | mesmo código de acesso |

- No Windows a porta é aberta em modo **exclusivo** (outro programa não consegue ocupar a mesma porta).
- O código de acesso pode ser trocado na janela do QR code (“Gerar novo código de acesso”): links antigos param de funcionar na hora.
- Textos que vão para as páginas são escapados; títulos de vídeo nunca viram HTML.
- Processos externos (ffmpeg, navegador) são chamados com lista de argumentos, sem shell.
- Imagens de capa são limitadas a 6 MB e 40 milhões de pixels.
- O tráfego na rede local é **HTTP sem criptografia**: use em rede doméstica confiável.

## Desempenho e estabilidade

- Tudo o que pode demorar (download, conversão, leitura de pastas, contagem da fila, uso de espaço) roda em segundo plano. A interface só é alterada pela thread principal, por uma fila de tarefas lida a cada 100 ms.
- A leitura do codec de cada arquivo é guardada em memória, e a lista da pasta só é relida quando a pasta muda.
- A janela aparece já montada (sem “desenhar aos poucos”) e as janelas secundárias abrem no lugar certo, sem piscar.
- Ao fechar, a janela some na hora, a sessão é salva e a busca de TVs tem no máximo 2 s para parar.

## Testes

Os testes ficam em `tests/` e usam uma TV simulada. Precisam de Python 3.11+, Tkinter, Pillow, imageio-ffmpeg e, para alguns, Playwright com Chromium. No Linux, rode com tela virtual:

```
xvfb-run -a python tests/files20.py
LP_FRAME=0 xvfb-run -a python tests/files20.py   # barra padrão do Windows
LP_FRAME=1 xvfb-run -a python tests/files20.py   # barra própria
```

Cada teste imprime `RESULTADO n / n` no fim (alguns só listam `OK`/`FALHOU`).

## Como modificar com segurança

- Textos novos: acrescente nos dois idiomas em `i18n.py`.
- Para publicar uma versão modificada, troque `APP_NAME`/`APP_SLUG` em `app_info.py` e o ícone (veja `COPYRIGHT_NOTICE.md`), e lembre que **a responsabilidade pela versão modificada é de quem a modificou** (`DISCLAIMER.md`).
- Não remova as checagens de rede local, o código de acesso nem as regras de exclusão da pasta.

---

## English summary

Livingplay is a **Python + Tkinter** desktop app. Links go through **yt-dlp** into a size-limited cache folder (files named `Title [id].ext`, plus a `<id>.<mode>.json` control file); local files are used directly or converted with ffmpeg. A local HTTP server hands files to a **Chromecast** (via PyChromecast) or to an Edge/Chrome app-mode window, using a random per-file token and Range support. A second local server serves the **phone remote** page, protected by a 24-character access code (constant-time compare, lockout after 8 failures, local-network IPs only, security headers/CSP, request limits, socket timeouts, exclusive port binding on Windows). The access code can be renewed at any time. The program only deletes files it created; user files in the folder are never part of automatic cleanup. Slow work runs in background threads; the UI is only touched from the main thread through a task queue. Settings are written atomically and validated on load. Tests in `tests/` use a simulated TV (run under `xvfb-run` on Linux). If you publish a modified version, rename it, replace the icon and remember that **you are responsible for your version**.
