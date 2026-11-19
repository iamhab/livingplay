# Avisos de terceiros / Third-party notices

**PT —** O Livingplay (código próprio sob licença MIT, veja `LICENSE`) **não inclui** nenhum código, binário ou pacote de terceiros neste repositório. As bibliotecas abaixo são instaladas **separadamente, na máquina de cada usuário**, pelo `pip` (por exemplo, via `iniciar.bat` ou `pip install -r requirements.txt`), a partir do PyPI. Ao instalá-las, o usuário recebe cada uma sob a licença do respectivo projeto, que prevalece para aquele componente.

**EN —** Livingplay's own code is MIT-licensed (see `LICENSE`). This repository **does not include** any third-party code, binary or package. The libraries below are installed **separately on each user's machine** by `pip` from PyPI. Each one is licensed by its own project and that license governs that component.

Levantamento feito em 2026-11-17 a partir dos metadados dos pacotes instalados no ambiente de teste (versões testadas abaixo). Os metadados podem estar incompletos ou mudar em versões futuras: **confira o arquivo de licença de cada pacote instalado**. / Collected on 2026-11-17 from installed package metadata; check each package's own license file.

## Dependências diretas / Direct dependencies

| Pacote | Versão testada | Licença (metadados) | Projeto |
| --- | --- | --- | --- |
| yt-dlp | 2026.10.26 | Unlicense | https://github.com/yt-dlp/yt-dlp |
| PyChromecast | 14.1.1 | MIT | https://github.com/home-assistant-libs/pychromecast |
| imageio-ffmpeg | 0.8.1 | BSD-2-Clause | https://github.com/imageio/imageio-ffmpeg |
| deno (pacote Python) | 2.9.8 | MIT | https://deno.com |
| segno | 1.6.6 | BSD | https://github.com/heuer/segno |
| DejaVu Sans Mono (fonte embutida) | — | Bitstream Vera / DejaVu (livre) | https://dejavu-fonts.github.io (texto em assets/fonts/DEJAVU-LICENSE.txt) |
| Pillow | 13.0.0 | MIT-CMU (HPND) | https://github.com/python-pillow/Pillow |

## Dependências indiretas / Transitive dependencies

| Pacote | Versão testada | Licença (metadados) | Projeto |
| --- | --- | --- | --- |
| brotli | 1.2.1 | MIT | https://github.com/google/brotli |
| casttube | 0.2.1 | MIT | http://github.com/ur1katz/casttube |
| certifi | 2026.10.23 | **MPL-2.0** | https://github.com/certifi/python-certifi |
| charset-normalizer | 3.5.2 | MIT | https://github.com/jawah/charset_normalizer |
| idna | 3.20 | BSD-3-Clause | https://github.com/kjd/idna |
| ifaddr | 0.2.0 | MIT | https://github.com/pydron/ifaddr |
| **mutagen** | 1.48.1 | **GPL-2.0-or-later** | https://mutagen.readthedocs.io |
| protobuf | 7.36.2 | BSD-3-Clause | https://developers.google.com/protocol-buffers/ |
| pycryptodomex | 3.24.2 | BSD e domínio público | https://www.pycryptodome.org |
| requests | 2.34.2 | Apache-2.0 | https://github.com/psf/requests |
| urllib3 | 2.8.0 | MIT | https://github.com/urllib3/urllib3 |
| websockets | 17.4 | BSD-3-Clause | https://github.com/python-websockets/websockets |
| yt-dlp-ejs | 0.8.0 | Unlicense, MIT e ISC | https://github.com/yt-dlp/ejs |
| **zeroconf** | 0.154.0 | **LGPL-2.1-or-later** | https://github.com/python-zeroconf/python-zeroconf |

## Componentes que merecem atenção / Components that need attention

- **ffmpeg (dentro do pacote `imageio-ffmpeg`).** O pacote traz um executável do ffmpeg. Na verificação feita para esta auditoria, o build empacotado foi compilado com a opção `--enable-gpl` (inclui x264), isto é, está sob GPL. Como o Livingplay **não redistribui** esse executável (o `pip` do usuário o baixa do PyPI), as obrigações de redistribuição da GPL não recaem sobre este repositório; **quem redistribuir um pacote ou instalador que inclua esse binário** passa a ter essas obrigações (texto da licença e oferta do código-fonte). Código-fonte do ffmpeg: https://ffmpeg.org/download.html . Situação de **patentes de codecs (H.264/AAC)**: **não foi analisada**.
- **mutagen (GPL-2.0-or-later)** e **zeroconf (LGPL-2.1-or-later)** são usados como bibliotecas instaladas separadamente. A análise de como as licenças copyleft interagem com um programa MIT que as importa **não foi feita por advogado**; por isso o repositório não as distribui. Se você redistribuir um pacote que as inclua, cumpra as licenças delas.
- **certifi (MPL-2.0).** Se você redistribuir os arquivos do certifi, mantenha o aviso da licença e disponibilize o código-fonte desses arquivos.
- **Deno** (executável instalado pelo pacote `deno`) e **yt-dlp-ejs** são usados pelo yt-dlp para executar JavaScript quando o site exige.

- **Instaladores.** Este repositório publica só o código-fonte. Um instalador que inclua o Python, as bibliotecas acima e o ffmpeg **redistribui** esses componentes e obriga quem o distribui a cumprir as licenças deles (GPL, LGPL, MPL etc.). / *This repository publishes source code only; an installer bundling these components redistributes them and its distributor must comply with their licenses.*
- **Verificação de vulnerabilidades:** `pip-audit -r requirements.txt` em 2026-11-18 não encontrou vulnerabilidades conhecidas. / *No known vulnerabilities found on 2026-11-18.*

Os textos completos das licenças estão nos arquivos de cada pacote instalado (pasta `site-packages/<pacote>-<versão>.dist-info/`) e nos repositórios acima.

## Marcas / Trademarks

Chromecast, Google e YouTube são marcas de seus respectivos titulares. Este programa não é afiliado, patrocinado nem endossado por eles. / Chromecast, Google and YouTube are trademarks of their respective owners. This program is not affiliated with, sponsored or endorsed by them.
