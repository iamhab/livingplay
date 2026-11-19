# Segurança / Security

## Como relatar uma vulnerabilidade / Reporting a vulnerability

**PT —** Não abra uma issue pública com detalhes de falhas de segurança. Use o recurso **“Report a vulnerability”** (aba **Security** do repositório no GitHub), que cria um relatório privado. Este é um projeto pessoal, sem prazo de resposta garantido.

**EN —** Do not open a public issue with security details. Use **“Report a vulnerability”** (the repository's **Security** tab) to create a private report. This is a personal project; no response time is guaranteed.

Relatos valem para a versão original deste repositório. Versões modificadas são de responsabilidade de quem as modificou. / Reports apply to the original version in this repository; modified versions are the responsibility of whoever modified them.

## Medidas adotadas / Measures in place

- **Só rede local.** Os servidores locais (arquivos para a TV e controle pelo celular) recusam qualquer endereço que não seja de rede privada, link-local ou do próprio computador. / *Local servers refuse anything that is not a private, link-local or loopback address.*
- **Código de acesso** aleatório de 24 caracteres para o controle pelo celular, comparado em tempo constante, com bloqueio de 1 minuto após 8 tentativas erradas. Pode ser trocado a qualquer momento na janela do QR code (“Gerar novo código de acesso”). / *24-character random access code, constant-time comparison, 1-minute lockout after 8 failures; can be renewed at any time.*
- **Arquivos para a TV** só por endereço com código aleatório próprio de cada arquivo; nenhum outro arquivo do computador é acessível. / *Files for the TV are only reachable through a random per-file token.*
- **Porta exclusiva no Windows** (outro programa não consegue ocupar a mesma porta) e **tempo limite** em conexões paradas (20 s no controle, 120 s nos arquivos). / *Exclusive port binding on Windows and socket timeouts.*
- **Entradas validadas:** só links `http(s)`; corpo das requisições limitado a 64 KB; textos das páginas escapados; cabeçalhos de segurança e Content-Security-Policy; configuração e backups conferidos ao abrir (valores inválidos são descartados). / *Validated inputs, request size limits, escaped page text, security headers/CSP, settings and backups validated on load.*
- **Processos externos** (ffmpeg, navegador) chamados com lista de argumentos, sem shell. A pasta só é aberta se for de fato uma pasta. / *External processes are run without a shell.*
- **Exclusões restritas** aos arquivos que o próprio programa criou; pastas sensíveis (raiz do disco, pasta do usuário, Windows, Arquivos de Programas) não são aceitas como pasta de vídeos. / *Deletion restricted to files the program created; sensitive folders are refused.*
- **Imagens** de capa limitadas a 6 MB e 40 milhões de pixels. / *Cover images limited in size.*
- **Uma instância por vez**, para evitar duas cópias gravando a mesma configuração. / *Single instance.*

## Limites conhecidos / Known limits

- **HTTP sem criptografia (sem TLS) na rede local.** Quem estiver na mesma rede e capturar o tráfego Wi-Fi pode ver o código de acesso. **Use só em rede doméstica confiável.** Se suspeitar, gere um novo código. / *Unencrypted HTTP on the local network; use only on a trusted home network and renew the code if in doubt.*
- **A TV não envia senha** ao buscar o arquivo; a proteção é o código aleatório na URL e a restrição à rede local. / *The TV sends no credentials.*
- **Atualização automática do yt-dlp** pelo `pip`, a partir do PyPI, no máximo 1 vez a cada 24 h (os sites mudam e o yt-dlp precisa acompanhar). Isso depende da segurança do PyPI. / *yt-dlp is auto-updated from PyPI at most once every 24 h.*
- **Cookies (`cookies.txt`)** dão acesso à sua conta; a opção vem desligada e exige confirmação. / *Cookies give access to your account; off by default.*
- **Firewall do Windows:** permita o programa apenas em rede **Privada**. / *Allow only on Private networks.*

## Verificações feitas / Checks performed

- `pip-audit -r requirements.txt` em 2026-11-18: **nenhuma vulnerabilidade conhecida**. Repita periodicamente. / *No known vulnerabilities on 2026-11-18; repeat periodically.*
- Revisão do código focada em segurança e estabilidade (servidores locais, entradas, exclusão de arquivos, chamadas entre threads). **Não houve auditoria independente.** / *Code review focused on security and stability; no independent audit.*
