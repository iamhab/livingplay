# Histórico de versões / Changelog

## 3.2.0 — 2026-11-18

### Novidades
- **Aba Arquivados** (antes “Baixados”): lista o que já está no computador, com busca, ordenação (recentes, nome, tamanho), tocar sem internet, juntar à fila, **renomear**, excluir um ou vários, **excluir todos** (só o que o programa baixou) e abrir a pasta. A ordenação e o item marcado ficam guardados.
- **Nomes legíveis nos downloads:** `Título do vídeo [código].ext`. O código no fim mantém o reconhecimento do que já foi baixado; arquivos antigos (`código.ext`) continuam funcionando.
- **Atalhos de teclado em todo o programa** (F1 mostra a lista): espaço, setas, Shift+setas, Ctrl+setas, N/P/M/S, Ctrl+1–4, Ctrl+Tab, Ctrl+L/F6, Ctrl+F, Ctrl+O, Ctrl+S, Ctrl+N, F5, F11, Ctrl+Q; nas listas Enter, Delete, F2 e Ctrl+A. Os atalhos não disparam enquanto se digita num campo.
- **Delete na fila** tira o item (exceto o que está tocando).
- **Backup** de playlists e ajustes (exportar/importar).
- **Janelas de pergunta no visual do programa**, no lugar das caixas padrão do Windows.
- **Botão “Salvar fila”** na aba Reproduzir; **legendas**, **volume uniforme** e **H.265** opcionais; **barra de título própria**; Ajustes numa coluna só; avisos de espaço em 50/75/90/100 %; reconhecimento de vídeos já baixados sem baixar de novo.
- **Novo código de acesso** para o controle pelo celular, a qualquer momento.

### Segurança
- Porta exclusiva no Windows; tempo limite em conexões paradas; leitura do corpo das requisições sempre limitada.
- Textos das páginas do celular e do PC escapados contra caracteres que quebrariam a página.
- Configuração e backups validados ao abrir (valores inválidos são descartados, sem travar o programa).
- Pastas sensíveis recusadas como pasta de vídeos; a pasta só é aberta se for pasta.
- Imagens de capa limitadas em tamanho e pixels.
- Uma instância por vez.

### Estabilidade e desempenho
- Contagem “X de N no computador” em segundo plano e sem consultas repetidas (antes podia congelar a janela com filas grandes de arquivos do PC).
- Codec de cada arquivo lido uma vez só; lista da pasta relida só quando a pasta muda.
- O limite de espaço nunca apaga o que está na fila; arquivos de controle sem vídeo são removidos junto.
- Registro de erros limitado a ~1 MB.
- Fechamento imediato: a janela some na hora e a busca de TVs tem no máximo 2 s para parar.
- Removida a tela “Aurora” (gerava vídeos grandes e lentos); ficou a Capa.

### Documentação
- `docs/COMO-FUNCIONA.md`, este histórico, aviso sobre **versões modificadas** (responsabilidade de quem modifica) e regras de **nome e ícone** para forks.

## 3.1.0 e anteriores

- Reprodução na TV (Chromecast) e no computador (janela própria do Edge/Chrome), fila, repetir, aleatório, timer, retomar sessão.
- Cache local com limite de espaço e limpeza segura; arquivos do PC com conversão quando necessário.
- Playlists; controle pelo celular por QR code; tutorial; português e inglês; tema claro e escuro; três tamanhos de interface.
- Avisos legais, termos, política de privacidade e avisos de terceiros.
- O projeto teve outro nome antes de se chamar Livingplay (por isso o programa ainda reconhece a pasta de vídeos da versão antiga).
