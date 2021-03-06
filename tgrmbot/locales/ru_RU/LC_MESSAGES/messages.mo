��          �               \  �  ]  /   '  -   W     �     �  #   �     �  V   �  %   H     n     �  *   �  F   �  1        >      ]  J   ~     �     �  �  �    u  M   �
  >   �
  5     D   J  =   �  +   �  �   �  <   �  <     7   A  \   y  �   �  K   m  T   �  J     �   Y  0   �  
      *Available commands:*

/watch `[app_id_or_url [app_description]]`
Start watching for reviews for an application. Command without arguments shows the list of watched applications. Example:
/watch `https://play.google.com/store/apps/details?id=com.android.chrome Chrome`

/unwatch `<app_id_or_url>`
Stop watching for reviews for an application.

/ignore
Add review author to ignore list. Command must be used in reply to review which author should be ignored. Added for watching: [%(app_desc)s](%(app_url)s) Already watching: [%(app_desc)s](%(app_url)s) App not found: %(app_url)s App not watched: `%(app_name)s` Can't find review author to ignore. Changed from Hello, I'm *Google Play app reviews watching bot*.
For help, please use /help command. Invalid app to unwatch: `%(app_str)s` Invalid app: `%(app_str)s` No watched apps. Please specify app to remove from watched. Please use this command in reply to message of reviewer to be ignored. Removed from watched: [%(app_desc)s](%(app_url)s) Reviewer added to ignore list. Reviewer already in ignore list. Unknown command: /%(cmd)s
Please use /help for list of available commands. Watched apps: ago Project-Id-Version: PROJECT VERSION
Report-Msgid-Bugs-To: EMAIL@ADDRESS
POT-Creation-Date: 2017-09-11 17:47+0300
PO-Revision-Date: 2015-07-16 12:30+0300
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language: ru_RU
Language-Team: ru_RU <LL@li.org>
Plural-Forms: nplurals=2; plural=(n==1 ? 0 : 1)
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.4.0
 *Доступные команды:*

/watch `[app_id_or_url [app_description]]`
Начать следить за отзывами о приложении. Команда без параметров выведет список отслеживаемых приложений. Пример:
/watch `https://play.google.com/store/apps/details?id=com.android.chrome Chrome`

/unwatch `<app_id_or_url>`
Прекратить следить за отзывами о приложении.

/ignore
Добавить автора отзыва в список игнорирования.
Используйте команду в ответе на сообщение с отзывом, автор которого должен быть добавлен в список игнорирования. Добавлено в отслеживаемые: [%(app_desc)s](%(app_url)s) Уже отслеживается: [%(app_desc)s](%(app_url)s) Приложение не найдено: %(app_url)s Приложение не отслеживается: `%(app_name)s` Не могу определить автора отзыва. Предыдущий комментарий Привет, я *бот отслеживания отзывов о приложениях Google Play*.
Используйте /help для получения списка доступных команд. Неправильное приложение: `%(app_str)s` Неправильное приложение: `%(app_str)s` Нет отслеживаемых приложений. Укажите приложение для удаления из отслеживаемых. Для игнорирования автора используйте эту команду в ответе на сообщение с отзывом. Удалено из отслеживаемых: [%(app_desc)s](%(app_url)s) Автор отзыва добавлен в список игнорирования. Автор отзыва уже в списке игнорирования. Неизвестная команда: /%(cmd)s
Используйте /help для получения списка доступных команд. Отслеживаемые приложения: назад 