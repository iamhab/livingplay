# Como contribuir / Contributing

**PT —** Obrigado pelo interesse! Este é um projeto pessoal e pequeno; contribuições são bem-vindas, mas podem demorar a ser analisadas.

- **Licença das contribuições.** Ao enviar código, texto ou imagens, você declara que é autor ou tem o direito de contribuir com eles e concorda que sejam licenciados sob a **licença MIT** deste projeto. Inclua uma linha `Signed-off-by: Seu Nome <email>` nos commits (`git commit -s`) para indicar isso (modelo DCO).
- **Não envie** conteúdo de terceiros protegido por direitos autorais, chaves, senhas, cookies, dados pessoais ou binários (`.exe`, `.dll`, ffmpeg etc.).
- **Não serão aceitas** mudanças cujo propósito seja burlar proteções técnicas, medidas de bloqueio ou termos de serviço de plataformas, nem recursos para distribuir conteúdo de terceiros.
- **Escopo.** Mudanças pequenas e focadas, com testes quando possível (`tests/`). Textos novos devem existir em português e em inglês (`i18n.py`).
- **Testes.** Veja `tests/` (Python 3.11+, Tkinter e, em alguns casos, Playwright/Chromium). Eles usam um Chromecast simulado; no Linux rode com `xvfb-run -a python tests/<arquivo>.py`. Como rodar e o que cada parte faz: `docs/COMO-FUNCIONA.md`.
- **Dependências novas** precisam de licença compatível e entrada em `THIRD_PARTY_NOTICES.md`.
- **Segurança:** não remova a restrição à rede local, o código de acesso, os limites de tamanho nem as regras que impedem apagar arquivos que o programa não criou. Veja `docs/COMO-FUNCIONA.md`.
- **Forks e versões modificadas** são de responsabilidade de quem as faz (`DISCLAIMER.md`) e devem seguir as regras de nome e ícone (`COPYRIGHT_NOTICE.md`).

**EN —** Thanks for your interest! This is a small personal project; contributions are welcome but may take time to review.

- **License of contributions.** By submitting code, text or images you state that you are the author or have the right to contribute them and agree that they are licensed under this project's **MIT license**. Sign off your commits (`git commit -s`, DCO model).
- **Do not submit** third-party copyrighted content, keys, passwords, cookies, personal data or binaries.
- **Not accepted:** changes meant to circumvent technical protections, blocking measures or platform terms of service, or features to distribute third-party content.
- **Scope.** Small, focused changes with tests when possible. New texts must exist in Portuguese and English (`i18n.py`).
- **New dependencies** need a compatible license and an entry in `THIRD_PARTY_NOTICES.md`.
- **Security:** do not remove the local-network restriction, the access code, the size limits or the rules that prevent deleting files the program did not create.
- **Forks and modified versions** are the responsibility of whoever makes them (`DISCLAIMER.md`) and must follow the name and icon rules (`COPYRIGHT_NOTICE.md`).
