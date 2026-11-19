"""Textos do programa em Português (Brasil) e English. Para mudar um texto, edite aqui."""
import locale

from app_info import APP_NAME

LANGS = {"pt": "Português (Brasil)", "en": "English"}
LANG = {"v": "pt"}

STR = {'app_title': (APP_NAME, APP_NAME),
 'subtitle': ('Player e cache local para a sua TV ou para o computador',
              'Local player and cache for your TV or your computer'),
 'st_starting': ('Iniciando...', 'Starting...'),
 'st_searching': ('Procurando a TV na rede...', 'Looking for your TV on the network...'),
 'st_scanning': ('Varrendo a rede...', 'Scanning the network...'),
 'st_connecting': ('Conectando a {name}...', 'Connecting to {name}...'),
 'st_online': ('Online', 'Online'),
 'st_online_name': ('Online · {name}', 'Online · {name}'),
 'st_offline': ('Offline', 'Offline'),
 'st_missing': ('Offline · falta um componente', 'Offline · missing component'),
 'btn_find': ('Procurar TV', 'Find TV'),
 'btn_remote': ('Controle no celular', 'Phone remote'),
 'ready': ('Pronto. Cole um link para começar.', 'Ready. Paste a link to start.'),
 'details': ('Detalhes', 'Details'),
 'copy_log': ('Copiar mensagens', 'Copy messages'),
 'log_copied': ('Mensagens copiadas. Agora é só colar (Ctrl+V) onde precisar.',
                'Messages copied. Just paste them (Ctrl+V) where you need.'),
 'tab_play': ('Reproduzir', 'Play'),
 'tab_lists': ('Playlists', 'Playlists'),
 'dlg_ok': ('OK', 'OK'),
 'dlg_cancel': ('Cancelar', 'Cancel'),
 'dlg_yes': ('Sim', 'Yes'),
 'dlg_no': ('Não', 'No'),
 'tab_files': ('Arquivados', 'Archived'),
 'sec_files': ('VÍDEOS E ÁUDIOS GUARDADOS','SAVED VIDEOS AND AUDIO'),
 'files_search': ('Buscar:','Search:'),
 'files_hint': ('Tudo o que já está baixado. Setas escolhem, Enter toca, F2 renomeia, Delete exclui, Ctrl+A marca todos. Dois cliques também tocam, sem internet.', 'Everything already downloaded. Arrows choose, Enter plays, F2 renames, Delete removes, Ctrl+A selects all. Double-click also plays, no internet needed.'),
 'files_empty': ('Nenhum arquivo baixado ainda. Ao tocar um link, o vídeo ou o áudio fica guardado aqui.',
                 'Nothing downloaded yet. When you play a link, the video or audio is kept here.'),
 'files_count': ('{n} arquivo(s) · {s}', '{n} file(s) · {s}'),
 'files_play': ('Tocar', 'Play'),
 'files_add': ('Juntar à fila', 'Add to queue'),
 'files_del': ('Excluir', 'Delete'),
 'files_refresh': ('Atualizar lista', 'Refresh list'),
 'files_pick': ('Escolha um arquivo da lista primeiro.', 'Pick a file from the list first.'),
 'files_del_ask': ('Excluir PERMANENTEMENTE {n} arquivo(s) ({s})?{nl}Não dá para desfazer.',
                   'Permanently delete {n} file(s) ({s})?{nl}This cannot be undone.'),
 'files_del_done': ('{n} arquivo(s) excluído(s), {s} liberados.', '{n} file(s) deleted, {s} freed.'),
 'files_kind_a': ('Áudio', 'Audio'),
 'files_kind_v': ('Vídeo', 'Video'),
 'files_inuse': ('Esse arquivo está tocando agora e não foi excluído.', 'That file is playing now and was not deleted.'),
 'files_found': ('{n} de {t} arquivo(s)', '{n} of {t} file(s)'),
 'files_sort_new': ('Mais recentes', 'Newest first'),
 'files_sort_name': ('Nome (A–Z)', 'Name (A–Z)'),
 'files_sort_size': ('Maior tamanho', 'Largest first'),
 'files_rename': ('Renomear', 'Rename'),
 'files_rename_t': ('Renomear arquivo', 'Rename file'),
 'files_rename_q': ('Novo nome do arquivo:', 'New file name:'),
 'files_renamed': ('Arquivo renomeado para “{name}”.', 'File renamed to “{name}”.'),
 'files_rename_err': ('Não foi possível renomear: {e}', 'Could not rename: {e}'),
 'files_rename_busy': ('Esse arquivo está tocando agora. Renomeie depois que parar.', 'That file is playing now. Rename it after it stops.'),
 'files_one': ('Escolha só um arquivo para renomear.', 'Pick just one file to rename.'),
 'files_del_all': ('Excluir todos', 'Delete all'),
 'files_del_all_t': ('Excluir todos os arquivos', 'Delete all files'),
 'files_del_all_ask': ('Excluir PERMANENTEMENTE todos os {n} arquivo(s) baixado(s) pelo programa ({s})?{nl}Não dá para desfazer. Arquivos seus que você colocou na pasta não são apagados.', 'Permanently delete all {n} file(s) downloaded by the program ({s})?{nl}This cannot be undone. Files you put in the folder yourself are not deleted.'),
 'files_del_err': ('Alguns arquivos não puderam ser excluídos: {e}', 'Some files could not be deleted: {e}'),
 'files_folder': ('Abrir pasta', 'Open folder'),
 'q_rm_playing': ('Esse item está tocando agora. Escolha outro para tirar da fila.', 'That item is playing now. Pick another one to remove from the queue.'),
 'keys_title': ('Atalhos do teclado', 'Keyboard shortcuts'),
 'f_keys': ('Atalhos do teclado', 'Keyboard shortcuts'),
 'h_keys': ('Espaço, setas, Delete, F2 e outros funcionam no programa todo. Também abrem com F1.', 'Space, arrows, Delete, F2 and more work across the program. Also opened with F1.'),
 'b_keys': ('Ver atalhos', 'Show shortcuts'),
 'f_backup': ('Backup das configurações', 'Settings backup'),
 'h_backup': ('Salva suas playlists e ajustes num arquivo, para levar a outro computador ou recuperar depois.', 'Saves your playlists and settings to a file, to move to another computer or restore later.'),
 'bk_export': ('Exportar', 'Export'),
 'bk_import': ('Importar', 'Import'),
 'bk_saved': ('Backup salvo ({n} playlist(s)).', 'Backup saved ({n} playlist(s)).'),
 'bk_err': ('Não foi possível: {e}', 'Could not do it: {e}'),
 'bk_not': ('Esse arquivo não é um backup do Livingplay.', 'That file is not a Livingplay backup.'),
 'bk_ask': ('Importar {n} playlist(s) e os ajustes deste backup?{nl}Playlists com o mesmo nome serão substituídas. Os ajustes valem quando você abrir o programa de novo.', 'Import {n} playlist(s) and the settings from this backup?{nl}Playlists with the same name will be replaced. Settings take effect next time you open the program.'),
 'bk_done': ('Backup importado ({n} playlist(s)). Feche e abra o programa para aplicar os ajustes.', 'Backup imported ({n} playlist(s)). Close and reopen the program to apply the settings.'),
 'qr_new': ('Gerar novo código de acesso', 'Create a new access code'),
 'qr_new_h': ('Use caso o link ou o QR code tenha chegado a quem não deveria: os antigos param de funcionar na hora.', 'Use it if the link or QR code reached someone it should not have: the old ones stop working at once.'),
 'qr_new_ask': ('Gerar um novo código? Celulares que já usam o controle precisarão ler o QR code de novo.', 'Create a new code? Phones already using the remote will need to scan the QR code again.'),
 'qr_new_done': ('Novo código de acesso criado. Leia o novo QR code no celular.', 'New access code created. Scan the new QR code on your phone.'),
 'already_open': ('O Livingplay já está aberto. Procure a janela dele na barra de tarefas.', 'Livingplay is already open. Look for its window on the taskbar.'),
 'dir_unsafe': ('Essa pasta não pode ser usada (raiz do disco, pasta do usuário ou do sistema). Crie ou escolha uma pasta só para os vídeos.', 'That folder cannot be used (drive root, user or system folder). Create or pick a folder just for the videos.'),
 'kg_play': ('Reprodução', 'Playback'),
 'kg_win': ('Janela', 'Window'),
 'kg_nav': ('Abas e campos', 'Tabs and fields'),
 'kg_lists': ('Nas listas', 'In lists'),
 'k_space': ('Espaço', 'Space'),
 'k_or': ('ou', 'or'),
 'kd_play': ('Tocar ou pausar', 'Play or pause'),
 'kd_skip10': ('Voltar ou avançar 10 s', 'Back or forward 10 s'),
 'kd_skip30': ('Voltar ou avançar 30 s', 'Back or forward 30 s'),
 'kd_vol': ('Volume', 'Volume'),
 'kd_next': ('Próximo', 'Next'),
 'kd_prev': ('Anterior', 'Previous'),
 'kd_mute': ('Sem som', 'Mute'),
 'kd_stop': ('Parar', 'Stop'),
 'kd_help': ('Esta lista de atalhos', 'This shortcut list'),
 'kd_max': ('Maximizar a janela', 'Maximize the window'),
 'kd_quit': ('Fechar o programa', 'Quit the program'),
 'kd_tab': ('Ir para uma aba', 'Go to a tab'),
 'kd_tabnext': ('Próxima aba', 'Next tab'),
 'kd_link': ('Campo do link', 'Link field'),
 'kd_search': ('Buscar nos Arquivados', 'Search Archived'),
 'kd_files': ('Escolher arquivos do PC', 'Pick files from the PC'),
 'kd_save': ('Salvar a fila como playlist', 'Save the queue as a playlist'),
 'kd_newpl': ('Nova playlist', 'New playlist'),
 'kd_refresh': ('Atualizar', 'Refresh'),
 'kd_enter': ('Tocar o item escolhido', 'Play the chosen item'),
 'kd_del': ('Excluir ou tirar da fila', 'Delete or remove from queue'),
 'kd_rename': ('Renomear', 'Rename'),
 'kd_all': ('Marcar todos', 'Select all'),
 'keys_foot': ('Os atalhos não funcionam enquanto você digita num campo.', 'Shortcuts do not work while you are typing in a field.'),
 'sec_set_help': ('AJUDA', 'HELP'),
 'f_welcome': ('Tela de boas-vindas', 'Welcome screen'),
 'h_welcome': ('Mostra de novo a mensagem da primeira vez que você abriu o programa.', 'Shows again the message from the first time you opened the program.'),
 'b_welcome': ('Ver boas-vindas', 'Show welcome'),
 'tab_set': ('Ajustes', 'Settings'),
 'sec_add': ('ADICIONAR VÍDEOS', 'ADD VIDEOS'),
 'btn_playnow': ('Tocar agora', 'Play now'),
 'btn_queue': ('Fila', 'Queue'),
 'btn_files': ('Arquivos do PC', 'PC files'),
 'hint_add': ('Cole o link de um vídeo ou de uma playlist (clipe, entrevista, podcast, documentário, show, '
              'transmissão...). “Tocar agora” troca a fila; “Fila” adiciona no final.',
              'Paste a video or playlist link (clip, interview, podcast, documentary, show, live stream...). '
              '“Play now” replaces the queue; “Queue” adds to the end.'),
 'lbl_mylists': ('Minhas playlists', 'My playlists'),
 'btn_open_pl': ('Abrir', 'Open'),
 'pl_pick_ph': ('Escolha uma playlist...', 'Choose a playlist...'),
 'sec_now': ('TOCANDO AGORA', 'NOW PLAYING'),
 'nothing': ('Nada tocando', 'Nothing playing'),
 'now_hint': ('Cole um link acima e clique em “Tocar agora”.', 'Paste a link above and click “Play now”.'),
 'now_item': ('Item {i} de {n}', 'Item {i} of {n}'),
 'hint_ctl': ('Atalhos: espaço toca ou pausa  ·  ← → pulam 10 s  ·  ↑ ↓ volume  ·  F1 mostra todos', 'Shortcuts: space plays or pauses  ·  ← → skip 10 s  ·  ↑ ↓ volume  ·  F1 shows them all'),
 'lbl_volume': ('Volume', 'Volume'),
 'lbl_quality': ('Qualidade', 'Quality'),
 'q_auto': ('Automática', 'Automatic'),
 'sleep_off': ('Timer: desligado', 'Timer: off'),
 'sleep_n': ('Parar em {n} min', 'Stop in {n} min'),
 'sleep_end': ('Parar ao fim do vídeo', 'Stop after this video'),
 'sec_queue': ('FILA DE REPRODUÇÃO', 'PLAYBACK QUEUE'),
 'bulk_start': ('Baixar a fila toda', 'Download whole queue'),
 'bulk_stop': ('Parar downloads', 'Stop downloads'),
 'hint_queue': ('Duplo clique em um item para tocá-lo. “Baixar a fila toda” guarda tudo no computador para '
                'tocar sem depender da conexão.',
                'Double-click an item to play it. “Download whole queue” saves everything on this PC so it '
                'plays without depending on the connection.'),
 'dl_count': ('Baixados: {r}/{n}', 'Downloaded: {r}/{n}'),
 'queue_from': ('Playlist: {name}', 'Playlist: {name}'),
 'bot_help': ('O YouTube bloqueou novos downloads por um tempo (pede para confirmar que você não é robô). '
              'Vídeos já baixados continuam tocando. Novos voltam a ser tentados sozinhos em 15 minutos. '
              'Você também pode tentar mais tarde ou atualizar o yt-dlp (o programa faz isso sozinho no '
              'máximo uma vez por dia).',
              'YouTube blocked new downloads for a while (it asks to confirm you are not a robot). Videos '
              'already downloaded keep playing. New ones are retried automatically in 15 minutes. You can '
              'also try again later or update yt-dlp (the program does this by itself at most once a day).'),
 'untitled': ('Vídeo', 'Video'),
 'err_convert': ('Não consegui converter este arquivo: {e}', 'Could not convert this file: {e}'),
 'err_notfound': ('arquivo não encontrado: {p}', 'file not found: {p}'),
 'err_unexpected': ('Erro inesperado: {e}', 'Unexpected error: {e}'),
 'no_tv': ('Nenhuma TV conectada ainda.', 'No TV connected yet.'),
 'prep_tools': ('Preparando componentes (só demora na 1ª vez)...',
                'Preparing components (only slow the first time)...'),
 'tools_ready': ('Componentes prontos.', 'Components ready.'),
 'missing_dep': ('Falta uma peça ({e}). Instalando, pode levar 1 a 2 minutos...',
                 'A component is missing ({e}). Installing, this may take 1-2 minutes...'),
 'dep_fail': ('Não consegui instalar o pychromecast: {e}', 'Could not install pychromecast: {e}'),
 'no_tv_found': ('Nenhum Chromecast encontrado', 'No Chromecast found'),
 'not_found_help': ('Não achei a TV. Confira: Chromecast ligado, mesmo Wi-Fi e firewall liberado. Em Ajustes '
                    '> Avançado dá para digitar o IP. {err}',
                    'Could not find the TV. Check: Chromecast is on, same Wi-Fi, firewall allows the app. In '
                    'Settings > Advanced you can type the IP. {err}'),
 'err_prefix': ('Erro: {e}', 'Error: {e}'),
 'conn_fail': ('Não consegui conectar: {e}', 'Could not connect: {e}'),
 'paste_first': ('Cole primeiro o link do vídeo ou da playlist.', 'Paste the video or playlist link first.'),
 'reading_link': ('Lendo o link...', 'Reading the link...'),
 'read_fail': ('Não consegui ler o link: {e}', 'Could not read the link: {e}'),
 'pick_files': ('Escolha vídeos ou áudios do computador', 'Choose videos or audio files from your computer'),
 'ft_media': ('Vídeo e áudio', 'Video and audio'),
 'ft_all': ('Todos', 'All'),
 'n_in_queue': ('{n} item(ns) na fila.', '{n} item(s) in the queue.'),
 'n_added': ('+{n} na fila.', '+{n} added to the queue.'),
 'bulk_stopped': ('Downloads em segundo plano parados.', 'Background downloads stopped.'),
 'queue_empty_dl': ('A fila está vazia: adicione um vídeo ou playlist primeiro.',
                    'The queue is empty: add a video or playlist first.'),
 'bulk_started': ('Baixando a fila toda, um item por vez e com intervalo (para não sobrecarregar o site). '
                  'Você já pode assistir enquanto baixa. Se houver bloqueio, continuo sozinho depois.',
                  'Downloading the whole queue, one item at a time with pauses (so the site is not '
                  'overloaded). You can watch meanwhile. If blocked, I will resume on my own later.'),
 'converting': ('Convertendo o arquivo para a TV (só na 1ª vez)...',
                'Converting the file for the TV (first time only)...'),
 'downloading': ('Baixando... {p}%', 'Downloading... {p}%'),
 'updating_yt': ('Atualizando o componente de download (yt-dlp)...',
                 'Updating the download component (yt-dlp)...'),
 'preparing_item': ('[{i}/{n}] Preparando: {t}', '[{i}/{n}] Preparing: {t}'),
 'playing_item': ('Tocando ({i}/{n}): {t}', 'Playing ({i}/{n}): {t}'),
 'play_fail': ("Não consegui tocar '{t}': {e}", "Could not play '{t}': {e}"),
 'stopped_blocked': ('Parei: o YouTube bloqueou novos downloads (nova tentativa automática às {h}) e nenhum '
                     'item desta fila está baixado ainda. Tente mais tarde.',
                     'Stopped: YouTube blocked new downloads (automatic retry at {h}) and no item in this '
                     'queue is downloaded yet. Please try again later.'),
 'stopped_none': ('Parei: nenhum item da fila tocou. Último erro: {e}',
                  'Stopped: no item in the queue played. Last error: {e}'),
 'unknown': ('desconhecido', 'unknown'),
 'timer_end_done': ('Timer: parei ao fim do vídeo.', 'Timer: stopped at the end of the video.'),
 'end_of_list': ('Fim da lista.', 'End of the list.'),
 'last_item': ('Este é o último item da lista.', 'This is the last item in the list.'),
 'audio_q': ('Você está no modo só áudio; a qualidade de vídeo vale quando voltar ao modo vídeo.',
             'You are in audio-only mode; the video quality applies when you go back to video mode.'),
 'q_set': ('Qualidade: {q}. Vale para os próximos vídeos', 'Quality: {q}. Applies to the next videos'),
 'q_restart': (' (reiniciando o atual no mesmo ponto).', ' (restarting the current one at the same point).'),
 'q_4k': ('2K/4K só funcionam em aparelhos que aceitam essa resolução. Se a TV não tocar, volte para 1080p.',
          '2K/4K only work on devices that support that resolution. If the TV does not play, go back to '
          '1080p.'),
 'paste_start': ('Cole um link e clique em “Tocar agora” para começar.',
                 'Paste a link and click “Play now” to start.'),
 'timer_end_set': ('Timer: vou parar ao fim deste vídeo.', 'Timer: I will stop at the end of this video.'),
 'timer_n_set': ('Timer: vou parar em {n} minutos.', 'Timer: I will stop in {n} minutes.'),
 'timer_up': ('Timer: hora de parar. Parei a reprodução.', 'Timer: time is up. Playback stopped.'),
 'mode_set_audio': ('Modo: só áudio (com capa). Vale para os próximos itens.',
                    'Mode: audio only (with cover). Applies to the next items.'),
 'mode_set_video': ('Modo: vídeo. Vale para os próximos itens.', 'Mode: video. Applies to the next items.'),
 'lang_saved': ('Idioma: Português (Brasil).', 'Language: English.'),
 'choose_dir_t': ('Escolha a pasta dos vídeos baixados', 'Choose the folder for downloaded videos'),
 'dir_fail': ('Não consegui usar essa pasta: {e}', 'Could not use that folder: {e}'),
 'dir_set': ('Pasta dos vídeos: {d} (o que já estava na pasta antiga fica lá).',
             'Videos folder: {d} (what was in the old folder stays there).'),
 'open_fail': ('Não consegui abrir a pasta: {e}', 'Could not open the folder: {e}'),
 'no_session': ('Não há sessão anterior para retomar.', 'There is no previous session to resume.'),
 'last_session': ('Última sessão: {t} em {p} ({n} item(ns) na fila)',
                  'Last session: {t} at {p} ({n} item(s) in the queue)'),
 'no_session_lbl': ('Ainda não há sessão anterior.', 'No previous session yet.'),
 'remote_starting': ('O controle pelo celular ainda está iniciando, tente de novo em instantes.',
                     'Phone remote is still starting, try again in a moment.'),
 'qr_title': ('Controle pelo celular', 'Phone remote'),
 'qr_head': ('Controle tudo pelo celular', 'Control everything from your phone'),
 'qr_sub': ('Com o celular no mesmo Wi-Fi, aponte a câmera para o QR code:',
            'With your phone on the same Wi-Fi, point the camera at the QR code:'),
 'qr_na': ('(QR code indisponível; digite o endereço abaixo no celular)',
           '(QR code unavailable; type the address below on your phone)'),
 'qr_fw': ('Se o Windows pedir, permita o programa na rede.',
           'If Windows asks, allow the program on the network.'),
 'sec_resume': ('CONTINUAR DE ONDE PAROU', 'RESUME WHERE YOU LEFT OFF'),
 'btn_resume': ('Retomar de onde parei', 'Resume where I left off'),
 'sec_playlists': ('MINHAS PLAYLISTS', 'MY PLAYLISTS'),
 'sec_set_conn': ('TV / CONEXÃO', 'TV / CONNECTION'),
 'sec_set_play': ('REPRODUÇÃO', 'PLAYBACK'),
 'sec_set_store': ('ARMAZENAMENTO', 'STORAGE'),
 'sec_set_look': ('IDIOMA E APARÊNCIA', 'LANGUAGE AND APPEARANCE'),
 'sec_set_adv': ('AVANÇADO', 'ADVANCED'),
 'f_device': ('Dispositivos encontrados', 'Devices found'),
 'h_device': ('As TVs da sua rede aparecem sozinhas. Selecione uma e clique em Conectar (ou dê duplo '
              'clique).',
              'TVs on your network show up by themselves. Select one and click Connect (or double-click).'),
 'f_mode': ('Modo de reprodução', 'Playback mode'),
 'h_mode': ('“Só áudio” baixa bem mais rápido: ótimo para podcasts, entrevistas e quando só o som importa. A '
            'tela da TV é escolhida logo abaixo.',
            '“Audio only” downloads much faster: great for podcasts, interviews and when only the sound '
            'matters. The TV screen is chosen just below.'),
 'm_video': ('Vídeo', 'Video'),
 'm_audio': ('Só áudio', 'Audio only'),
 'f_look': ('Baixar adiantado', 'Download ahead'),
 'h_look': ('Quantos vídeos seguintes ficam prontos enquanto um toca.',
            'How many next videos are prepared while one plays.'),
 'f_dir': ('Pasta dos vídeos baixados', 'Downloaded videos folder'),
 'h_dir': ('Onde ficam os vídeos e áudios baixados.', 'Where downloaded videos and audio are kept.'),
 'b_choose': ('Escolher...', 'Choose...'),
 'b_open': ('Abrir', 'Open'),
 'f_limit': ('Limite da pasta (GB)', 'Folder limit (GB)'),
 'h_limit': ('Passou do limite, os itens mais antigos são apagados. 0 = nunca apagar.',
             'Above the limit, the oldest items are deleted. 0 = never delete.'),
 'f_lang': ('Idioma', 'Language'),
 'h_lang': ('Muda na hora, sem reiniciar.', 'Changes immediately, no restart needed.'),
 'f_theme': ('Tema', 'Theme'),
 'h_theme': ('Claro ou escuro.', 'Light or dark.'),
 'f_size': ('Tamanho da interface', 'Interface size'),
 'h_size': ('Compacto, Normal ou Grande.', 'Compact, Normal or Large.'),
 'th_Escuro': ('Escuro', 'Dark'),
 'th_Claro': ('Claro', 'Light'),
 'sz_Compacto': ('Compacto', 'Compact'),
 'sz_Normal': ('Normal', 'Normal'),
 'sz_Grande': ('Grande', 'Large'),
 'f_ip': ('Endereço IP da TV', 'TV IP address'),
 'h_ip': ('Só se a TV não aparecer sozinha: digite o endereço IP do aparelho (aparece no app de configuração '
          'dele).',
          'Only if the TV does not show up: type the device IP address (shown in its setup app).'),
 'b_ip': ('Conectar por IP', 'Connect by IP'),
 'f_cookies': ('Cookies (cookies.txt)', 'Cookies (cookies.txt)'),
 'h_cookies': ('Opcional e desligado por padrão. Use só se souber o que está fazendo: cookies dão acesso à '
               'sua conta. Veja o LEIA-ME.',
               'Optional and off by default. Use only if you know what you are doing: cookies give access to '
               'your account. See the README.'),
 'none': ('Nenhum', 'None'),
 'f_adj': ('Ajuste fino da troca', 'Fine-tune the switch'),
 'h_adj': ('Segundos. Maior = troca mais cedo (menos pausa). Menor = mais tarde.',
           'Seconds. Higher = switches earlier (less gap). Lower = later.'),
 'size_saved': ('Tamanho aplicado.', 'Size applied.'),
 'theme_saved': ('Tema aplicado.', 'Theme applied.'),
 'pl_hint': ('Crie quantas playlists quiser. Selecione uma para ver, tocar ou editar os vídeos dela.',
             'Create as many playlists as you like. Select one to view, play or edit its videos.'),
 'pl_items_in': ('Vídeos em “{name}”', 'Videos in “{name}”'),
 'pl_none_sel': ('Selecione uma playlist acima para ver os vídeos.',
                 'Select a playlist above to see its videos.'),
 'pl_count': ('{name}  ({n})', '{name}  ({n})'),
 'pl_new': ('Nova...', 'New...'),
 'pl_save_q': ('Salvar a fila atual...', 'Save current queue...'),
 'pl_play': ('Tocar', 'Play'),
 'pl_enqueue': ('Adicionar à fila', 'Add to queue'),
 'pl_rename': ('Renomear...', 'Rename...'),
 'pl_delete': ('Excluir', 'Delete'),
 'pl_add_link': ('Adicionar link à playlist', 'Add link to playlist'),
 'pl_link_ph': ('Link de vídeo ou playlist', 'Video or playlist link'),
 'pl_rm_item': ('Remover da playlist', 'Remove from playlist'),
 'pl_name_q': ('Nome da playlist:', 'Playlist name:'),
 'pl_new_title': ('Nova playlist', 'New playlist'),
 'pl_save_title': ('Salvar playlist', 'Save playlist'),
 'pl_rename_title': ('Renomear playlist', 'Rename playlist'),
 'pl_exists': ('Já existe uma playlist com esse nome.', 'A playlist with that name already exists.'),
 'pl_overwrite': ('Já existe uma playlist “{name}”. Substituir?',
                  'A playlist “{name}” already exists. Replace it?'),
 'pl_created': ('Playlist “{name}” criada.', 'Playlist “{name}” created.'),
 'pl_saved': ('Playlist “{name}” salva com {n} item(ns).', 'Playlist “{name}” saved with {n} item(s).'),
 'pl_renamed': ('Playlist renomeada para “{name}”.', 'Playlist renamed to “{name}”.'),
 'pl_deleted': ('Playlist “{name}” excluída.', 'Playlist “{name}” deleted.'),
 'pl_confirm_del': ('Excluir a playlist “{name}”?', 'Delete the playlist “{name}”?'),
 'pl_choose': ('Escolha uma playlist da lista.', 'Choose a playlist from the list.'),
 'pl_empty_pl': ('Esta playlist está vazia. Adicione links nela.',
                 'This playlist is empty. Add links to it.'),
 'pl_added': ('{n} vídeo(s) adicionado(s) à playlist “{name}”.', '{n} video(s) added to playlist “{name}”.'),
 'pl_item_removed': ('Item removido da playlist.', 'Item removed from the playlist.'),
 'pl_queued': ('{n} item(ns) da playlist “{name}” adicionado(s) à fila.',
               '{n} item(s) from playlist “{name}” added to the queue.'),
 'pl_empty_queue': ('A fila está vazia, não há o que salvar.', 'The queue is empty, nothing to save.'),
 'pl_sel_first': ('Selecione primeiro uma playlist.', 'Select a playlist first.'),
 'title_delete': ('Excluir', 'Delete'),
 'remote_ph': ('Cole um link', 'Paste a link'),
 'r_shuffle': ('🔀 Aleatório', '🔀 Shuffle'),
 'r_repeat': ('🔁 Repetir', '🔁 Repeat'),
 'r_timer': ('Timer de dormir', 'Sleep timer'),
 'r_end': ('Fim do vídeo', 'End of video'),
 'r_play': ('Tocar agora', 'Play now'),
 'r_add': ('Adicionar à fila', 'Add to queue'),
 'r_lists': ('Minhas playlists', 'My playlists'),
 'bulk_limit': ('Parei os downloads: a fila já ocupa o limite da pasta. Aumente o limite em Ajustes se '
                'quiser baixar o resto.',
                'Stopped downloads: the queue already fills the folder limit. Raise the limit in Settings to '
                'download the rest.'),
 'bulk_done': ('Pronto: {r} de {n} itens baixados ({f} com erro).',
               'Done: {r} of {n} items downloaded ({f} with errors).'),
 'f_usage': ('Espaço ocupado', 'Space used'),
 'h_usage': ('Só arquivos criados por este programa são contados e apagados. Outros arquivos da pasta nunca '
             'são tocados.',
             'Only files created by this program are counted and deleted. Other files in the folder are '
             'never touched.'),
 'usage_calc': ('Calculando...', 'Calculating...'),
 'usage_pct': ('Pasta em {p}% do limite ({l}).', 'Folder at {p}% of the limit ({l}).'),
 'usage_nolimit': ('Sem limite: nada é apagado sozinho.', 'No limit: nothing is deleted automatically.'),
 'space_btn': ('Pasta {p}%', 'Folder {p}%'),
 'space_warn': ('A pasta de vídeos está em {p}% do limite ({u} de {l}). Se quiser, limpe ou aumente o limite em Ajustes > Armazenamento.', 'The video folder is at {p}% of its limit ({u} of {l}). If you like, clean it or raise the limit in Settings > Storage.'),
 'space_90': ('A pasta de vídeos está quase cheia: {p}% do limite ({u} de {l}). Ao passar do limite, os itens mais antigos são apagados sozinhos. Veja em Ajustes > Armazenamento.', 'The video folder is almost full: {p}% of its limit ({u} of {l}). Past the limit, the oldest items are deleted automatically. See Settings > Storage.'),
 'space_full': ('A pasta de vídeos chegou ao limite ({u} de {l}). Os itens mais antigos serão apagados sozinhos. Para guardar tudo, aumente o limite em Ajustes > Armazenamento.', 'The video folder reached its limit ({u} of {l}). The oldest items will be deleted automatically. To keep everything, raise the limit in Settings > Storage.'),
 'usage_fmt': ('Vídeos baixados: {v} ({nv})  ·  Cache temporário: {c} ({nc})',
               'Downloaded videos: {v} ({nv})  ·  Temporary cache: {c} ({nc})'),
 'usage_unsafe': ('Esta pasta é protegida (raiz do disco ou pasta do sistema). Escolha outra pasta para os '
                  'vídeos.',
                  'This folder is protected (disk root or system folder). Choose another folder for videos.'),
 'b_clean': ('Limpar cache', 'Clear cache'),
 'b_delvids': ('Excluir vídeos baixados...', 'Delete downloaded videos...'),
 'clean_title': ('Limpar cache', 'Clear cache'),
 'clean_ask': ('Apagar o cache temporário ({n} arquivo(s), {s})?{nl}Isso remove downloads incompletos e '
               'arquivos convertidos; eles são refeitos quando precisar. Seus vídeos baixados não são '
               'apagados.',
               'Delete the temporary cache ({n} file(s), {s})?{nl}This removes incomplete downloads and '
               'converted files; they are rebuilt when needed. Your downloaded videos are not deleted.'),
 'clean_none': ('Não há cache temporário para limpar.', 'There is no temporary cache to clear.'),
 'clean_done': ('Cache limpo: {n} arquivo(s), {s} liberados.', 'Cache cleared: {n} file(s), {s} freed.'),
 'delv_title': ('Excluir vídeos baixados', 'Delete downloaded videos'),
 'delv_ask': ('Excluir PERMANENTEMENTE {n} vídeo(s) baixado(s) ({s})?{nl}Não dá para desfazer. Os vídeos '
              'online podem ser baixados de novo; os seus arquivos do PC não são tocados.',
              'PERMANENTLY delete {n} downloaded video(s) ({s})?{nl}This cannot be undone. Online videos can '
              'be downloaded again; your own PC files are not touched.'),
 'delv_none': ('Não há vídeos baixados para excluir.', 'There are no downloaded videos to delete.'),
 'delv_done': ('{n} vídeo(s) excluído(s), {s} liberados.', '{n} video(s) deleted, {s} freed.'),
 'delv_inuse': (' ({k} em uso foi mantido.)', ' ({k} in use was kept.)'),
 'clean_fail': ('Não consegui apagar {n} arquivo(s): {e}', 'Could not delete {n} file(s): {e}'),
 'btn_tutorial': ('Ver tutorial', 'Show tutorial'),
 'lbl_playon': ('Reproduzir em', 'Play on'),
 'tgt_cast': ('Chromecast', 'Chromecast'),
 'tgt_pc': ('Computador', 'Computer'),
 'b_connect': ('Conectar', 'Connect'),
 'b_research': ('Procurar de novo', 'Search again'),
 'dev_current': ('(conectada)', '(connected)'),
 'dev_none': ('Nenhuma TV encontrada ainda.', 'No TV found yet.'),
 'dev_pick': ('Selecione uma TV da lista.', 'Select a TV from the list.'),
 'reconnecting': ('Conexão perdida. Tentando reconectar ({n}/{m})...',
                  'Connection lost. Trying to reconnect ({n}/{m})...'),
 'reconnect_fail': ('Não consegui reconectar sozinho. Clique em “Procurar TV”.',
                    'Could not reconnect by myself. Click “Find TV”.'),
 'st_pc': ('Online · Computador', 'Online · Computer'),
 'pc_title': ('Reprodução no computador', 'Playback on this computer'),
 'pc_idle': ('Aguardando um vídeo...', 'Waiting for a video...'),
 'pc_err': ('Não foi possível reproduzir este vídeo neste computador.',
            'This video could not be played on this computer.'),
 'pc_nowin': ('A janela do vídeo não respondeu. Verifique se o Microsoft Edge ou o Google Chrome está '
              'instalado.',
              'The video window did not respond. Check that Microsoft Edge or Google Chrome is installed.'),
 'pc_timeout': ('O vídeo demorou demais para começar no computador.',
                'The video took too long to start on this computer.'),
 'pc_nobrowser': ('Não achei o Microsoft Edge nem o Google Chrome. Um deles é necessário para o modo '
                  'Computador.',
                  'Could not find Microsoft Edge or Google Chrome. One of them is required for Computer '
                  'mode.'),
 'sw_to_pc': ('Agora tocando no computador.', 'Now playing on this computer.'),
 'sw_to_cast': ('Agora tocando no Chromecast.', 'Now playing on the Chromecast.'),
 'sw_nocast': ('Conecte uma TV antes de usar o Chromecast.', 'Connect a TV before using the Chromecast.'),
 'sw_busy': ('Aguarde a troca terminar.', 'Wait for the switch to finish.'),
 'sw_failed': ('Não consegui trocar. Voltei para o modo anterior.',
               'Could not switch. Went back to the previous mode.'),
 'tut_title': ('Tutorial rápido', 'Quick tutorial'),
 'tut_step': ('Passo {i} de {n}', 'Step {i} of {n}'),
 'tut_prev': ('Voltar', 'Back'),
 'tut_next': ('Próximo', 'Next'),
 'tut_done': ('Concluir', 'Done'),
 'tut_close': ('Fechar', 'Close'),
 'tut1_t': ('Encontre e conecte sua TV', 'Find and connect your TV'),
 'tut1_d': ('O programa procura os Chromecasts da sua rede sozinho. Escolha a TV na lista e clique em '
            'Conectar. O indicador mostra Online, Offline ou Conectando.',
            'The program looks for Chromecasts on your network by itself. Pick your TV in the list and click '
            'Connect. The indicator shows Online, Offline or Connecting.'),
 'tut2_t': ('Adicione vídeos e playlists', 'Add videos and playlists'),
 'tut2_d': ('Cole o link de um vídeo ou playlist e clique em Tocar agora (troca a fila) ou Fila (adiciona no '
            'fim). Arquivos do seu PC também entram na fila.',
            'Paste a video or playlist link and click Play now (replaces the queue) or Queue (adds to the '
            'end). Files from your PC can join the queue too.'),
 'tut3_t': ('Toque, pause e controle', 'Play, pause and control'),
 'tut3_d': ('Use os botões grandes para tocar, pausar, pular faixa ou 10 segundos, repetir e embaralhar. Pelo teclado: espaço toca ou pausa, ← → pulam 10 s, ↑ ↓ mudam o volume. F1 mostra todos os atalhos.', 'Use the big buttons to play, pause, skip a track or 10 seconds, repeat and shuffle. With the keyboard: space plays or pauses, ← → skip 10 s, ↑ ↓ change the volume. F1 shows every shortcut.'),
 'tut4_t': ('Chromecast ou computador', 'Chromecast or computer'),
 'tut4_d': ('Em “Reproduzir em”, troque entre a TV e o computador. O vídeo continua de onde estava, na mesma '
            'fila. Só um lugar toca por vez.',
            'Under “Play on”, switch between the TV and the computer. The video continues from where it was, '
            'in the same queue. Only one place plays at a time.'),
 'tut5_t': ('Saída de som', 'Sound output'),
 'tut5_d': ('O som acompanha o destino escolhido: TV (Chromecast) ou computador. Ver na TV e ouvir no PC ao '
            'mesmo tempo não é oferecido, porque o som sairia fora de sincronia.',
            'The sound follows the chosen destination: TV (Chromecast) or computer. Watching on the TV while '
            'listening on the PC is not offered, because the sound would be out of sync.'),
 'tut6_t': ('Controle no celular', 'Phone remote'),
 'tut6_d': ('Clique em “Controle no celular” e leia o QR code com a câmera. Com o celular no mesmo Wi-Fi, '
            'você controla tudo pelo navegador. Só quem tem o QR code controla.',
            'Click “Phone remote” and scan the QR code with your camera. With your phone on the same Wi-Fi, '
            'you control everything from its browser. Only whoever has the QR code can control it.'),
 'tut7_t': ('Arquivados e espaço', 'Archived files and space'),
 'tut7_d': ('A aba Arquivados lista tudo o que já está no computador: busque, ordene, toque sem internet, renomeie (F2) ou exclua (Delete). Em Ajustes > Armazenamento você vê o espaço usado e limpa o que quiser; nada é apagado sem confirmação.', 'The Archived tab lists everything already on the computer: search, sort, play offline, rename (F2) or delete (Delete). Under Settings > Storage you see the space used and clean up what you want; nothing is deleted without asking.'),
 'tut8_t': ('Ajustes principais', 'Main settings'),
 'tut8_d': ('Em Ajustes: conexão, modo de reprodução (vídeo ou só áudio), legendas e volume uniforme, pasta e limite de espaço, idioma, tema e tamanho. Em Avançado ficam o backup das playlists e a lista de atalhos.', 'In Settings: connection, playback mode (video or audio only), subtitles and even volume, folder and space limit, language, theme and size. Advanced holds the playlist backup and the shortcut list.'),
 'r_offline': ('Sem conexão com o programa no computador. Tentando de novo...',
               'Lost connection to the program on the computer. Retrying...'),
 'r_nothing': ('Nada tocando', 'Nothing playing'),
 'r_now': ('Posição do vídeo', 'Video position'),
 'r_vol': ('Volume', 'Volume'),
 'r_playon': ('REPRODUZIR EM', 'PLAY ON'),
 'r_addvideo': ('ADICIONAR VÍDEO', 'ADD VIDEO'),
 'r_queue': ('FILA DE REPRODUÇÃO', 'PLAYBACK QUEUE'),
 'r_empty': ('A fila está vazia.', 'The queue is empty.'),
 'r_item': ('Item %1 de %2', 'Item %1 of %2'),
 'bad_url': ('Link inválido. Use um endereço que comece com http:// ou https://.',
             'Invalid link. Use an address that starts with http:// or https://.'),
 'f_frame': ('Barra da janela', 'Window bar'),
 'h_frame': ('Por padrão o Livingplay usa uma barra própria, com os botões dentro da janela. Se algo parecer estranho, marque para voltar à barra padrão do Windows.', 'By default Livingplay uses its own bar, with the buttons inside the window. If anything looks odd, tick this to go back to the standard Windows bar.'),
 'ck_frame': ('Usar a barra padrão do Windows', 'Use the standard Windows bar'),
 'frame_restart': ('Feche e abra o Livingplay para aplicar a barra escolhida.', 'Close and reopen Livingplay to apply the chosen bar.'),
 'sec_set_media': ('LEGENDAS E SOM', 'SUBTITLES AND SOUND'),
 'f_subs': ('Legendas', 'Subtitles'),
 'h_subs': ('Aparecem na TV se existirem: arquivo .srt ou .vtt com o nome do vídeo, legenda embutida ou do YouTube.', 'Shown on the TV when available: a .srt or .vtt file named like the video, embedded subtitles or YouTube captions.'),
 'sub_off': ('Desligadas', 'Off'),
 'sub_pt': ('Português', 'Portuguese'),
 'sub_en': ('Inglês', 'English'),
 'f_norm': ('Volume', 'Volume'),
 'h_norm': ('Mesmo nível de som entre os itens. Vale para novos downloads e arquivos convertidos.', 'Same sound level across items. Applies to new downloads and converted files.'),
 'ck_norm': ('Volume uniforme', 'Even volume'),
 'f_hevc': ('Vídeos H.265', 'H.265 videos'),
 'h_hevc': ('Para vídeos de câmera, drone e celular em H.265 em Chromecast Ultra ou Google TV. Na dúvida, deixe desligado.', 'For camera, drone and phone H.265 videos on Chromecast Ultra or Google TV. If unsure, leave it off.'),
 'ck_hevc': ('Tocar H.265 direto', 'Play H.265 directly'),
 'ck_use': ('Usar cookies.txt', 'Use cookies.txt'),
 'ck_title': ('Ativar cookies.txt?', 'Turn on cookies.txt?'),
 'ck_warn': ('Cookies dão acesso à sua conta nos sites. Ao ativar, o programa envia seus cookies ao site de '
             'onde você baixa. Isso pode colocar sua conta em risco (inclusive suspensão) e pode contrariar '
             'os termos do site. Só ative se entender isso e o arquivo cookies.txt for seu.\n'
             '\n'
             'Ativar mesmo assim?',
             'Cookies give access to your account on websites. When on, the program sends your cookies to '
             'the site you download from. This can put your account at risk (including suspension) and may '
             "go against the site's terms. Turn on only if you understand this and the cookies.txt file is "
             'yours.\n'
             '\n'
             'Turn on anyway?'),
 'terms_title': ('Bem-vindo', 'Welcome'),
 'terms_head': ('Bem-vindo ao Livingplay', 'Welcome to Livingplay'),
 'terms_body': ('Seus vídeos e músicas na TV ou no computador, do jeito mais simples: cole um link, escolha '
                'arquivos do PC e aperte play.\n'
                '\n'
                'Tudo fica guardado no seu computador, então o que você já baixou toca rápido, mesmo sem '
                'internet boa.\n'
                '\n'
                'Qualquer dúvida, o botão “Ver tutorial” mostra o caminho. Aproveite!\n'
                '\n'
                'Lembrete: o programa é para uso pessoal, e cada pessoa é responsável pelo que baixa e assiste. '
                'Os detalhes ficam em “Avisos”, no rodapé.',
                'Your videos and music on the TV or the computer, the easy way: paste a link, pick files '
                'from your PC and press play.\n'
                '\n'
                'Everything is kept on your computer, so what you already downloaded plays fast, even on a '
                'weak connection.\n'
                '\n'
                'Any questions, the “Show tutorial” button shows the way. Enjoy!\n'
                '\n'
                'Reminder: the program is for personal use, and each person is responsible for what they '
                'download and watch. Details are under “Notices”, at the bottom.'),
 'terms_ok': ('Vamos lá', "Let's go"),
 'btn_notice': ('Avisos', 'Notices'),
 'notice_title': ('Avisos e informações legais', 'Notices and legal information'),
 'notice_body': ('Finalidade\n'
                 'O Livingplay é um software de uso pessoal e doméstico, voltado à reprodução e ao '
                 'armazenamento local de conteúdo audiovisual no computador e em aparelhos de transmissão da '
                 'sua rede.\n'
                 '\n'
                 'Conteúdo e responsabilidade\n'
                 'O usuário é o único responsável pelo conteúdo que reproduz, baixa e armazena. Utilize '
                 'apenas material que você tenha o direito de usar (de sua autoria, de domínio público, '
                 'licenciado ou expressamente autorizado) e observe a legislação de direitos autorais e os '
                 'termos de uso de cada serviço acessado.\n'
                 '\n'
                 'Privacidade\n'
                 'Configurações, histórico e arquivos permanecem somente no seu computador. O programa não '
                 'exige cadastro, não faz rastreamento e não envia dados pessoais ao desenvolvedor. As '
                 'únicas comunicações externas são as necessárias para acessar o conteúdo que você solicita '
                 'e para atualizar o componente de download. O controle pelo celular opera apenas na sua '
                 'rede local e é protegido por senha.\n'
                 '\n'
                 'Garantia\n'
                 'O software é fornecido “no estado em que se encontra”, sem garantias de qualquer natureza, '
                 'expressas ou implícitas, inclusive de adequação a uma finalidade específica ou de '
                 'funcionamento ininterrupto. Os autores não respondem por danos decorrentes do uso.\n'
                 '\n'
                 'Independência e marcas\n'
                 'O Livingplay é um projeto independente, sem vínculo, patrocínio ou endosso de qualquer '
                 'empresa ou serviço de terceiros. Nomes e marcas eventualmente mencionados pertencem aos '
                 'seus respectivos titulares e servem apenas para indicar compatibilidade.\n'
                 '\n'
                 'Versões modificadas\n'
                 'O código é aberto e pode ser modificado por qualquer pessoa. Estes avisos valem para a versão '
                 'original publicada pelo autor. Quem modificar, redistribuir ou usar o programa para outras '
                 'finalidades é o único responsável pela própria versão e pelo uso que fizer dela.\n'
                 '\n'
                 'Documentos e licenças\n'
                 'Os termos completos estão na pasta do programa: TERMS_OF_USE.md, PRIVACY_POLICY.md e '
                 'DISCLAIMER.md. O código-fonte é distribuído sob a Licença MIT; os componentes de terceiros '
                 'mantêm suas próprias licenças, listadas em THIRD_PARTY_NOTICES.md.',
                 'Purpose\n'
                 'Livingplay is software for personal and home use, designed for playing and locally storing '
                 'audiovisual content on your computer and on streaming devices on your network.\n'
                 '\n'
                 'Content and responsibility\n'
                 'The user is solely responsible for the content they play, download and store. Use only '
                 'material you have the right to use (your own, public domain, licensed or expressly '
                 'authorized) and comply with copyright law and the terms of use of each service you '
                 'access.\n'
                 '\n'
                 'Privacy\n'
                 'Settings, history and files stay on your computer only. The program requires no sign-up, '
                 'performs no tracking and sends no personal data to the developer. The only external '
                 'communications are those needed to reach the content you request and to update the '
                 'download component. The phone remote operates only on your local network and is password '
                 'protected.\n'
                 '\n'
                 'Warranty\n'
                 'The software is provided “as is”, without warranties of any kind, express or implied, '
                 'including fitness for a particular purpose or uninterrupted operation. The authors are not '
                 'liable for damages arising from its use.\n'
                 '\n'
                 'Independence and trademarks\n'
                 'Livingplay is an independent project, with no affiliation, sponsorship or endorsement by '
                 'any third-party company or service. Names and trademarks that may be mentioned belong to '
                 'their respective owners and only indicate compatibility.\n'
                 '\n'
                 'Modified versions\n'
                 'The code is open and anyone may modify it. These notices apply to the original version '
                 'published by the author. Whoever modifies, redistributes or uses the program for other purposes '
                 'is solely responsible for their own version and for how it is used.\n'
                 '\n'
                 'Documents and licenses\n'
                 'The full terms are in the program folder: TERMS_OF_USE.md, PRIVACY_POLICY.md and '
                 'DISCLAIMER.md. The source code is distributed under the MIT License; third-party '
                 'components keep their own licenses, listed in THIRD_PARTY_NOTICES.md.'),
 'notice_close': ('Fechar', 'Close'),
 'f_screen': ('Tela da TV com áudio', 'TV screen for audio'),
 'h_screen': ('“Capa” mostra o título, o artista e a capa do vídeo em tela cheia na TV enquanto toca só o som.', '“Cover” shows the title, artist and video cover full screen on the TV while only sound plays.'),
 's_cover': ('Capa', 'Cover'),
 'btn_save_queue': ('Salvar fila', 'Save queue'),
 'vis_kicker': ('Tocando agora', 'Now playing'),
 'vis_making': ('Preparando a tela {s} desta faixa... {p}%',
                'Preparing the {s} screen for this track... {p}%')}


def detect_lang():
    """Idioma do Windows: português se o sistema estiver em português, senão inglês."""
    try:
        import ctypes
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return "pt" if (lid & 0xFF) == 0x16 else "en"
    except Exception:
        try:
            return "pt" if (locale.getlocale()[0] or "").lower().startswith("pt") else "en"
        except Exception:
            return "en"


def set_lang(code):
    LANG["v"] = code if code in LANGS else "en"


def T(key, **kw):
    pair = STR.get(key)
    if not pair:
        return key
    s = pair[0 if LANG["v"] == "pt" else 1]
    if kw:
        try:
            return s.format(**kw)
        except Exception:
            return s
    return s
