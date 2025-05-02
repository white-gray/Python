# Python for Avaya IPO Server Edition v11
написанное на Python для Avaya IPO Server Edition v11

Данные с IPO читаются через API

> *Более подробное описание действия и возможностей скриптов находятся в текстах самих скриптов*

## Avaya_change_users_fromList_Pythin2.7.py
* С помощью этого скрипта можно внести изменения в настройки Users на IPO


## Avaya_delete_users_fromList_Pythin2.7.py
* С помощью этого скрипта из IPO удаляются Users и соответствующие Exteisions из списка


## Avaya_extensions_searchEmptyPool_Pythin2.7.py
* С помощью этого скрипта можно узнать какие пулы Exteisions в системе Avaya IP Office еще свободны.
  > Помогает, когда, например, надо прописать несколько номеров для одного отдела, - чтобы у них были "похожие" номера.


## Avaya_read_extensionsData.py
* С помощью этого скрипта можно получить данные по Exteisions и их GUIDs из иситемы Avaya IP Office


## Avaya_read_usersData_fromAPIandWEB_Pythin2.7.py
* С помощью этого скрипта можно получить данные по Users, и их GUIDs, из сиситемы Avaya IP Office


## Avaya_usersFromWeb_Pythin2.7.py
* С помощью этого скрипта можно получить данные по Users из файла Avaya_usersFromWEB.xml
  > сам .xml файл берется из IPO WebManagement
