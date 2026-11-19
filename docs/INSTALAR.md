# Como instalar o Livingplay no seu computador

**Português** · [English](#english)

Este repositório **não traz instalador pronto (.exe)**: ele publica só o código-fonte. A instalação é feita por você, no seu computador, em poucos passos. Leva cerca de 10 minutos na primeira vez, e depois o programa abre com dois cliques.

> Antes de usar, leia o `README.md` e o `DISCLAIMER.md`: o Livingplay é para **uso pessoal**, e cada pessoa é responsável pelo que baixa e reproduz.

## O que você precisa

- **Windows 10 ou 11.**
- **Internet**, para baixar o Python e as bibliotecas na primeira vez.
- Cerca de **500 MB livres** para o programa e as bibliotecas, mais o espaço para os vídeos que você guardar (o limite é definido em Ajustes).
- **Microsoft Edge ou Google Chrome**, para o modo Computador. O Edge já vem no Windows.
- Opcional: uma **TV ou aparelho compatível com Chromecast** na **mesma rede Wi-Fi** do computador.

Não precisa ser administrador do computador.

## Passo 1 — Instalar o Python

1. Abra **https://www.python.org/downloads/** e clique no botão amarelo **Download Python 3.x** (qualquer versão **3.11 ou mais nova**).
2. Abra o arquivo baixado.
3. **Importante:** na primeira tela, marque a caixa **“Add python.exe to PATH”**, embaixo.
4. Clique em **Install Now** e espere terminar. Depois clique em **Close**.

> Não use o Python da Microsoft Store. Se você digitar `python` e a Microsoft Store abrir, instale pelo site python.org como acima.

## Passo 2 — Baixar o Livingplay

1. Na página do repositório no GitHub, clique no botão verde **Code** e depois em **Download ZIP**.
2. Antes de extrair, clique com o botão direito no ZIP baixado, depois em **Propriedades**. Se aparecer, marque **Desbloquear** e clique em **OK**. Isso evita avisos do Windows depois.
3. Clique com o botão direito no ZIP e escolha **Extrair tudo…**.
4. Escolha uma **pasta definitiva**, por exemplo `Documentos\Livingplay`. Não deixe o programa em Downloads nem numa pasta temporária: se a pasta mudar de lugar, os atalhos param de funcionar.

> Quem usa git pode simplesmente rodar `git clone https://github.com/iamhab/livingplay.git`.

## Passo 3 — Preparar e abrir

1. Dentro da pasta, dê dois cliques em **`iniciar.bat`**.
2. Se o Windows mostrar **“O Windows protegeu o computador”**, clique em **Mais informações** e depois em **Executar assim mesmo**. O aviso aparece porque o arquivo veio da internet; o `iniciar.bat` é texto simples e pode ser aberto no Bloco de Notas para conferir o que ele faz.
3. Na **primeira vez**, abre uma janela preta que:
   - cria um ambiente separado só para o Livingplay (a pasta `.venv`, dentro da pasta do programa);
   - baixa e instala as bibliotecas listadas em `requirements.txt`.

   Isso leva alguns minutos. **Não feche a janela.**
4. No fim, o Livingplay abre sozinho e mostra a tela de boas-vindas.

Nas próximas vezes, o `iniciar.bat` abre o programa direto, em poucos segundos.

## Passo 4 — Permitir na rede (só para TV e celular)

Na primeira vez que o programa conversar com a TV, o **Firewall do Windows** pode perguntar se permite o acesso:

- marque **Redes privadas**;
- **desmarque Redes públicas**;
- clique em **Permitir acesso**.

Assim a TV e o celular da sua casa encontram o programa, mas redes de lugares públicos não.

## Passo 5 — Criar atalhos (recomendado)

Dê dois cliques em **`criar-atalho.bat`**. Ele cria o atalho **Livingplay**, com o ícone do programa, na **Área de Trabalho** e no **Menu Iniciar**. A partir daí, abra o programa por esses atalhos, sem janela preta.

## Primeiros passos no programa

1. Escolha onde tocar: **Chromecast** (TV) ou **Computador**.
2. Na aba **Reproduzir**, cole um link ou clique para escolher arquivos do computador e aperte play.
3. Aperte **F1** para ver os atalhos do teclado e use **Ver tutorial**, no alto, para um passeio guiado.
4. Em **Ajustes → Armazenamento**, defina o limite de espaço da pasta de vídeos.

## Atualizar para uma versão nova

1. Feche o Livingplay.
2. Baixe o ZIP novo (passo 2) e extraia **por cima da mesma pasta**, aceitando substituir os arquivos.
3. Abra pelo atalho ou pelo `iniciar.bat`. Se as bibliotecas mudaram, ele instala só o que for preciso.

Suas playlists, ajustes e vídeos **não se perdem**: eles ficam na sua pasta de usuário, fora da pasta do programa.

## Desinstalar

1. Feche o Livingplay.
2. Apague a pasta do programa e os atalhos `Livingplay` da Área de Trabalho e do Menu Iniciar.
3. Para apagar também seus dados, abra a sua pasta de usuário (`C:\Users\SEU_NOME`) e apague:
   - `.livingplay.json`, `.livingplay.log`, `.livingplay.log.old` e `.livingplay.lock`;
   - a pasta `.livingplay_window`;
   - a pasta de vídeos `LivingplayCache` (ou a que você escolheu em Ajustes).
4. Se não for usar o Python para mais nada, desinstale-o em **Configurações → Aplicativos**.

## Problemas comuns

| O que acontece | O que fazer |
| --- | --- |
| “Python 3 nao encontrado” ou a Microsoft Store abre | Instale o Python pelo **python.org** marcando **Add python.exe to PATH** (passo 1). Se continuar, vá em **Configurações → Aplicativos → Configurações avançadas de aplicativos → Aliases de execução de aplicativo** e desligue **python.exe** e **python3.exe**. |
| “precisa do Python 3.11 ou mais novo” | Instale a versão atual pelo python.org. |
| “nao tem o Tkinter” | Reinstale o Python pelo python.org e, em **Customize installation**, deixe marcado **tcl/tk and IDLE**. |
| Erro ao instalar as dependências | Confira a internet e rode o `iniciar.bat` de novo: ele continua de onde parou. Se persistir, apague a pasta `.venv` e tente outra vez. |
| A TV não aparece | Computador e TV na **mesma rede Wi-Fi**; Firewall permitido em **Redes privadas** (passo 4); clique em **Procurar TV**. Em último caso, digite o IP da TV em **Ajustes → Avançado**. |
| O celular não abre o controle | Celular no **mesmo Wi-Fi** do computador; leia o QR code de novo. |
| O antivírus bloqueou algo | O antivírus pode estranhar o `iniciar.bat` ou o ffmpeg baixado pelo `pip`. Os arquivos vêm do PyPI oficial; se confiar, libere a pasta do Livingplay no antivírus. |
| “O Livingplay já está aberto” | Ele já está rodando: procure a janela na barra de tarefas. |
| Mudei a pasta de lugar e o atalho parou | Rode o `criar-atalho.bat` de novo, a partir da pasta nova. |

Se nada resolver, use o botão **Copiar mensagens**, no rodapé do programa, e abra uma *issue* no GitHub colando o texto. Apague antes qualquer link ou nome pessoal.

---

## English

This repository publishes **source code only** (no ready-made .exe). Installing takes about 10 minutes the first time; afterwards the program opens with a double-click. Livingplay is for **personal use**; see `README.md` and `DISCLAIMER.md`.

**You need:** Windows 10/11, internet for the first setup, about 500 MB free (plus space for saved videos), Microsoft Edge or Google Chrome (for computer mode), optionally a Chromecast-compatible device on the same Wi-Fi. No administrator rights needed.

1. **Install Python 3.11+** from https://www.python.org/downloads/ and tick **“Add python.exe to PATH”** on the first screen. Do not use the Microsoft Store version.
2. **Download** this repository (**Code → Download ZIP**). Right-click the ZIP → **Properties** → tick **Unblock** if shown. Then **Extract All…** into a permanent folder (e.g. `Documents\Livingplay`). Or `git clone https://github.com/iamhab/livingplay.git`.
3. Double-click **`iniciar.bat`**. If Windows says “Windows protected your PC”, click **More info → Run anyway** (the file is plain text; you can open it in Notepad to check it). The first run creates a private environment (`.venv`) inside the folder and installs `requirements.txt`; this takes a few minutes, so do not close the black window. The program then opens by itself.
4. When the **Windows Firewall** asks, allow **Private networks** only.
5. Double-click **`criar-atalho.bat`** to add **Livingplay** shortcuts to the Desktop and Start menu.

**Update:** close the program, extract the new ZIP over the same folder, and open it again; your playlists, settings and videos live in your user folder and are kept.

**Uninstall:** delete the program folder and shortcuts. To remove your data too, delete `.livingplay.json`, `.livingplay.log*`, `.livingplay.lock`, the `.livingplay_window` folder and the `LivingplayCache` folder (or the one you chose) from your user folder.

**Common problems:** “Python not found” or the Store opens: install from python.org with PATH ticked, and turn off the `python.exe`/`python3.exe` app execution aliases in Windows Settings. “needs Python 3.11”: install the current version. “no Tkinter”: reinstall Python with **tcl/tk and IDLE** ticked. Dependency install failed: check the internet and run `iniciar.bat` again; if needed delete `.venv`. TV not found: same Wi-Fi, firewall allowed on Private networks, **Find TV**, or enter the TV IP under **Settings → Advanced**. Moved the folder: run `criar-atalho.bat` again.
