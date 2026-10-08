# Глоссарий и роспись персонажей — Этап C

Живой документ. Обновляется по ходу перевода `dialogue.csv` (нарезан по
персонажам в `csv/dialogue/*.csv`, индекс — `csv/dialogue/_index.csv`).

## Общие правила перевода диалогов

Продолжение конвенций, уже устоявшихся при переводе `ui.csv`
(см. `NOTES.md`):

- **Имена персонажей — оставляются на латинице/английском** везде: и в
  реплике-теге (`context`/спикер), и при упоминании имени внутри самой
  фразы (например, "Connor" остаётся "Connor", не "Коннор"). Это прямое
  продолжение решения, уже принятого для `ui.csv` (Kyle Hill, MJ Hayes,
  San Mazo и т.д. — все имена собственные держатся в оригинале).
- **Топонимы** (San Mazo, Attleset, Monumento, San Juanico и т.д.) —
  на английском, кроме уже транслитерированной сказочной топонимики
  сюжетной линии Riri/Galinia (Henneg→Хеннег, Galinia→Галиния,
  Brassica→Брассика, Adarna→Адарна, Avery→Эйвери, Hensonian
  Institute→Институт Хенсона — см. блок `riri` в `NOTES.md`).
- **Название рецептов/пончиков** — не переводятся (см. правило
  "recipe-name-never-translated", последовательно применялось во всех
  блоках `ui.csv`).
- **Плейсхолдеры** `{$mcName}`, `${tag}`, `{$type:tag}`, `[i]`/`[/i]`,
  `AND`/`OR`/`NOT` внутри `{...}`/`[...]` — копируются побайтово, не
  переводятся (правило из `NOTES.md`, "Инвентаризация разметки").
- **Бренды** (Starducks, Priceco, Pentagram, hamazon, MacWoland,
  Chauron Oil и т.д.) — на английском, как и во всём `ui.csv`.

## Как читать таблицу

`Речь` — краткая заметка о голосе/регистре персонажа, по образцам
первых строк файла и/или уже накопленному контексту из блоков `ui.csv`.
`TBD` — ещё не прочитан подробно, заметка появится перед переводом его
блока (тот же порядок работы, что был в `ui.csv`: разбор голоса
персонажа непосредственно перед переводом его строк, а не заранее
скопом на все 69).

## Персонажи (по убыванию объёма)

