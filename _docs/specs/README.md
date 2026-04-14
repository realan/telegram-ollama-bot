# Phase Specs

В этой папке лежат исполнимые спеки для отдельных фаз из [_docs/roadmap.yaml](/Users/user/projects/hw1/_docs/roadmap.yaml).

Идея:

- `roadmap.yaml` хранит общий план развития
- `context-dump.md` хранит актуальное состояние проекта
- `specs/phase-*.yaml` задают узкую постановку на конкретный чат

## Как использовать

Для запуска новой фазы в отдельном чате передавай:

- документы из блока `chat_bundle` внутри конкретного `phase-*.yaml`
- стартовый текст из блока `chat_prompt_template` внутри конкретного `phase-*.yaml`

Если нужна более гибкая настройка контекста:

- используй `required_context`, где файлы разделены на обязательные и опциональные

## Как делать новую phase spec

1. Выбрать фазу в [_docs/roadmap.yaml](/Users/user/projects/hw1/_docs/roadmap.yaml).
2. Скопировать [phase-spec.template.yaml](/Users/user/projects/hw1/_docs/specs/phase-spec.template.yaml).
3. Заполнить `required_context`, `chat_bundle`, `chat_prompt_template`, `scope_in`, `scope_out`, `dependencies`, `files_to_touch`, `acceptance_criteria`.
4. После завершения фазы обновить:
   - статус фазы в `roadmap.yaml`
   - [_docs/context-dump.md](/Users/user/projects/hw1/_docs/context-dump.md)

## Принцип хорошей phase spec

Хорошая спецификация:

- ограничивает scope
- явно перечисляет обязательный контекст для нового чата
- дает готовый `chat_bundle` для копипаста без ручного выбора файлов
- дает готовый `chat_prompt_template` для стартового сообщения в новом чате
- явно перечисляет затрагиваемые файлы
- задает критерии готовности
- указывает, какие тесты нужны
- не требует тянуть весь roadmap в каждый новый чат
