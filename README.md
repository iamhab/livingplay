<p align="center"><img src="assets/icon.png" width="96" alt="Livingplay"></p>

# Livingplay

**Português** · [English](#english)

Player e cache local para reproduzir mídia na **TV (aparelhos compatíveis com Chromecast)** ou **no próprio computador**, com fila, playlists, arquivos guardados e **controle pelo celular**. Gratuito, de código aberto (licença MIT), feito para **uso pessoal e doméstico**.

> Chromecast, Google e YouTube são marcas de seus respectivos titulares. Este programa é independente e **não é afiliado, patrocinado nem endossado** por eles.

## Para que serve

Você cola um link ou escolhe arquivos do computador e aperta play. O Livingplay guarda uma cópia no seu computador, numa pasta com limite de espaço, e toca na TV ou numa janela própria no PC. O que já está guardado toca de novo na hora, mesmo com internet ruim.

## Uso pessoal e responsabilidade (leia)

- O Livingplay foi feito para **uso pessoal e doméstico**. Use **apenas conteúdo que você tem direito de reproduzir e salvar** (seu, de domínio público, licenciado ou autorizado pelo titular).
- **Você é o único responsável** pelo que baixa, guarda e reproduz. Muitos sites, **inclusive o YouTube, não permitem baixar conteúdo fora dos recursos que eles oferecem**; usar o programa pode contrariar esses termos e levar à suspensão da sua conta.
- O programa **não tenta contornar bloqueios, proteções técnicas ou limites** dos sites. Contribuições com esse objetivo não são aceitas.
- **Versões modificadas:** o código é aberto e qualquer pessoa pode modificá-lo. Os avisos deste repositório valem para a versão original publicada pelo autor. **Quem modificar, redistribuir ou usar o programa para outras finalidades é o único responsável pela própria versão e pelo uso que fizer dela.** Veja `DISCLAIMER.md`.
- Este repositório **não contém nem distribui** vídeos, músicas ou outro conteúdo de terceiros. Nada aqui é aconselhamento jurídico.

Leia também: `TERMS_OF_USE.md` · `DISCLAIMER.md` · `PRIVACY_POLICY.md` · `SECURITY.md` · `COPYRIGHT_NOTICE.md`

## O que faz

- **Reproduzir:** TV (Chromecast) ou janela própria no computador (usa o Microsoft Edge ou o Google Chrome já instalados). Fila, repetir, aleatório, timer, retomar a última sessão.
- **Playlists:** quantas quiser; salvar a fila atual como playlist com um clique.
- **Arquivados:** lista tudo o que já está no computador, com busca, ordenação (recentes, nome, tamanho), tocar sem internet, renomear, excluir um, vários ou todos, e abrir a pasta.
- **Arquivos com nome legível:** downloads novos ficam como `Título do vídeo [código].mp4`. O código no fim evita baixar de novo o que já existe.
- **Espaço sob controle:** limite de tamanho da pasta, avisos em 50/75/90/100 % e limpeza manual. O programa nunca apaga arquivos que não criou.
- **Legendas** (arquivo ao lado do vídeo, embutidas ou do site), **volume uniforme** e suporte opcional a **H.265**.
- **Capa na TV** quando o item é só áudio (imagem gerada na hora e apagada depois).
- **Controle pelo celular** (QR code), só na rede local, com código de acesso que pode ser trocado a qualquer momento.
- **Teclado no programa todo** (F1 mostra a lista): espaço toca ou pausa; ← → pulam 10 s; ↑ ↓ mudam o volume; Ctrl+1 a 4 trocam de aba; Delete, F2, Enter e Ctrl+A nas listas.
- **Backup** de playlists e ajustes num arquivo (exportar e importar).
- Português e inglês, tema claro e escuro, três tamanhos de interface, tutorial integrado.

## Requisitos

- Windows 10/11 (o código é Python e pode rodar em outros sistemas, mas foi pensado para Windows).
- Python 3.11 ou mais novo, com Tkinter (já vem no instalador de python.org).
- Internet para instalar as bibliotecas e para o conteúdo que você pedir.
- Opcional: um aparelho compatível com Chromecast na mesma rede (o modo Computador não precisa dele).

## Como instalar e abrir (Windows)

1. Instale o [Python 3](https://www.python.org/downloads/) marcando **“Add python.exe to PATH”**.
2. Baixe este repositório (**Code → Download ZIP**) e extraia.
3. Dê dois cliques em **`iniciar.bat`**. Na primeira vez ele cria um ambiente virtual (`.venv`) e instala as dependências do `requirements.txt`; depois abre o programa. Não precisa de administrador.

Manualmente: `python -m venv .venv`, depois `.venv\Scripts\pip install -r requirements.txt` e `.venv\Scripts\python livingplay.py`.

Na primeira execução o Windows pode pedir permissão no firewall: permita **apenas em rede Privada**.

Este repositório **não oferece instalador pronto (.exe)**. Veja “Licenças” abaixo para entender por quê.

## Como funciona

O resumo técnico (módulos, caminho de um vídeo do link até a TV, arquivos gravados no computador e modelo de segurança) está em [`docs/COMO-FUNCIONA.md`](docs/COMO-FUNCIONA.md). O histórico de versões está em [`CHANGELOG.md`](CHANGELOG.md).

## Cookies (opcional, avançado)

Por padrão **nenhum cookie é usado**. Em **Ajustes → Avançado** dá para ativar um arquivo `cookies.txt` (na sua pasta de usuário ou ao lado do programa). Isso dá acesso à sua conta e pode contrariar os termos do site; o programa pede confirmação. Não há opção de ler cookies direto do navegador.

## Limitações

- Sites mudam e podem bloquear downloads. O programa não tenta contornar isso: mostra um aviso e tenta de novo mais tarde. Atualizar o yt-dlp às vezes resolve (o programa faz isso no máximo 1 vez por dia).
- O controle pelo celular usa HTTP sem criptografia na sua rede: use só em rede doméstica confiável (`SECURITY.md`).
- As teclas de mídia do teclado (play/pausa/próximo) não chegam ao programa no Windows; use os atalhos da lista (F1).

## O que foi testado

Testes automatizados (pasta `tests/`, 16 roteiros) em **Linux com tela virtual, Chromecast simulado** e Chromium para a janela do modo Computador e a página do celular, nos dois modos de janela (barra própria e barra padrão). **Não foi testado em Windows real, com Chromecast real nem com acesso real a sites de vídeo.** Varredura de vulnerabilidades das dependências (`pip-audit`, em 2026-11-18): nenhuma conhecida.

## Licenças

- O código deste repositório é **MIT** (`LICENSE`). O nome e o ícone têm regras próprias (`COPYRIGHT_NOTICE.md`).
- **Nenhuma biblioteca de terceiros está incluída aqui**: o `pip` instala cada uma na sua máquina, com a licença dela (`THIRD_PARTY_NOTICES.md`).
- Algumas têm licença copyleft (GPL/LGPL/MPL), e o pacote `imageio-ffmpeg` traz um ffmpeg compilado com GPL. **Quem distribuir um pacote ou instalador que inclua esses componentes passa a ter as obrigações dessas licenças** (texto da licença e oferta do código-fonte). Por isso este repositório publica só o código-fonte.
- A situação de patentes de codecs (H.264/AAC) não foi analisada.

## Contribuir e relatar problemas

`CONTRIBUTING.md` (contribuições sob MIT, com `Signed-off-by`) · falhas de segurança: aba **Security → Report a vulnerability** (`SECURITY.md`).

---

## English

Local player and cache to play media on your **TV (Chromecast-compatible devices)** or **on the computer itself**, with a queue, playlists, saved files and a **phone remote**. Free, open source (MIT), made for **personal and home use**.

> Chromecast, Google and YouTube are trademarks of their respective owners. This independent program is **not affiliated with, sponsored or endorsed** by them.

### What it is for

Paste a link or pick files from your computer and press play. Livingplay keeps a copy on your computer, in a size-limited folder, and plays it on the TV or in its own window on the PC. What is already saved plays again instantly, even on a weak connection.

### Personal use and responsibility (please read)

- Livingplay is made for **personal and home use**. Use **only content you have the right to play and save**.
- **You alone are responsible** for what you download, keep and play. Many sites, **including YouTube, do not allow downloading content outside the features they offer**; using the program may go against those terms and lead to account suspension.
- The program **does not try to circumvent blocks, technical protections or limits** of any site. Contributions with that goal are not accepted.
- **Modified versions:** the code is open and anyone may modify it. The notices in this repository apply to the original version published by the author. **Whoever modifies, redistributes or uses the program for other purposes is solely responsible for their own version and for how it is used.** See `DISCLAIMER.md`.
- This repository contains no third-party content. Nothing here is legal advice.

### Features

TV or on-computer playback; queue, repeat, shuffle, sleep timer, resume; unlimited playlists; **Archived** tab (search, sort, offline play, rename, delete one/many/all, open folder); readable file names (`Video title [id].mp4`); folder size limit with 50/75/90/100 % warnings (never deletes files it did not create); subtitles, even volume, optional H.265; cover screen for audio; phone remote (QR code, local network only, access code you can renew); **keyboard shortcuts everywhere** (F1 lists them); settings backup; Portuguese/English, light/dark theme, built-in tutorial.

### Install (Windows)

Install [Python 3.11+](https://www.python.org/downloads/) with “Add python.exe to PATH”, download/extract this repository and double-click **`iniciar.bat`** (creates `.venv`, installs `requirements.txt`, opens the program; no administrator needed). Allow the firewall prompt **on Private networks only**. No ready-made installer is published here (see Licenses).

### How it works

See [`docs/COMO-FUNCIONA.md`](docs/COMO-FUNCIONA.md) (English summary at the end) and [`CHANGELOG.md`](CHANGELOG.md).

### Limitations

Sites change and may block downloads; the program does not work around blocks. The phone remote uses unencrypted HTTP on your network (`SECURITY.md`). Keyboard media keys do not reach the program on Windows.

### What was tested

Automated tests (`tests/`) on **Linux with a virtual display, a simulated Chromecast** and Chromium, in both window modes. **Not tested on real Windows, a real Chromecast or real video sites.** Dependency scan (`pip-audit`, 2026-11-18): no known vulnerabilities.

### Licenses

Code: **MIT** (`LICENSE`); name and icon have their own rules (`COPYRIGHT_NOTICE.md`). **No third-party library is included**: `pip` installs each one on your machine under its own license (`THIRD_PARTY_NOTICES.md`). Some are copyleft and `imageio-ffmpeg` ships a GPL-built ffmpeg: **anyone distributing a package or installer that includes them takes on those licenses' obligations**. That is why only source code is published here. Codec patent status was not analyzed.
