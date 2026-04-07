
# DevOps / SRE Job Monitor (plus)

Готовый шаблон проекта, который:

- два раза в день (10:00 и 18:00 по America/Los_Angeles) запускает скрапинг через GitHub Actions;
- собирает вакансии с нескольких job-бордов;
- фильтрует только DevOps / SRE / Platform / Cloud роли и исключает объявления с clearance / US citizen / green card требованиями;
- нормализует и дедуплицирует вакансии;
- присваивает приоритеты по локации (P1 Remote → P2 LA/Irvine → P3 California → P4 остальное);
- сохраняет результат в `data/jobs.json` вместе со статусом по каждому источнику (`sources_status`);
- отображает вакансии на GitHub Pages странице `web/index.html` в виде дашборда с KPI и фильтрами;
- даёт кнопку ручного запуска workflow через GitHub API с помощью Personal Access Token.

## Какие ресурсы скрапятся

Сейчас реализованы три HTML-источника (см. `scraper/sources.py`):

- **Wellfound** — DevOps Engineer по North America: `https://wellfound.com/role/l/devops-engineer/north-america`;
- **startup.jobs** — DevOps вакансии: `https://startup.jobs/devops-jobs`;
- **YC Work at a Startup** — DevOps team: `https://www.workatastartup.com/jobs?team=devops`.

Также добавлена инфраструктура под ATS-источники Greenhouse и Lever (см. `scraper/ats_providers.py` и `sources_config.json`) — туда можно будет вписать свои компании, чтобы тянуть данные через официальные Job Board API.

## Фильтрация

`scraper/filters.py` реализует:

- включающие ключевые слова ("devops", "site reliability", "sre", "platform engineer", "infrastructure", "cloud engineer", "kubernetes", "terraform", "gitops");
- стоп-слова для clearance / TS/SCI / US citizen / green card и схожих требований;
- приоритет по локации: P1 Remote, P2 LA / Irvine, P3 California, P4 остальные.

## GitHub Actions

`.github/workflows/scrape.yml`:

- запускается по cron два раза в день (10:00 и 18:00 по LA) + вручную через `workflow_dispatch`;
- ставит зависимости;
- выполняет `python -m scraper.pipeline`;
- коммитит `data/jobs.json` обратно в репозиторий.

## GitHub Pages / фронтенд

`web/index.html` — одностраничный дашборд:

- грузит `../data/jobs.json` и считает KPI;
- показывает таблицу вакансий с приоритетами и источниками;
- поддерживает фильтры (поиск, Remote only, LA/Irvine, California, priority);
- позволяет помечать вакансии как избранные (звёздочка, хранится в localStorage);
- показывает статус по источникам (`sources_status`);
- даёт кнопку "Запустить скраппинг", которая через GitHub API вызывает workflow `scrape.yml`.

Перед использованием **обязательно**:

1. Заменить `YOUR_GITHUB_USERNAME` и `YOUR_REPO_NAME` в `web/index.html` на свои значения.
2. Включить GitHub Actions в репозитории.
3. Один раз вручную запустить workflow `Scrape jobs` (вкладка Actions → `Run workflow`).
4. Включить GitHub Pages и указать директорию, из которой будет отдаваться `web/index.html`.