| Спикер (context) | Полное имя | Строк | Роль / голос |
|---|---|---|---|
| `MC` | (игрок, имя из `{$mcName}`) | 20382 | Реплики игрока (протагонист) |
| `QUESTION` | — | 5271 | Варианты ответа игрока (choice-меню) |
| `NARRATION` | — | 4966 | Авторский текст/ремарки |
| `CONNORCOLLINS` | Connor Collins | 3082 | Лучший друг MC с детства; тёплый, поддерживающий, слегка неловкий регистр ("Hey, bud!") |
| `MJHAYES` | MJ Hayes | 3005 | Сестра/брат Zone Hayes; энергичная, торопливая речь, много восклицаний ("Sup, {$mcName}!", "Whew! Guess who's pumped?!") |
| `LUCYDEE` | Lucy Dee | 2871 | Тревожная/мечтательная, много многоточий, интроспективная речь |
| `STACYORTIZ` | Stacy Ortiz | 2828 | Гламурная/light drama, "hun", уход за собой, слегка капризная |
| `EMMETTEMEINE` | Emmette Meine | 2689 | Брат/сестра Emma Meine; ревнивый/поддразнивающий тон к MC и партнёру MC |
| `HARRYYEN` | Harry Yen | 2498 | Брат Cody Yen (см. блоки `harry`/`cody` в `ui.csv`) |
| `RIRI` | Riri | 2120 | Работница куриной фермы в San Mazo; возвышенный, элегантный регистр; тайно — принцесса Avery королевства Galinia (см. блок `riri`) |
| `KYLEHILL` | Kyle Hill | 2077 | Наследник Blooming Hill Florists; туповато-обаятельный студент-повеса (см. блок `kyle`) |
| `ZOEYBELLADONA` | Zoey Belladonna ("Zoey Bee") | 1561 | В паре с Billie; см. блоки `zoey`/`billie` |
| `ORDER` | — | 1316 | Реплики заказа пончика (см. `OrderPanel.cs`) |
| `JOJO` | Jojo | 1264 | Владелец/менеджер зала Starlight Lifters (см. блок `jojo`) |
| `ZONEHAYES` | Zone Hayes | 1248 | Сестра/брат MJ Hayes (см. блок `zone`) |
| `DEXIEDEAN` | Dexie Dean | 1204 | См. блок `dexie` |
| `EMMAMEINE` | Emma Meine | 1200 | Сестра/брат Emmette Meine; дерзкая, ироничная, "Donut Baristaaaaa!" |
| `ADAMLACHANCE` | Adam LaChance | 1066 | Театральный, экспрессивный, вставки "amico"; см. блок `adam` (цитата Пастернака, id#3183) |
| `SALLYDIVINE` | Sally Divine | 970 | Вежливая, слегка отстранённая, много "..."; см. блок `sally` |
| `CODYYEN` | Cody Yen | 862 | Брат Harry Yen (см. блок `cody`) |
| `DETECTIVEFOX` | Detective Fox ("Donut Fox") | 810 | Нуарный детектив; см. блок `dfox` в `ui.csv` (Вор Пончиков, San Juanico, Attleset, Monumento) |
| `NOVA` | Nova | 730 | Роллер-дерби/скейт-тема, энергичная; см. блок `nova` |
| `DEBORA` | Debora | 687 | Сдержанная, вежливо-формальная, философские наблюдения |
| `BILLIE` | Billie | 580 | В паре с Zoey; см. блок `billie` |
| `ELISASTERN` | Elisa Stern | 538 | Жена мэра Hugo Stern (см. таблоидный сюжет блока `sm`/`san`) |
| `REBELBOY` / `REBELGIRL` / `REBELDUCK` | — (архетипы) | 535 / 407 / 25 | Массовка/архетип "бунтарь" |
| `DOUCHEBAG` | — (архетип) | 463 | Массовка-архетип |
| `SOCMEDGIRL` / `SOCMEDBOY` | — (архетипы) | 445 / 418 | Массовка "соцсетевые" архетипы |
| `HIPSTER` | — (архетип) | 434 | Массовка-архетип |
| `CHEERLEADER` | — (архетип) | 360 | Массовка-архетип |
| `CATBOY` | — (архетип) | 321 | Массовка-архетип |
| `SAMCAMARILLO` | Sam Camarillo | 372 | Музыкант/танцор, тема "Waltzing Through Unlife", актёрские классы (пересекается с Adam LaChance) |
| `DAKOTA` | Dakota (Banner) | 113 | Мать держит кейтеринг «Щепотка соли» (см. блок `dakota` в `ui.csv`); переписка с эмодзи, тревожится за Connor/MC |
| `LUCKY` | Lucky | 94 | Упоминает "sister" уехавшую из San Mazo — вероятная связь с сюжетом Riri |
| `CHAD` | Chad | 58 | Бро-архетип ("bro", романтические похождения) |
| `DARLA` | Darla | 45 | Резкая/циничная, упоминает "buckin' wild minotaurs" — похоже на игру/шоу внутри игры |
| `REINA` | Reina | 38 | Не человек — "Chirp Chirp!" (питомец/птица) |
| `TIMDUNHAM` | Tim Dunham | 36 | Тележурналист/ведущий новостей (San Mazo News, репортажи про мэра Stern) |
| `CROWD` | — | 33 | Массовка, хором |
| `QUEENADARNA` | Queen Adarna | 17 | Королева Galinia, бабушка принцессы Avery (сюжет Riri) |
| `ANNOUNCER` | — | 16 | Спортивный/шоу-комментатор (борцовское шоу, "POM POM POUNDER") |
| `MAYORSTERN` | Hugo Stern | 15 | Мэр Attleset, муж Elisa Stern (см. таблоидный блок `sm`) |
| `DEFOWLER` | The DeFowler | 13 | Ростовой костюм/злодей-маскот ("BOW BEFORE THE FEATHERY MIGHT OF THE DEFOWLER") |
| `TRIXIA` | Trixia | 13 | Valley-girl регистр ("like," как слово-паразит) |
| `BECKGELLER` | Beck Geller | 9 | Журналист(ка), берёт интервью у мэра Stern |
| `HUGOSTERN` | Hugo Stern | 9 | (дубль контекста с `MAYORSTERN`? уточнить при переводе — политическая риторика) |
| `TELEVISION` | — | 8 | Голос из телевизора |
| `DIEDRICK` | Diedrick | 7 | Обсуждает политический заговор/исчезновение принцессы (сюжет Riri) |
| `SHOWHOST` | — | 5 | Ведущий шоу, реплики пока пустые ("...") |
| `STERNSUPPORTER` | — | 5 | Массовка на митинге Stern |
| `MARIANNE` / `HANNAH` / `LUKE` | Marianne / Hannah / Luke | 3 / 3 / 2 | Похоже на сценку из внутриигровой мыльной оперы/пьесы (призрак-любовник, "Ashton", "Takako") — не основной актёрский состав |
| `MAYORPEREZ` | Sophia Perez | 2 | Соперница Hugo Stern на выборах мэра (имя подтверждено репликой `TIMDUNHAM`: "Mayor Sophia Perez") |
| `SCENE11` / `SCENE11-2` / `SCENE11-3` | — | 2 / 2 / 2 | Варианты реплики заказа для Connor (альтернативные ветки одной сцены) |
| `CONSOLE` / `CUSTOMER` / `GENERIC` / `KITCHEN1` / `KITCHEN2` / `None` / `SALLY` / `STACY` | — | 1 каждый | Единичные системные/заглушечные строки |

## Открытые вопросы

- `HUGOSTERN` vs `MAYORSTERN` — два разных context-кода с одинаковым
  персонажем (мэр Hugo Stern), нужно свериться при переводе, не
  расходятся ли по регистру речи или по роли в сцене.
- `SALLY`/`STACY` (1 строка каждый) — вероятно опечатка/дубль контекста
  от `SALLYDIVINE`/`STACYORTIZ` (сравнить `id`, при подтверждении —
  either слить в основной файл персонажа, either оставить отдельно).
- `LUCKY` — требует проверки, не является ли он частью сюжета Riri
  (сестра, уехавшая из San Mazo).
