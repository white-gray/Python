# coding=utf-8    #   НЕ УБИРАТЬ И НЕ МЕНЯТЬ! Работает с #  ! И это для Python2 где необходимо опредеоить кодировку


""" Пояснения:
      1) при запуске скрипта из Limux или интерпретатора Pythom (под Windows), предварительно удалить все .decode('UTF-8').encode('cp866')

         при запуске скрипта из cmd Windows  предварительно дописать в каждую подоперацию print (где выводится кириллица) дополнение .decode('UTF-8').encode('cp866')

            (это .decode('UTF-8').encode('cp866') прописывается для верного отображения кириллицы в при запуске скрипта из cmd Windows )

"""


"""
  Описание скрипта
  -----------------

Скрипт написан для обработки заявок Jira по удалению данных в системах телефонии (Naumen + Avaya IPO SE) по уволившимся пользователям.
	Также даются комментарии по удалению данных по этим пользователям в FMTN.
	
	При исполнении скрипта ведется log файл, в котором выводятся действия в процессе, и конечные данные.

Этапы работы скрипта:
	1) коннект в Jira
		- ищет заявки (issue), определенного типа, с определенным названием, и назначенные на определенную группу инженеров
		- найденные заявки прописываются в dictionary с именем results вида  {issueNumber:[dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo, telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department]}, где
														issueNumber              - номер рассматриваемой issue Jira
														dataDismiss              - дата увольнения сотрудника
														nameDismiss              - имя сотрудника
														accountDismiss           - учетка сотрудника
														accountImoprtantInfo     - дополнительная инфо
														telephoneNumberDismiss   - телефонные номера
														nccGrAll_Dismiss         - отделы где участвовал сотрудник
														numberFMTN               - номер FMTN или Zoiper
														department               - департамент где работал сотрудник
		- (сразу) если найдена заявка, которая уже была рассмотрена и пока отложена, т.к. дата увольнения пользователя еще не наступила, - такая заявка в dictionary не вносится
	
	2) коннект с Active Directory (AD)
		- там ищется прописанный в issue пользователь, и по нему собираются данные (если они там есть): в какой группе Naumen участвует пользователь, данные по FMTN и Zoiper, тед.номер в IPO
		- найденные данные прописываются в results
	
	3) коннект с Naumen
		- там по учетке пользователя ищется не состоит ли он в некоей группе Naumen (т.к. данные в AD могут отсутствовать или быть не верными), + данные по  FMTN и Zoiper.
		- найденные данные прописываются в results
    
	4) коннект с Avaya IPO 
		- там читаются данные по Users и Extensions из IPO (полностью), и в них ищутся данные по каждому из увольняющихся пользователей (т.к. данные в AD могут отсутствовать или быть не верными), -  тел.номер в IPO
		- найденные данные прописываются в results

	5) конечные действия
		- если у пользователя не найдено данных по телефонии, - его issue закрывается в Jira с комментарием "Пользователь в системах телефонии не найден"
		- по каждой позиции в results рассматривается была ли уже дата увольнения; и если она еще не наступила, а телефония у пользователя есть, - issue отправляется В ожидание
		- если дата увольнения уже наступила (и по времени уже более 16:00), или уже была в прошлом, - у пользователя удаляются найденные данные из Naumen, IPO, и оставляются комментарии по FMTN и Zoiper
    
"""

import base64
import os.path
import os
import string
import codecs
import requests
import re
import json
import logging
from logging.handlers import RotatingFileHandler
import time
import collections
# import jira
from ldap3 import Server, Connection, ALL
from jira import JIRA
# import psycopg2
import xml.dom.minidom
import random
import requests
from datetime import datetime



# для изменения кодировки 1
import sys
  # определение кодировки
reload(sys)
sys.setdefaultencoding('utf8')
  # _______________________________









"""
  настойки систем
_____________________________________________________________________________________________________________________________________________________"""


  #------------------ логирование -----------------

  # Logging initializing
log_file = './forBlockingUsers.log'
  #logging.basicConfig()
logger = logging.getLogger("forBlockingUsers_ACCESS_Pythin2.7")
logger.setLevel(logging.DEBUG)
  #Set logging level @ params
maxBytes = 500000         # когда размер текущего лог-файла достигнет размера,  следующие записи будут попадать в другие файлы
backupCount = 1  # сколько всего будет сохраняться старых файлов логов (старые будут стираться) (+ рабочий файл)
handler = RotatingFileHandler(log_file, maxBytes = maxBytes, backupCount = backupCount, mode='a', encoding=None, delay=0)
# handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s line %(lineno)d:   %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)



  # ------------------ Jira settings -----------------

    # задаем адрес Jira
jira_options = {'server': URL доступа к Jira}
    # задаем пароль, логин
loginJira = логин доступа Jira (в кавычках)
passJira = парлль доступа Jira (в кавычках)

jira = JIRA(options=jira_options, basic_auth=(loginJira, passJira))

    # определение запроса в Jira - определение типа заявок, которые необходимо найти
      # все заявки типав траЛЯЛя с именем "Блока", направленные на группу из "имя группы инженеров 1", "имя группы инженеров 2"), или "имя группы инженеров 3 (старая)", с указанным статусом
        # значение jql можно предварительно рассмотреть, опеделить, попробовать в WEBinterface Jira на опеации "поиск"
jql = ('project in ("траЛЯЛя") AND status in ("Зарегистрирована", "В ожидании", "В работе", "В очереди", "Первичная обработка", "Первичная обработка. 3 линия", "В очереди. 3 линия", "В работе. 3 линия") AND summary ~ "Блока" AND ("Ответственная команда" in ("имя группы инженеров 1", "имя группы инженеров 2") OR component = "имя группы инженеров 3 (старая)")  order by Rank ASC')



  # ------------------ LDAP Settings -----------------

ldaphost = имя хоста LDAP (в кавычках)
ldaproot = 'dc=...,dc=LOCAL' вместо точек - требуемые параметры
ldapuser = 'cn=...,ou=...,ou=service users,dc=..,dc=local' вместо точек - требуемые параметры
ldappass = пароль доступа LDAP (в кавычках)

# attributes = ['*']   # выводит все атрибуты каждой найденной записи в AD
attributes = ['telephoneNumber', 'memberOf']  # выводить определенные атрибута

LDAPServer = Server(ldaphost, get_info=ALL)



  # ------------------ NaumenCC Settings -----------------

username = имя пользователя Naumen
api_token = токен доступа Naumen
headersNuamen = {"Content-Type": "application/json",
            "Username": username,
            "X-API-Key": api_token}

# max_retries_Naumen = 3   # количество попыток



  # ------------------ IPO Avaya Settings -----------------

server = IPaddress сервера IPO (в кавычках)
username = имя пользователя IPO (в кавычках)
password = пароль IPO (в кавычках) 
authStr = username + ":" + password
authBytesStrEncoded = str(base64.b64encode(bytes(authStr)))

headersIPO_Auth = {"X-User-Client": "Avaya-WebAdmin",
               "X-User-Agent": "Avaya-SDKUser",
               "Content-Type": "application/json",
               "Authorization": "Basic " + authBytesStrEncoded}
headersIPO = {"X-User-Client": "Avaya-WebAdmin",
           "X-User-Agent": "Avaya-SDKUser",
           "Content-Type": "application/json"}





  # ------------------ общие Settings -----------------

nowData = datetime.now().date()     # текущая дата

results={}                    # туда собираются все данные по уволившимся сотрудникам
issueNumber = ""              # номер рассматриваемой issue Jira
dataDismiss = ""              # дата увольнения сотрудника
nameDismiss = ""              # имя сотрудника
accountDismiss = ""           # учетка сотрудника
accountImoprtantInfo = ""     # дополнительная инфо
telephoneNumberDismiss = ""   # телефонные номера
nccGrAll_Dismiss = ""         # отделы где участвовал сотрудник
numberFMTN =  ""              # номер FMTN или Zoiper
department = ""               # департамент где работал сотрудник

dataFromAvayaUsers = {}           # полученные и обработанные данные из IPO Avaya по Users
dataFromAvayaExtensions = {}      # полученные и обработанные данные из IPO Avaya по Extensions

"""
  КОНЕЦ 
    настойки систем
_____________________________________________________________________________________________________________________________________________________"""















"""
  здесь собраны все DEFs
_____________________________________________________________________________________________________________________________________________________"""

  # перевод имени месяца в численное значение
def month_nameToNumber(monthName):
  months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
  monthNumber = months.index(monthName) + 1
  monthNumber = str(monthNumber)
  if len(monthNumber) < 2:
    monthNumber = "0" + monthNumber
  return monthNumber


  # запись логов по конкретной завке
def logIssueInfo(nameIssue, issueResults):
  # print (str(nameIssue), "\t", str(issueResults[0]), "\t", str(issueResults[1]), "\t", str(issueResults[2]), "\t",         str(issueResults[3]), "\t", str(issueResults[4]), "\t", str(issueResults[5]), "\t", str(issueResults[6]))
  logger.info(str(nameIssue) + "\t" + str(issueResults[0]) + "\t" + str(issueResults[1]) + "\t" + str(issueResults[2]) + "\t" + str(issueResults[3]) + "\t" + str(issueResults[4]) + "\t" + str(issueResults[5]) + "\t" + str(issueResults[6]) + "\t" + str(issueResults[7]))



  # вывод на экран собранным данных по Issue
def printInfoAboutIssue (searchInAD, issueNumber, dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo, telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department):
  print "\n\n\t-----------------------------------------------------------------------------------------------------"
  print "\tsearchInAD = ", searchInAD
  print "\tissueNumber = ", issueNumber
  print "\tdataDismiss = ", dataDismiss
  print "\tNameDismiss = ", nameDismiss
  print "\taccountDismiss = ", accountDismiss
  print "\taccountImoprtantInfo = ", accountImoprtantInfo
  print "\ttelephoneNumberDismiss = ", telephoneNumberDismiss
  print "\tnccGrAll_Dismiss = ", nccGrAll_Dismiss
  print "\tnumberFMTN = ", numberFMTN
  print "\tdepartment = ", department
  print "\n"


  # проверка что дата увольнения уже в прошлом, или "сегодня после 16:00)
  # если получаем True - значит дата+время увольнения еще в будущем, и еще ранл удалять функционал пользователя
  # если получаем False, то значит дата увольнения уже наступила, и пора удалять функционал пользователя
def chackDataForChanger():
    print ("\t----In DEF--- dataDismiss = " + str(dataDismiss) + " , nowData = " + str(nowData))
    logger.info("\t----Im DEF--- dataDismiss = " + str(dataDismiss) + " , nowData = " + str(nowData))
    chackData = (nowData < dataDismiss)
    print ("\t\tdataDismiss < nowData = " + str(chackData))
    logger.info("\t\tdataDismiss < nowData = " + str(chackData))
    if chackData:
      print ("\t\tПока рано вносить изменения в аккаунт, т.к. пользователь еще работает\n")
      logger.info("\t\t\tПока рано вносить изменения в аккаунт, т.к. пользователь еще работает\n")
      return True
    elif nowData == dataDismiss and datetime.now().strftime("%H") < "16":
      print ("\t\tПользователь увольняется сегодня, но (по времени) еще рано удалять выданные ему возможности")
      logger.info("\t\tПользователь увольняется сегодня, но (по времени) еще рано удалять выданные ему возможности")
      return True
    else:
      print ("\t\tСегодняшняя дата равна или позже даты увольнения. Обрабатываем данные")
      logger.info("\t\tСегодняшняя дата равна (да и время подходящее)) или позже даты увольнения. Обрабатываем данные")
      return False


  # удаление ранее прописанное метки (чтобы не захламлять вывод)
  #   находятся и удаляются все указанные метки(textMark) в переменной(textFull) (даже если их несколько)
def deleteMark(textFull, textMark):
  textEnd = str.replace(textFull, "")
  if textEnd.find("textMark") != -1: textEnd = deleteMark(textEnd, textMark)
  return textEnd


  # проверяет не является ди данная issue ОТМЕНА УВОЛЬНЕНИЯ или ТЕХНИЧЕСКОЕ увольнение
def thisCancelOrTechDismissal(accountImoprtantInfo):
  if accountImoprtantInfo.find("!!! ОТМЕНА УВОЛЬНЕНИЯ !!!") != -1 or accountImoprtantInfo.find("!!! ТЕХНИЧЕСКОЕ увольнение !!!") != -1:
    print "\t\t\t\t !!! LDAP - поиск пропускается, т.к. у пользователя указано ОТМЕНА или ТЕХНИЧЕСКОЕ УВОЛЬНЕНИЯ"
    logIssueInfo(str(issueNumber), results[str(issueNumber)])  # вывод в лог данных по Issue
    return true


    #----------------
    # работа c AD
    #----------------

  # чтение данных по сотруднику в  Active Directory
def toLDAP_search (ldaproot, ldapfilter, findingUserPrincipalName, attributes):
  # LDAPConn.search(ldaproot, ldapfilter, attributes=attributes)  # было изначально  # мои изменения
  # result = LDAPConn.search(ldaproot, ldapfilter, attributes=attributes)  # мои изменения - выбор пользователя по его  cn
  # print result
  LDAPConn.search(ldaproot, ldapfilter % findingUserPrincipalName, attributes=attributes)
  # print "LDAPConn.entries = ",LDAPConn.entries
  # print "LDAPConn.search = ", LDAPConn.search(ldaproot,'(givenName=i.ivanovskaya)')
  return LDAPConn.entries




    # ----------------
    # работа c Наумен
    #----------------

  # чтение данных по сотруднику в  КЦ Наумен
def toNauenCC_search_User (accountDismiss):
  link = "http://10.20.10.235:8080/api/v2/employees/" + accountDismiss
  response = requests.get(link, headers=headersNuamen, timeout=(1, 3))
  return response

  # определение данных пользователя из Наумен, и добавление их в имеющимся
def printDataFromNaumenCC(issueNumber, results, response, thisIsSecondAccaunt_m):
  printVariableWithCheckIt(thisIsSecondAccaunt_m, "login", response, "login", "")
  printVariableWithCheckIt(thisIsSecondAccaunt_m, "title", response, "title", "")
  printVariableWithCheckIt(thisIsSecondAccaunt_m, "email", response, "email", "")
  printVariableWithCheckIt(thisIsSecondAccaunt_m, "Внутренний телефон", response, "internalPhoneNumber", "")
  results[issueNumber][5] += printVariableWithCheckIt(thisIsSecondAccaunt_m, "Отдел", response, "ou", "")
  results[issueNumber][6] += thisIsSecondAccaunt_m + printVariableWithCheckIt(thisIsSecondAccaunt_m, "Домашний телефон", response, "homePhoneNumber", " FMTN ")
  results[issueNumber][6] += printVariableWithCheckIt(thisIsSecondAccaunt_m, "Рабочий телефон", response, "workPhoneNumber", "")
  results[issueNumber][6] += printVariableWithCheckIt(thisIsSecondAccaunt_m, "Комментарий", response, "comment", " Zoiper ")
  # if response.json()['removed']: results[issueNumber][5] += thisIsSecondAccaunt_m + " | в Наумен даннай УЗ уже уволена!"
  # if response.json()['removed']: print thisIsSecondAccaunt_m, "\n\t\t\tв Наумен даннай УЗ уже уволена!\n"
  return results


  # "костыль" из-за того, чтио не все параметры записи присылаются по REST если эта учетка уволенного пользователя (баг Нау)
def printVariableWithCheckIt(thisIsSecondAccaunt_m, nameVariable, response, variable, append):
  try:
    tryVar = response.json()[variable]  # .dencode('cp866')
    print thisIsSecondAccaunt_m, "\t\t", nameVariable, "\t", tryVar
    if tryVar: data = str(append + tryVar) + " "
    else: data = str(tryVar)
    return data

  except Exception as e:
    print thisIsSecondAccaunt_m, '\t\t\tзапрошено', nameVariable, ', но параметр ', variable, ' в данный момент почему-то не принят  по REST или не может быть показан !)'
    print '\n\tThis is error: ', str(sys.exc_info())


  # удаление учетки в КЦ Наумен (перевод ее с "состояние - удалена")
def remove_user_request(userNaumen):
  global response
  link = "http://10.20.10.235:8080/api/v2/employees/" + userNaumen
  json_data = {"removed": True}

  try:
    response = requests.put(link, json=json_data, headers=headersNuamen, timeout=(1, 3))
    if (response.status_code != 200):
      return ("При удвлении " + userNaumen + ' получена ошибка : ' + str(response.status_code))
    else:
      return ("В системе Наумен удалена учетка " + userNaumen)

  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by def remove_user_request(): ' + str(sys.exc_info()))

  finally:
    response.close()



    #----------------
    # работа c Jira
    #----------------

  # подключение к системе Jira
def enterJira (jira_options, loginJira, passJira):
  jira = JIRA(options=jira_options, basic_auth=(loginJira, passJira))
  print "\t------------ enter Jira"
  logger.info ("\n\t------------ enter Jira")
  return jira



    # ----------------
    # работа c IPO
    # ----------------

  # Авторизация на IPO
def authorizationIPO():
  try:
    # линк для авторизации
    linkAuth ="https://" + server + ":7070/WebManagement/ws/sdk/security/authenticate"

     # процесс авторизации
    global session
    session = requests.session()  # создаём сессию
    session.get(linkAuth, headers=headersIPO_Auth, timeout=(1, 3), verify=False)  # получаем cookie c токеном

  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by def authorizationIPO(): ' + str(sys.exc_info()))
    sys.exit()


   # GET запрос на IPO
def sessionGet(APIfunction):
  try:
    link = "https://" + server + ":7070/WebManagement/ws/sdk/admin/v1/" + APIfunction
    return session.get(link, headers=headersIPO, verify=False)

  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by IPO GET: ' + str(sys.exc_info()))
    sys.exit()

  finally:
    session.close()
    # print "session.verify sessionGet(APIfunction) = ", session.verify


 # DELETE запрос на IPO
def sessionDelete(APIfunction, guid):
  print "\t\tDeleting GUID ", guid
  logger.info("\tDeleting GUID " + guid)
  try:
    link = "https://" + server + ":7070/WebManagement/ws/sdk/admin/v1/" + APIfunction + "?guid=" + guid
    return session.delete(link, headers=headersIPO, verify=False)

  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by IPO DELETE: ' + str(sys.exc_info()))
    sys.exit()

  finally:
    session.close()
    # print "session.verify sessionDelete(APIfunction, guid) = ", session.verify


"""
  КОНЕЦ 
    здесь собраны все DEFs
_____________________________________________________________________________________________________________________________________________________"""












###################################################################################################
#           Program starts
###################################################################################################


print "_____________________________________________________________________________________________________________________________________________________"
print "Обработка задач по увольнениям запущена "
print datetime.now()
print "_____________________________________________________________________________________________________________________________________________________\n\n\n"

logger.info ("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\t_____________________________________________________________________________________________________________________________________________________\n\tОбработка задач по увольнениям запущена \n\t_________________________________________________________________________________________________________________________________________________\n\n\n")






"""
  Получение из Jira данных по заявкам об уволенных пользователях
_____________________________________________________________________________________________________________________________________________________"""



print "\nЗапусквется поиск в Jira\n_____________________________________________________________________________________________________________________________________________________\n\n"
logger.info ("\nЗапусквется поиск в Jira\n_____________________________________________________________________________________________________________________________________________________\n\n")


try:

  jira = enterJira(jira_options, loginJira, passJira)  # подключение к Jira

  # запрос в Jira с поиском заявок указанного в jql типа
  issues_list = jira.search_issues(jql)

  print "\n\t------------список заявок", issues_list, "\n\t------------\n\n"
  logger.info ("\nсписок заявок" + str(issues_list) + "\n")

  logger.info("\n\t-----------------------------------\n\tНайдено: ")

  # рассмотрение найденных заякок
  for findedNameIssue in issues_list:
    findedNameIssue = (str(findedNameIssue).strip())
    print "\n\t-----------------------------------\n\tномер заявки " + findedNameIssue          # номер заявки#

    dataDismiss = ""  # дата увольнения сотрудника
    nameDismiss = ""  # имя сотрудника
    accountDismiss = ""  # учетка сотрудника
    accountImoprtantInfo = ""  # дополнительная инфо
    telephoneNumberDismiss = ""  # телелфонные номера
    nccGrAll_Dismiss = ""  # отделы где участвовал сотрудник
    numberFMTN = ""  # номер FMTN или Zoiper
    department = ""  # дамертамент где работал сотрудник

    # print "\n\njira.issue(findedNameIssue) = ", jira.issue(findedNameIssue)
    # print "\n\njira.issue(findedNameIssue).__dict__ = ", jira.issue(findedNameIssue).__dict__
    # print "\n\njira.issue(findedNameIssue).__dict__['raw'] = ", jira.issue(findedNameIssue).__dict__['raw']
    # print "\n\njira.issue(findedNameIssue).__dict__['raw']['fields'] = ", jira.issue(findedNameIssue).__dict__['raw']['fields']
    # print "\n\njira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624'] = ", jira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624']
    # print "\n\njira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624']['id'] = ", jira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624']['id']
      #  Определяется отправленна ли issue в ожидание до даты увольнения
      #   По условиям:
      #     1. что поле 'customfield_19624' вообще заполнено, и
      #     2. данная issue уже было рассмотрено и отправлена "В ожидание" с меткой "Решнеие техническоцй проблемы" (код 43407)
      #     3. данная issue уже было рассмотрено и отправлена "В ожидание" с меткой "Дата оформления/увольнения" (код 45405) и (поскольку этот код такой же, как и у новой заявки) у issue есть комментарий с текстом "отложено до 16:00 даты увольнения"

    print "findedNameIssue = ", findedNameIssue

    try:      # сделано через try потому что поля comment нет в изначальном issue
      issueInWaitimg = 0 # эта переменная для выхода из вложенного цикла
      # print "jira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624'] = ", jira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624']
      # print "jira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624']['id']", jira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624']['id']
      # print "jira.issue(findedNameIssue).fields.comment.comments = ", jira.issue(findedNameIssue).fields.comment.comments
      if jira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624'] != None :
        if jira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624']['id'] == "43407" \
            or jira.issue(findedNameIssue).__dict__['raw']['fields']['customfield_19624']['id'] == "45405":
          for id in jira.issue(findedNameIssue).fields.comment.comments:
            # print "id коммента = ", id
            # print "id.body = ", id.body
            # print "id.body.find('отложено до 16:00 даты увольнения') = ", id.body.find("отложено до 16:00 даты увольнения")
            if id.body.find("отложено до 16:00 даты увольнения") !=-1 or id.body.find("отложено до 16:00 даты  увольнения") !=-1:
              issueInWaitimg = 1  # помечаем что данная issue отправленна в ожидание до даты увольнения
    except Exception as e:
      # issueInWaitimg = 0 # эта переменная для выхода из вложенного цикла
      print '\n\tэта issue рассматривется в первый раз\n\t\t', str(e), "\n\t\t", str(sys.exc_info())
      logger.error('эта issue рассматривется в первый раз ')
    print "issueInWaitimg = ", issueInWaitimg
    if issueInWaitimg == 1:   # если определено что данная issue отправлена в ожидание до даты увольнения
      print "\t\t" + str(findedNameIssue) + " уже рассматривалаcь, и по результатам отправлена В ожидание. Пропускаем"
      logger.info("\t\t" + str(findedNameIssue) + " уже рассматривалаcь, и по результатам отправлена В ожидание. Пропускаем")
      # if accountImoprtantInfo.find("Заявка уже отправлена В ожидание до даты увольнения | ") == -1:
      # results[issueNumber][3] = str("Заявка уже отправлена В ожидание до даты увольнения | " + accountImoprtantInfo)
      continue


      # для каждой заявки берем ее текст и вытаскиваем из него требуемые данные
    # print "findedNameIssue = ", findedNameIssue
    # print "type findedNameIssue = ", type(findedNameIssue)

      # рассмотр поля заявки "Описание"
    issues_descriptionText = jira.issue(findedNameIssue).fields.description

    # print "issues_descriptionText = " + str(issues_descriptionText)
    # print "\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"

      # если в тексте issue ничего нет, то читаем текст из родительнской заявки (по номеру -2)
              # побовал это сделать, но не получилось.
                # По каким-то причинам обрабатывает только первый родительский issue, а на осталные выдает
                #    error: (<type 'exceptions.TypeError'>, TypeError("cannot concatenate 'str' and 'NoneType' objects",), <traceback object at 0x05047990>)
                # разбираться не стал, т.к. это разовая задача
    if issues_descriptionText is None:

        # старое - получение  key родительской issue при условии, что она = -2
      # numberIssueParent = int((str(findedNameIssue).split("-")[1]).strip()) - 2
      # findedNameIssueParent = "ACCESS-" + str(numberIssueParent)
      # IssueParent = "ACCESS-" + str(numberIssueParent)
        # КОНЕЦ старое - получение  key родительской issue при условии, что она = -2
      IssueParent = jira.issue(findedNameIssue).__dict__["raw"]["fields"]['issuelinks'][0]['outwardIssue']['key']  # получение key родительской issue
      # print "findedNameIssueParent = " + findedNameIssueParent
      # jql_OneIssue = ('issue = "ACCESS-433"')  # только заявки по которым требуется работа
      # issues_list_OneIssue = jira.search_issues(jql_OneIssue)
      # IssueParent = jira.issue("ACCESS-619")
      # print "IssueParent4 = ", IssueParent
      # IssueParent = jira.issue(findedNameIssueParent)
      # print "IssueParent3 = ", IssueParent
      # IssueParent = jira.issue("ACCESS-433")
      # print "IssueParent2 = ", IssueParent
      # IssueParent = jira.issue(findedNameIssueParent)
      # print "IssueParent = ", IssueParent
      # print "type IssueParent = ", type(IssueParent)
      print "\n\t\t--------\tздесь пусто. Рассматриваем родительскую заявку " + str(IssueParent)  # номер родительской заявки#
      logger.info("\n\t\t--------\tздесь пусто. Рассматриваем родительскую заявку " + str(IssueParent))  # номер родительской заявки#
      accountImoprtantInfo += " Saw in parent issue " + str(IssueParent) + " with name "
      # try:
      # print "\t\t\tjira.issue(findedNameIssueParent).fiIssueParentelds.description = " + str(jira.issue(findedNameIssueParent).fields.description)
      issues_descriptionText = jira.issue(IssueParent).fields.description
      if issues_descriptionText is None: issues_descriptionText += "empty in issues_descriptionText"
      # print "\t\t\tjira.issue(findedNameIssueParent).fields.description = " + str(jira.issue(findedNameIssueParent).fields.description)
      # issues_descriptionText = "empty in issues_descriptionText."
      if issues_descriptionText.find("empty in issues_descriptionText") != -1 : print "issues_descriptionText = ", issues_descriptionText
      # except Exception as e:
      #   print "!!!!!Error!   issues_descriptionText = ", issues_descriptionText
      #   logger.info("!!!!!Error!   issues_descriptionText = " + str(issues_descriptionText))
      #   print '\n\tThis is error: ', str(sys.exc_info())
      #   issues_descriptionText = " empty in issues_descriptionText "
      #   print "issues_descriptionText = ", issues_descriptionText




    words_issues_descriptionText = issues_descriptionText.rsplit()
    # print words_issues_descriptionText
    # print "\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"
    for word in words_issues_descriptionText:

      # print "word = ", word


        # определение не прописано ли в тексте, что увольнение отменяется
      if word.lower() == "увольнение":
        indexWord = words_issues_descriptionText.index(word)
        if words_issues_descriptionText[indexWord + 1].lower() == "отменено" :
          if accountImoprtantInfo.find("!!! ОТМЕНА УВОЛЬНЕНИЯ !!!") == -1:
            print "найдено Отм увольнения! в тексте"
            accountImoprtantInfo += " !!! ОТМЕНА УВОЛЬНЕНИЯ !!! "
            print accountImoprtantInfo, "\t"  # на УЗ ОТМЕНА УВОЛЬНЕНИЯ

      if word.lower() == "сообщаем":
        indexWord = words_issues_descriptionText.index(word)
        if words_issues_descriptionText[indexWord + 1].lower() == "вам," and words_issues_descriptionText[indexWord + 2].lower() == "об" and words_issues_descriptionText[indexWord + 3].lower() == "отмене" and words_issues_descriptionText[indexWord + 4].lower() == "увольнения":
          if accountImoprtantInfo.find("!!! ОТМЕНА УВОЛЬНЕНИЯ !!!") == -1:
            print "найдено Отм увольнения! в тексте"
            accountImoprtantInfo += " !!! ОТМЕНА УВОЛЬНЕНИЯ !!! "
            print accountImoprtantInfo, "\t"  # на УЗ ОТМЕНА УВОЛЬНЕНИЯ



        # определение не прописано ли в тексте, что это ТЕХНИЧЕСКОЕ увольнение
      if word.lower() == "техническое":
        indexWord = words_issues_descriptionText.index(word)
        if words_issues_descriptionText[indexWord + 1].lower() == "увольнение" :
          print "найдено Тех увольнение!"
          if accountImoprtantInfo.find("!!! ТЕХНИЧЕСКОЕ увольнение !!!") == -1:
            accountImoprtantInfo += " !!! ТЕХНИЧЕСКОЕ увольнение !!! "
            print accountImoprtantInfo, "\t"  # на УЗ ТЕХНИЧЕСКОЕ увольнение



        # оперделение даты увольнения
      if word.endswith("Сообщаем"):
        indexWord = words_issues_descriptionText.index(word)
        print "\t\tзапущено Определение даты - indexWord = ", indexWord,
        if words_issues_descriptionText[indexWord+1] == "вам," and words_issues_descriptionText[indexWord+2] == "что":
          dataDismiss = words_issues_descriptionText[indexWord+3] + " " + month_nameToNumber(words_issues_descriptionText[indexWord+4]) + " " + words_issues_descriptionText[indexWord+5]
          dataDismiss = datetime.strptime(dataDismiss, '%d %m %Y').date()

          print "\t\b ", dataDismiss, "\t"  # дата увольнения
        print

          # если в тексте прописано-вставлено об ОТМЕНА увольнения
      if word.lower() == "сообщаем":
        indexWord = words_issues_descriptionText.index(word)
        print "\t\tзапущено Определение даты при ОТМЕНА УВОЛЬНЕНИЯ - indexWord = ", indexWord,
        if words_issues_descriptionText[indexWord + 1].lower() == "вам," and words_issues_descriptionText[
          indexWord + 2].lower() == "об" and words_issues_descriptionText[indexWord + 3].lower() == "отмене" and \
            words_issues_descriptionText[indexWord + 4].lower() == "увольнения":
          dataDismiss = words_issues_descriptionText[indexWord + 5] + " " + month_nameToNumber(
            words_issues_descriptionText[indexWord + 6]) + " " + words_issues_descriptionText[indexWord + 7]
          dataDismiss = datetime.strptime(dataDismiss, '%d %m %Y').date()

          print "\t\b ", dataDismiss, "\t"     # дата увольнения
        print



        # определение имени увольняющегося
      if word == "увольняется":
        indexWord = words_issues_descriptionText.index(word)
        print "\t\tзапущено определение имени - indexWord = ", indexWord
        nameDismiss = words_issues_descriptionText[indexWord+1]
        print "\t\t\tшаг 1 nameDismiss = ", nameDismiss
        indexWord_next = indexWord + 2
        # print "words_issues_descriptionText[indexWord_next] при indexWord_next = ", indexWord_next, " получаем ", words_issues_descriptionText[indexWord_next]
        while words_issues_descriptionText[indexWord_next] != "занимающий":
          nameDismiss = nameDismiss + " " + words_issues_descriptionText[indexWord_next]
          indexWord_next += 1
          print "\t\t\t\twords_issues_descriptionText[indexWord_next] при indexWord_next = ", indexWord_next, " получаем ", words_issues_descriptionText[indexWord_next]
        nameDismiss = nameDismiss.strip(",")

        print "\t\t\t\t", nameDismiss, "\t"   # Имя увольющегос

          # если в тексте прописано-вставлено об ОТМЕНА увольнения
      if word == "по":
        indexWord = words_issues_descriptionText.index(word)
        print "\t\tзапущено определение имени в ОТМЕНЕ УВОЛЬНЕНИЯ- найдено слово 'по' indexWord = ", indexWord
        if  words_issues_descriptionText[indexWord+1] == "сотруднику":
          nameDismiss = words_issues_descriptionText[indexWord+2]
          print "\t\t\tшаг 1 nameDismiss = ", nameDismiss
          indexWord_next = indexWord + 3
          print "\t\t\t\twords_issues_descriptionText[indexWord_next] при indexWord_next = ", indexWord_next, " получаем ", words_issues_descriptionText[indexWord_next]
          while words_issues_descriptionText[indexWord_next] != "занимающий":
            nameDismiss = nameDismiss + " " + words_issues_descriptionText[indexWord_next]
            indexWord_next += 1
            print "\t\t\t\twords_issues_descriptionText[indexWord_next] при indexWord_next = ", indexWord_next, " получаем ", words_issues_descriptionText[indexWord_next]
          nameDismiss = nameDismiss.strip(",")

          print "\t\t\t\t", nameDismiss, "\t"   # Имя увольющегос



        # оперделение УЗ увольняющегося
      # accountImoprtantInfo = "" # это следующий блок; но возможно уже здесь они будут заполняться
      if word == "Учетная":
        indexWord = words_issues_descriptionText.index(word)
        print "\t\tзапущено определение Учетки - indexWord = ", indexWord
        # print "Определение аккаунта - indexWord = ", indexWord
        # print "words_issues_descriptionText[indexWord+1] = ", words_issues_descriptionText[indexWord+1]
        # print "words_issues_descriptionText[indexWord+2] = ", words_issues_descriptionText[indexWord+2]
        # print "words_issues_descriptionText[indexWord+3] = ", words_issues_descriptionText[indexWord+3]
        if words_issues_descriptionText[indexWord+1] == "запись" and words_issues_descriptionText[indexWord+2] == "сотрудника:":
          accountDismiss = words_issues_descriptionText[indexWord+3]

          # если в Jira не указана УЗ сотрудника
        if accountDismiss =="" or accountDismiss == "Если":
          accountDismiss = "в заявке не указана УЗ! Смотреть вручную."
          print "\n\t\t\t\t !!! Jira - у пользователя не указано имя УЗ !!!"
        else:
          print "\t\t\t\t", accountDismiss, "\t"     # УЗ увольющегося





          #____________________________________________
          # определение ситуации по параметрам issue
          # ___________________________________________

    Issue_name = jira.issue(findedNameIssue).fields.summary  # получение имени  родительской issue
    print "\t\t\tIssue_name = ", Issue_name

      # проверка есть ли родительская заявка
    checkIfThereIsParentIssue = jira.issue(findedNameIssue).__dict__["raw"]["fields"]['issuelinks']
    # print "checkIfThereIsParentIssue = ", checkIfThereIsParentIssue
    if checkIfThereIsParentIssue != []:
      IssueParent_name = jira.issue(findedNameIssue).__dict__["raw"]["fields"]['issuelinks'][0]['outwardIssue']['fields']['summary']  # получение имени  родительской issue
      # print "\t\t\tIssueParent_name = ", IssueParent_name
    else:
      IssueParent_name = "None"

      # оперделение что это  ТЕХНИЧЕСКОЕ увольнение
    # print "IssueParent_name.lower().find(техническое увольнение) = ", IssueParent_name.lower().find("техническое увольнение")
    # print "str(Issue_name).lower().find(техническое увольнение) = ", Issue_name.lower().find("техническое увольнение")
    if IssueParent_name.lower().find("техническое увольнение") != -1 or Issue_name.lower().find("техническое увольнение") != -1:
      if accountImoprtantInfo.find("!!! ТЕХНИЧЕСКОЕ увольнение !!!") == -1:
        print "\t\tнайдено Тех увольнение! в одном из заголовков"
        accountImoprtantInfo += " !!! ТЕХНИЧЕСКОЕ увольнение !!! "    # на УЗ ОТМЕНА УВОЛЬНЕНИЯ

      # оперделение что это ОТМЕНА УВОЛЬНЕНИЯ
    # print "str(IssueParent_name).lower().find(отмена увольнения) = ", IssueParent_name.lower().find("отмена увольнения")
    # print "str(IssueParent_name).lower().find(увольнение отменено) = ", IssueParent_name.lower().find("увольнение отменено")
    # print "str(Issue_name).lower().find(отмена увольнения) = ", Issue_name.lower().find("отмена увольнения")
    # print "str(Issue_name).lower().find(увольнение отменено) = ", Issue_name.lower().find("увольнение отмененоя")
    if IssueParent_name.lower().find("отмена увольнения") != -1 or IssueParent_name.lower().find("увольнение отменено") != -1 or Issue_name.lower().find("отмена увольнения") != -1 or Issue_name.lower().find("увольнение отменено") != -1:
      if accountImoprtantInfo.find("!!! ОТМЕНА УВОЛЬНЕНИЯ !!!") == -1:
        print "\t\tнайдено Отм увольнения! в одном из заголовков"
        accountImoprtantInfo += " !!! ОТМЕНА УВОЛЬНЕНИЯ !!! "   # на УЗ ОТМЕНА УВОЛЬНЕНИЯ

          # ____________________________________________
          # КОНЕЦ
          #     определение ситуации по параметрам issue
          # ___________________________________________




     # сохранение полученных результатов
    jira_data = [dataDismiss, str(nameDismiss), str(accountDismiss), str(accountImoprtantInfo), str(telephoneNumberDismiss), str(nccGrAll_Dismiss), str(numberFMTN), str(department)]
    # print "\t\tjira_data = ", jira_data
    results.update({str(findedNameIssue):jira_data})
    # print "\t\tjira_result = ", results

      # вывод в лог данных по Issue
    logIssueInfo (str(findedNameIssue), results[str(findedNameIssue)])
    # break



except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!! Jira -  Возникла ошибка типа: ',  str(e)
  print '\n\tJira import - This is error: ', str(sys.exc_info())
  logger.error('\n\n\t\tError by Jira import: ' + str(sys.exc_info()))
  sys.exit()

finally:
  jira.close()    # закрытие сессии Jira





  # сорторивка словаря с issues по значениям issues
results = collections.OrderedDict(sorted(results.items(), key=lambda t: t[0]))


print "\n---------------------------------------\n\tОбработка данных Jira завершена\n---------------------------------------\n\n\n"
logger.info ("\n---------------------------------------\n\tОбработка данных Jira завершена\n---------------------------------------\n\n\n")


"""
  КОНЕЦ
    Получение из Jira данных по заявкам об уволенных пользователях
_____________________________________________________________________________________________________________________________________________________"""








# sys.exit()

"""
  Получение из LDAP данных по уволенным пользователям
_____________________________________________________________________________________________________________________________________________________"""


print "\nЗапусквется поиск в AD\n_____________________________________________________________________________________________________________________________________________________\n\n"
logger.info ("\nЗапусквется поиск в AD\n_____________________________________________________________________________________________________________________________________________________\n\n")



try:

    # LDAP initializing
  LDAPConn = Connection(LDAPServer, ldapuser, ldappass, auto_bind=True)
  logger.info('Connected to LDAP %s ' % ldaphost)

  logger.info('Результат ')

  for searchInAD in results.items():
    issueNumber = searchInAD[0]
    dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo, telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department = searchInAD[1]

      # вывод на экран собранных данных по этой issue
    printInfoAboutIssue(searchInAD, issueNumber, dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo,
                        telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department)

    # logger.info('\t-------------------------------------------------------------------\n\t' + issueNumber + "\t\t\t" + dataDismiss + "\t" + nameDismiss + "\t" + accountDismiss)

    
      # пропускаем рассмотрение этой issue, если определено, что это ОТМЕНА УВОЛЬНЕНИЯ или ТЕХНИЧЕСКОЕ увольнение
    if thisCancelOrTechDismissal(accountImoprtantInfo): continue

      # пропускаем, если в заявке не указана УЗ пользователя
    if accountDismiss == "в заявке не указана УЗ! Смотреть вручную.":
      print "\t\t\t\t !!! LDAP - поиск пропускается, т.к. у пользователя не указано имя УЗ !!!"
      logIssueInfo(str(issueNumber), results[str(issueNumber)])    # вывод в лог данных по Issue
      continue

    # ldapfilter = '(&(objectClass=person)(memberOf: CN=NCC_IT,OU=NCC,OU=Service Users,DC=SD,DC=LOCAL)'  # просмотр пользователей группы NCC_IT
    # ldapfilter = '(&(objectClass=person)(cn=Беляков Сергей Евгеньевич))'  # показывает данные конкретному пользователю
    findingUserPrincipalName = searchInAD[1][2]+"@SD.LOCAL"
    print "\tfindingUserPrincipalName = ", findingUserPrincipalName
    ldapfilter = '(&(objectClass=person)(userPrincipalName=%s))'  # показывает данные по конкретному пользователю

      # поиск данных в AD
    LDAPConn_entries = toLDAP_search(ldaproot, ldapfilter, findingUserPrincipalName, attributes)

      # если пользователь не найден в AD, или найдена не одне запись
        # то пытаемся найти его другими способами
          # поиск УЗ в других (не @SD.LOCAL) доменах -------------->
    if len(LDAPConn_entries) == 0:
      print "\n\tПо заданным значениям в AD не найдено записей. Пробуем поискать в других доменах"
      nextDomen = ["@spbren.ru", "@samolet.ru", "@scor.ru"] # доманы, в которых ищется УЗ
      for nowDomen in nextDomen:
        print "\tсмотрим в домене ", nowDomen
        findingUserPrincipalName = searchInAD[1][2] + nowDomen
        print "\t\tfindingUserPrincipalName = ", findingUserPrincipalName
        LDAPConn_entries = toLDAP_search(ldaproot, ldapfilter, findingUserPrincipalName, attributes)
        print "\t\tLDAPConn_entries здесь есть!"   #, LDAPConn_entries
        if len(LDAPConn_entries) != 0:
          print "\tнайдено LDAPConn_entries"
          break
          # <--------- конец поиск УЗ в других (не @SD.LOCAL) доменах

    print "\tnow the number of records in AD found (len(LDAPConn_entries) = ", len(LDAPConn_entries)

    if len(LDAPConn_entries) == 0:
      results[issueNumber][3] += " По заданным значениям в AD не найдено записей. Требуется рассмотреть эту запись вручную"
      print "\n\t-----------------------------------------\nПо заданным значениям в AD не найдено записей. Требуется рассмотреть эту запись вручную\n-----------------------------------------"
      logIssueInfo(str(issueNumber), results[str(issueNumber)])    # вывод в лог данных по Issue
    elif len(LDAPConn_entries) > 1:
      results[issueNumber][3] += " По заданным значениям в AD найдено сразу "+ str(len(LDAPConn_entries)) + " записей. Требуется рассмотреть эту запись вручную"
      print "\n\t-----------------------------------------\nПо заданным значениям в AD найдено сразу "+ str(len(LDAPConn_entries)) + " записей. Требуется рассмотреть эту запись вручную\n-----------------------------------------"
      logIssueInfo(str(issueNumber), results[str(issueNumber)])    # вывод в лог данных по Issue


    for userData_fromLDAP in LDAPConn_entries:
      print "\tuserData_fromLDAP = ", userData_fromLDAP
       # определяем что RIP или прописяваем отдел --------->
      if str(userData_fromLDAP).find(',OU=R.I.P,') != -1:
        accountImoprtantInfo += " Аккаунт в папке R.I.P ! "
      # else:
      # import chardet
      for q in str(userData_fromLDAP).split(","):
        if q[:3] == "OU=":
          # result = chardet.detect(q)
          # print("коддировка = ", result)
          # q = q.replace("\\","")
          department = q[3:] + "\\" + department
        elif q == "DC=SD": break
        # if q[:3] == "OU=": ou.insert(0, q[3:])
      # print "q after END = ", q#
      # print "accountImoprtantInfo = ", accountImoprtantInfo#
      print "\taccountImoprtantInfo = ", accountImoprtantInfo#
        # убираем лишнюю запись "R.I.P\"
      if department.find("R.I.P") != -1:
        department = ""
      else:
        print "\tdepartment = ", department


      # print "department = ", department.decode('windows-1251')
      # print "ou_2 = ", ou
      # department += ou#
      # print "department = ", department#
      # accountImoprtantInfo += str("отдел" + ou)#
      # print "accountImoprtantInfo with отдел = ", accountImoprtantInfo#
      # # <--------- конец определяем что RIP или прописяваем отдел
      memberOfList_NCC = []
      for memberOf in userData_fromLDAP['memberOf']:
        if (memberOf.startswith("NCC_", 3, 7)):
          memberOfList_NCC.append(memberOf)
      print '\tmemberOfList_NCC = ', memberOfList_NCC
      print '\tlen memberOfList_NCC = ', len(memberOfList_NCC)

      nccGrAll_Dismiss = ""  # список NCC групп в которых прописан user
      if (len(memberOfList_NCC) == 0): memberOfList_NCC=""
      elif (len(memberOfList_NCC) > 0):
        print '\n\tUser ', accountDismiss, " registered in AD as an agent of groups NCC_ : "
        # logger.info("\tUser " + accountDismiss + " registered in AD as an agent of groups NCC_ : ")
        for nccGr in memberOfList_NCC:
          print '\t\t', nccGr
          # print '\t\t', (nccGr.split(",")[0])[3:]
          nccGrAll_Dismiss += (nccGr.split(",")[0])[3:] + " "
        #   logger.info( '\t\t' + nccGr)

      telephoneNumberDismiss = userData_fromLDAP['telephoneNumber'] # номер телефона увлльняющегося
      if len(telephoneNumberDismiss) == 0: telephoneNumberDismiss = ""
      else: print "\n\tВ AD у Пользователя прописан телефон: ", telephoneNumberDismiss

        # новая инфо дописывается к имеющимся данным
      results[issueNumber][3] = str(accountImoprtantInfo)
      results[issueNumber][4] += str(telephoneNumberDismiss)
      results[issueNumber][5] += str(nccGrAll_Dismiss)
      results[issueNumber][7] += str(department)

        # вывод в лог данных по Issue
      logIssueInfo(str(issueNumber), results[str(issueNumber)])



except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!!  LDAP - Возникла ошибка типа: ', str(e)
  print '\n\tError by LDAPimport: ', str(sys.exc_info())
  logger.error('\n\n\t\tLDAPImport - This is error: '+ str(sys.exc_info()))
  sys.exit()



print "\n---------------------------------------\n\tОбработка данных AD завершена\n---------------------------------------\n\n\n"
logger.info(
  "\n---------------------------------------\n\tОбработка данных AD завершена\n---------------------------------------\n\n\n")

"""
  КОНЕЦ
    Получение из LDAP данных по уволенным пользователям
_____________________________________________________________________________________________________________________________________________________"""








"""
  Получение из КЦ Наумен данных по уволенным пользователям
_____________________________________________________________________________________________________________________________________________________"""


print "\nЗапусквется поиск в КЦ Наумен\n_____________________________________________________________________________________________________________________________________________________\n\n"
logger.info ("\nЗапусквется поиск в КЦ Наумен\n_____________________________________________________________________________________________________________________________________________________\n\n")

logger.info('Результат ')

try:

  for searchInNaumenCC in results.items():
    issueNumber = searchInNaumenCC[0]
    dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo, telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department = searchInNaumenCC[1]

      # вывод на экран собранных данных по этой issue
    printInfoAboutIssue(searchInNaumenCC, issueNumber, dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo,
                        telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department)
    # logger.info('\t-------------------------------------------------------------------\n\t' + issueNumber + "\t\t\t" + dataDismiss + "\t" + nameDismiss + "\t" + accountDismiss)

      # пропускаем рассмотрение этой issue, если определено, что это ОТМЕНА УВОЛЬНЕНИЯ или ТЕХНИЧЕСКОЕ увольнение
    if thisCancelOrTechDismissal(accountImoprtantInfo): continue

      # пропускаем, если в заявке не указана УЗ пользователя
    if accountDismiss == "в заявке не указана УЗ! Смотреть вручную." or accountDismiss == "" or accountImoprtantInfo.find("empty in issues_descriptionText") != -1:
      errorMassage = "\t\t\t\t !!! КЦ Наумен - поиск пропускается, т.к. у пользователя не указано имя УЗ !!!"
      print errorMassage
      results[issueNumber][3] += errorMassage
      logIssueInfo(str(issueNumber), results[str(issueNumber)])    # вывод в лог данных по Issue
      continue

     # проверяем основной аккаунт
    response = toNauenCC_search_User(accountDismiss)  # чтение данных по User из NaumenCC

      # если такого User в системе НауменКЦ нет, то оповещаем об этом и пропускаем ход
    searchData=1
    if response.status_code == 404 and response.json()['status'] == 404 and response.json()['title'] == "Object not found":
      print "\t\tТакого User в системе нет. Переходим на рассмотрение следующего"
      searchData=0


    if searchData == 1:
      print "\t   Данные из НауменКЦ:"

      thisIsSecondAccaunt_m = ""   # вывод данных по основному User
      printDataFromNaumenCC(issueNumber, results, response, thisIsSecondAccaunt_m)     # вывод на экран прочитанных данных; и там же новая инфо дописывается к имеющимся данным
      # dataDismiss = datetime.strptime(dataDismiss, '%Y-%m-%d').date()
      # print "\t\tДата увольнения\t", dataDismiss
      #
      # if dataDismiss < nowData: print "\t\t\tСегодня уже ", nowData, ". Значит пора удалять эту запись из НауменКЦ"




      # проверка не создан ли этому User еще и дополнительный User_m
    accountDismiss += "_m"      # вывод данных по дополнтгельному  User_m
      # чтение данных из NaumenCC по User 	Яцкевич Сергей, у которого не стандартно прописан mobile аккаунт
    if accountDismiss=="s.yatskevich_m": accountDismiss=="yatskevich.s"

    response = toNauenCC_search_User(accountDismiss)  # чтение данных по User из NaumenCC

      # если такого User в системе нет, то оповещаем об этом и пропускаем ход
    searchData = 1
    if response.status_code == 404 and response.json()['status'] == 404 and response.json()['title'] == "Object not found":
      print "\t\t\t\tПроверено, что у данного пользователя нет дополнительной учетки mobile"
      searchData=0

    if searchData == 1:
      print "\n\t\t   Данные из НауменКЦ по дополнительному аккаунту (..._m):"
      thisIsSecondAccaunt_m = "\t\t_m\t"  # смещение для вывода данных по дополнительному User_m
      printDataFromNaumenCC(issueNumber, results, response, thisIsSecondAccaunt_m)     # вывод на экран прочитанных данных; и там же новая инфо дописывается к имеющимся данным


    # response = toNauenCC_search_User(accountDismiss)
    # allUserData = response.json().decode('UTF-8').encode('utf-8')
    # titleUser = response.json()['title'].encode('utf-8')

      # вывод в лог данных по Issue
    logIssueInfo (str(issueNumber), results[str(issueNumber)])

    response.close()


except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!!  Naumen - Возникла ошибка типа: ', str(e)
  print '\n\tError by NaumenCC import: ', str(sys.exc_info())
  logger.error('\n\n\t\tNaumenCC import - This is error: ' + str(sys.exc_info()))
  sys.exit()

# finally:

print "\n---------------------------------------\n\tОбработка данных КЦ Наумен завершена\n---------------------------------------\n\n\n"
logger.info(
  "\n---------------------------------------\n\tОбработка данных КЦ Наумен завершена\n---------------------------------------\n\n\n")

"""
КОНЕЦ
  Получение из КЦ Наумен данных по уволенным пользователям
_____________________________________________________________________________________________________________________________________________________"""






"""
   Получение данных из IPO Avaya
_____________________________________________________________________________________________________________________________________________________"""

print "\nПолучение данных из IPO Avaya\n_____________________________________________________________________________________________________________________________________________________\n\n"
logger.info ("\nПолучение данных из IPO Avaya\n_____________________________________________________________________________________________________________________________________________________\n\n")

# аутентификация в Avaya IPO
authorizationIPO()

          ###################################
          ###  чтение данных из IPO
          ###################################

# чтение данных по User из Avaya
ipoAvaya_usersDatatensionsData = sessionGet("users")

logger.info("________ по Users получено response _______\n\t\t" + str(ipoAvaya_usersDatatensionsData))
# logger.info("________ по Users получено text _______\n\t\t" + str(ipoAvaya_usersDatatensionsData.text))
# logger.info("________ по Users получено json _______\n\t\t" + str(ipoAvaya_usersDatatensionsData.json()))
# logger.info("________ по Users получено response.status_code _______\n\t\t" + str(ipoAvaya_usersDatatensionsData.status_code))
# logger.info("________ по Users получено response.cookies _______\n\t\t" + str(ipoAvaya_usersDatatensionsData.content))
# logger.info("________ по Users получено response.history _______\n\t\t" + str(ipoAvaya_usersDatatensionsData.history))
# logger.info("________ по Users получено response.headers _______\n\t\t" + str(ipoAvaya_usersDatatensionsData.headers))
logger.info("________ по Users получено response.elapsed _______\n\t\t" + str(ipoAvaya_usersDatatensionsData.elapsed))
# logger.info("________ по Users получено response.content _______\n\t\t" + str(ipoAvaya_usersDatatensionsData.content))

textUsersFromAvaya_API = ipoAvaya_usersDatatensionsData.content  # полученные данные по Users!!!

# чтение данных по Extensions из Avaya
ipoAvaya_extensionsData = sessionGet("extensions")

logger.info("________ about Extensions received response _______\n\t\t" + str(ipoAvaya_extensionsData))
# logger.info("________ about Extensions received text _______\n\t\t" + str(ipoAvaya_extensionsData.text))
# logger.info("________ about Extensions received json _______\n\t\t" + str(ipoAvaya_extensionsData.json()))
# logger.info("________ about Extensions received response.status_code _______\n\t\t" + str(ipoAvaya_extensionsData.status_code))
# logger.info("________ about Extensions received response.cookies _______\n\t\t" + str(ipoAvaya_extensionsData.cookies))
# logger.info("________ about Extensions received response.history _______\n\t\t" + str(ipoAvaya_extensionsData.history))
# logger.info("________ about Extensions received response.headers _______\n\t\t" + str(ipoAvaya_extensionsData.headers))
logger.info("________ about Extensions received response.elapsed _______\n\t\t" + str(ipoAvaya_extensionsData.elapsed))
# logger.info("________ about Extensions received response.content _______\n\t\t" + str(ipoAvaya_extensionsData.content))

textExtensionsFromAvaya_API = ipoAvaya_extensionsData.content  # полученные данные по Extensions

          ##################################
          ##  КОНЕЦ
          ##    чтение данных из IPO
          ##################################


      # ------------------------------------------------
      ### ----------> работа с файлами, чтобы не постоянно читать данные с системы IPO
      # ------------------------------------------------

 # сохранения данных в файлы
file1 = open(r'.\Avaya_userData_response.content.data', 'w')
print "\t\twrite  Avaya_userData_response.content.data"
file2 = open(r'.\Avaya_extensionsData_response.content.data', 'w')
print "\t\twrite  Avaya_extensionsData_response.content.data"
try:
  file1.write(str(ipoAvaya_usersDatatensionsData.content))
  file2.write(str(ipoAvaya_extensionsData.content))
except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
  print ('\n\tError by file write: ' + str(sys.exc_info()))
  sys.exit()
finally:
  file1.close()
  file2.close()
 # ________________________________ конец  сохранения данных в файллы
#
#  # чтение данных из файлов
# file1 = open(r'.\Avaya_userData_response.content.data', 'r')
# logger.info("\n\n-----------------------read data from file   Avaya_userData_response.content.data")
# file2 = open(r'.\Avaya_extensionsData_response.content.data', 'r')
# logger.info("\n\n-----------------------read data from file   Avaya_extensionsData_response.content.data")
# print "read data from files   Avaya_..._response.content.data"
# try:
#   textUsersFromAvaya_API = file1.read()
#   textExtensionsFromAvaya_API = file2.read()
# except Exception as e:
#   print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
#   print ('\n\tError by file read: ' + str(sys.exc_info()))
#   sys.exit()
# finally:
#   file1.close()
#   file2.close()
# ________________________________ конец  чтение данных и файлов
#
#       # ------------------------------------------------
#       ### <---------- КОНЕЦ работа с файлом
#       # ------------------------------------------------


          ###############################################
          ###    парсинг полученных данных Avaya IPO API
          ###############################################


# подготовка к парсингу данных  (из-за того, что в файлах эти значения указаны без кавычек)
false = "false"
true = "true"

dictUsersFromAvayaIPO_API = {}  # определяем dict чтобы не отображались ошибки при выполнении проги
dictExtensionsFromAvayaIPO_API = {}  # определяем dict чтобы не отображались ошибки впри выполнении проги

            # ---------------------------------------
            # парсинг данных из IPO API по Users
            # ---------------------------------------

exec ('dictUsersFromAvayaIPO_API = ' + textUsersFromAvaya_API)
# print " type(dictUsersFromAvayaIPO_API) = ", type(dictUsersFromAvayaIPO_API)
logger.info("--- received dictUsersFromAvayaIPO_API ___________________________________________\n\t")
print ("--- received dictUsersFromAvayaIPO_API _____")

# в логе выводится оглавление и заголовок таблицы данных
logger.info(
  "\n\n___________________________________________\n\t\t\t\t\t\t\t\t\t\t\t\t\t\tReceived from API IPO:\n\t\t\t\t\t\t\t\t\t\t\t\t" + "GUID" + "\t" + "Extension" + "\t" + "FullName" + "\t" + "Name")

for dataUser in dictUsersFromAvayaIPO_API["response"]["data"]["ws_object"]:
  giud = "-zero-"
  extension = "-zero-"
  fullName = "-zero-"
  name = "-zero-"
  # print ("--- received dataUser in textUsersFromAvaya_API ___________")
  giud = str(dataUser['User']['@GUID'])
  # print "\t\t\tgiud = " + giud
  extension = str(dataUser['User']['Extension'])
  # print "\t\t\textension = " + extension
  fullName = str(dataUser['User']['FullName'])
  # print "\t\t\tfullName = " + fullName
  name = str(dataUser['User']['Name'])
  # print "\t\t\tname = " + name

  # сохранение полученных результатов в словаре dataFromAvaya, где за ключ берется extension
  dataFromAvayaUsers.update({extension: [giud, extension, fullName, name]})

  # отправка данных в лог
  logger.info(
    "---\t" + str(dataFromAvayaUsers[extension][0]) + "\t" + str(dataFromAvayaUsers[extension][1]) + "\t" + str(
      dataFromAvayaUsers[extension][2]) + "\t" + str(dataFromAvayaUsers[extension][3]))

            # ---------------------------------------
            # КОНЕЦ
            #     парсинг данных из IPO API по Users
            # ---------------------------------------

            # ---------------------------------------
            # парсинг данных из IPO API по Extensions
            # ---------------------------------------

logger.info("\n--- received textExtensionsFromAvaya_API ___________________________________________")
# logger.info("\n--- received textExtensionsFromAvaya_API ___________________________________________\n\t" + str(textExtensionsFromAvaya_API))
# print ("\n--- received textExtensionsFromAvaya_API _____")


exec ('dictExtensionsFromAvayaIPO_API = ' + textExtensionsFromAvaya_API)
logger.info("\n--- received dictExtensionsFromAvayaIPO_API ___________________________________________\n\t" + str(
  dictExtensionsFromAvayaIPO_API))
# print ("--- received dictExtensionsFromAvayaIPO_API _____")

# захват первого-отдельного описанного в dictExtensionsFromAvayaIPO_API значения Extansion
dataFromAvayaExtensions.update({str(dictExtensionsFromAvayaIPO_API["response"]["data"]["ws_object"]["Extension"][1]):
                                  [str(dictExtensionsFromAvayaIPO_API["response"]["data"]["ws_object"]["Extension"][0][
                                         "@GUID"]),
                                   str(
                                     dictExtensionsFromAvayaIPO_API["response"]["data"]["ws_object"]["Extension"][1])]})

# парсинг остальных описанных в dictExtensionsFromAvayaIPO_API значений Extansions
for dataExtension in dictExtensionsFromAvayaIPO_API["ws_object"]:
  # logger.info("--- получено dataExtension from Смирнова ___________________________________________\n\t"+ str(dataExtension))
  # print ("--- received dataExtension from textExtensionsFromAvaya_API ___________________________________________")
  extension = str(dataExtension['Extension'][1])
  # print "\t\t\textension = " + extension
  guid = str(dataExtension['Extension'][0]['@GUID'])
  # print "\t\t\tguid = " + guid

  # сохранение полученных результатов в словаре dataFromAvaya, где за ключ берется extension
  dataFromAvayaExtensions.update({extension: [guid, extension]})

          # ----------------------------
          # КОНЕЦ
          #     парсинг данных из IPO API по Extensions
          # ----------------------------

        ###############################################
        ###  КОНЕЦ
        ###    парсинг полученных данных Avaya IPO API
        ###############################################



        ######################################################################################
        ###    Поиск соответствий полученных ранее данных (из AD, Jira) и данных из Avaya IPO
        ######################################################################################

print ("\n_____________ Проверка совпадений имеющихся данных; и данных из IPO Avaya")
logger.info ("\n_____________ Проверка совпадений имеющихся данных; и данных из IPO Avaya")

for issueJira_data in results.items():
  issueNumber = issueJira_data[0]
  dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo, telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department = issueJira_data[1]

    # вывод на экран собранных данных по этой issue
  printInfoAboutIssue(issueJira_data, issueNumber, dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo,
                      telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department)

    # пропускаем рассмотрение этой issue, если определено, что это ОТМЕНА УВОЛЬНЕНИЯ или ТЕХНИЧЕСКОЕ увольнение
  if thisCancelOrTechDismissal(accountImoprtantInfo): continue

  logger.info ("\tissueNumber = " + issueNumber)    # вывод в лог инфо с какой issue сейчас работаем

    # берется внутренний номер(а) взятый из AD
  findPhoneNumberFromData = str(telephoneNumberDismiss).strip()                   # внутренний номер

    # из имени пользователя берется отделно его его фамилия и его имя
  findUserSurnameFromData = str(nameDismiss).strip().split()[0].decode('utf-8').lower()       #  фамилия пользователя
  findUserNameFromData = str(nameDismiss).strip().split()[1].decode('utf-8').lower()          #  имя пользователя

    # из учетки  пользователя берется его фамилия (в латинице)
  findUserLatinSurnameFromData = str(accountDismiss).split(".")       # из учетки пользовтеля вырезается фамилия
  # print "findUserLatinSurnameFromData = ", findUserLatinSurnameFromData
    # если в учетке пользователя есть разделение инициялы.фамилия знаком "."
  if len(findUserLatinSurnameFromData)>=2:
        # если получили "нестандартное" имя учетки, типа Sedyakina.YS (т.е. первая - фамилия, далее инициалы)
    if len((findUserLatinSurnameFromData[0])) > 2 and (findUserLatinSurnameFromData[1]) <= 2:
      findUserLatinSurnameFromData = (findUserLatinSurnameFromData[0]).strip().decode('utf-8').lower()
    else:   # иначе принимаем, что учетки стандартнного вида: перваяБукваИмени.фамилия
      findUserLatinSurnameFromData = (findUserLatinSurnameFromData[1]).strip().decode('utf-8').lower()
  else:  # а если в учетке пользователя отсутствует знак "."
    findUserLatinSurnameFromData = (findUserLatinSurnameFromData[0]).strip().decode('utf-8').lower()

  #   # создаем list из значений, которые ищем.
  # whatFind = [findPhoneNumberInUsersIPO, findUserSurnameInUsersIPO, findUserNameInUsersIPO, findUserLatinSurnameFromData]
  # print "whatFind = ", whatFind

  print ("\t_________________________________рассматривается:")


#  dataFromAvayaUsers. = ({extension: [giud, extension, fullName, name]})  - оставил просто чтобы смотреть какие данные там

  print "\t\tfindPhoneNumberFromData =  ", findPhoneNumberFromData
  print "\t\tfindUserSurnameFromData =  ", findUserSurnameFromData
  print "\t\tfindUserNameFromData =  ", findUserNameFromData
  print "\t\tfindUserLatinSurnameFromData =  ", findUserLatinSurnameFromData


    # проверка прописан ли такой номер на IPO Avaya
  if findPhoneNumberFromData not in dataFromAvayaUsers:
    message = " (в IPO такого номера нет) "
    print ("\n\t\t\t\t " + message + " Extension " + findPhoneNumberFromData)
    logger.info("\n\t\t\t\t " + message + " Extension " + findPhoneNumberFromData)
    telephoneNumberDismiss += message


    # проверка совпадений данных из Jira,AD , и данных из IPO
  for ext in dataFromAvayaUsers:

    try:    # чтобы пропускать Extensions 00000xx
      if ext == ""  :           # если в записи в поле Extension ничего не прописано
        print "\t\t\tполе Extension на стороне IPO Avaya пусто"
        continue

        # далее ситуации рассматриваются в приоритете "наиболее хороший вариант"
        # все значения переводятся в нижний регистр для более полной проверки

        #-----------------------------------------
        # если совпали extension, фамилия, и имя
                                # сколько раз "(не)попало"  + 4 -0
        # -----------------------------------------
      if findPhoneNumberFromData == ext \
            and (str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()).find(findUserSurnameFromData) != -1 \
            and (str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()).find(findUserNameFromData) != -1:
        print "\n\t\t\tExtension =  ", ext
        print "\t\t\t\tfstr(dataFromAvayaUsers[ext][2]).decode('utf-8').lower() =  ", str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()
        print "\t\t\t\tfstr(dataFromAvayaUsers[ext][3]).decode('utf-8').lower() =  ", str(dataFromAvayaUsers[ext][3]).decode('utf-8').lower()
        message = "User найден в IPO (по номер + фамилия + имя). Можно удалять его из IPO Avaya. ( " + ext + " ) "
        print ("\t\t\t\t " + message + " Extension " + ext)
        logger.info("\t\t\t\t " + message + " Extension " + ext)
        accountImoprtantInfo = message + " | " + accountImoprtantInfo

        #-----------------------------------------
        # если совпали extension, и учетка  (т.е. сюда попадает и смена фамилии)
        # -----------------------------------------
      elif findPhoneNumberFromData == ext \
            and ((str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()).find(findUserLatinSurnameFromData) != -1 \
            or (str(dataFromAvayaUsers[ext][3]).decode('utf-8').lower()).find(findUserLatinSurnameFromData) != -1):
        print "\t\tExtension =  ", ext
        print "\t\tfstr(dataFromAvayaUsers[ext][2]).decode('utf-8').lower() =  ", str(
          dataFromAvayaUsers[ext][2]).decode('utf-8').lower()
        print "\t\tfstr(dataFromAvayaUsers[ext][3]).decode('utf-8').lower() =  ", str(
          dataFromAvayaUsers[ext][3]).decode('utf-8').lower()
        message = "User найден в IPO (по номер + учетка). Можно удалять его из IPO Avaya. ( " + ext + " ) "
        print ("\t\t\t\t " + message + " Extension " + ext)
        logger.info("\t\t\t\t " + message + " Extension " + ext)
        accountImoprtantInfo = message + " | " + accountImoprtantInfo

        #----------------------------------------------------------------
        # если в FullName есть и имя и фамилия и в Name есть имя учетки
        #----------------------------------------------------------------
      elif (str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()).find(findUserSurnameFromData) != -1 \
          and (str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()).find(findUserNameFromData) != -1 \
          and (str(dataFromAvayaUsers[ext][3]).decode('utf-8').lower()).find(findUserLatinSurnameFromData) != -1 \
          and (str(accountDismiss)) != "":
        print "\t\tExtension =  ", ext
        print "\t\tfstr(dataFromAvayaUsers[ext][2]).decode('utf-8').lower() =  ", str(
          dataFromAvayaUsers[ext][2]).decode('utf-8').lower()
        print "\t\tfstr(dataFromAvayaUsers[ext][3]).decode('utf-8').lower() =  ", str(
          dataFromAvayaUsers[ext][3]).decode('utf-8').lower()
        message = "User найден в IPO (по фамилии, имени + учетка). Надо проверить в AD, - рассмотреть его к удалению из IPO Avaya. ( " + ext + " ) "
        print ("\t\t\t\t " + message + " Extension " + ext)
        logger.info("\t\t\t\t " + message + " Extension " + ext)
        accountImoprtantInfo = message + " | " + accountImoprtantInfo

        #----------------------------------------------------------------
        # если в FullName есть имя и в Name есть имя учетки (т.е. похоже сменилась фамилия)
        #----------------------------------------------------------------
      elif (str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()).find(findUserNameFromData) != -1 \
          and (str(dataFromAvayaUsers[ext][3]).decode('utf-8').lower()).find(findUserLatinSurnameFromData) != -1 \
          and (str(accountDismiss)) != "":
        print "\t\tExtension =  ", ext
        print "\t\tfstr(dataFromAvayaUsers[ext][2]).decode('utf-8').lower() =  ", str(
          dataFromAvayaUsers[ext][2]).decode('utf-8').lower()
        print "\t\tfstr(dataFromAvayaUsers[ext][3]).decode('utf-8').lower() =  ", str(
          dataFromAvayaUsers[ext][3]).decode('utf-8').lower()
        message = "User найден в IPO (по имени + учетка). Надо проверить в AD, - рассмотреть его к удалению из IPO Avaya. ( " + ext + " ) "
        print ("\t\t\t\t " + message + " Extension " + ext)
        logger.info("\t\t\t\t " + message + " Extension " + ext)
        accountImoprtantInfo = message + " | " + accountImoprtantInfo

        #--------------------------------------------------------------------
        # если есть такой extension, но учетка и фамилия на нем не совпадают
        #--------------------------------------------------------------------
      elif findPhoneNumberFromData == ext \
          and (str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()).find(findUserSurnameFromData) == -1 \
          and (str(dataFromAvayaUsers[ext][3]).decode('utf-8').lower()).find(findUserLatinSurnameFromData) == -1:
        print "\t\tExtension =  ", ext
        print "\t\tfstr(dataFromAvayaUsers[ext][2]).decode('utf-8').lower() =  ", str(
          dataFromAvayaUsers[ext][2]).decode('utf-8').lower()
        print "\t\tfstr(dataFromAvayaUsers[ext][3]).decode('utf-8').lower() =  ", str(
          dataFromAvayaUsers[ext][3]).decode('utf-8').lower()
        message = " (В IPO на номере другое имя) "
        print ("\t\t\t\t " + message + " Extension " + ext)
        logger.info("\t\t\t\t " + message + " Extension " + ext)
        telephoneNumberDismiss += message

      #   #-------------------------------------------------------
      #   # если в FullName есть фамилия и в Name есть имя учетки
      #     # похоже лучше удалить
      #   #-------------------------------------------------------
      # elif (str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()).find(findUserSurnameFromData) != -1 \
      #       and (str(dataFromAvayaUsers[ext][3]).decode('utf-8').lower()).find(findUserLatinSurnameFromData) != -1:
      #   print "\t\tExtension =  ", ext
      #   print "\t\tfstr(dataFromAvayaUsers[ext][2]).decode('utf-8').lower() =  ", str(
      #     dataFromAvayaUsers[ext][2]).decode('utf-8').lower()
      #   print "\t\tfstr(dataFromAvayaUsers[ext][3]).decode('utf-8').lower() =  ", str(
      #     dataFromAvayaUsers[ext][3]).decode('utf-8').lower()
      #   message = "User найден в IPO (по фамилии + учетка). Надо проверить в AD, - рассмотреть его к удалению из IPO Avaya. ( " + ext + " ) "
      #   print ("\t\t\t\t " + message + " Extension " + ext)
      #   logger.info("\t\t\t\t " + message + " Extension " + ext)
      #   accountImoprtantInfo = message + " | " + accountImoprtantInfo

        #--------------------------------
        # если в Name есть имя учетки
                              # сколько раз "(не)попало"  + 0 -14
        #     # похоже лучше удалить
        #--------------------------------
      # elif findUserLatinSurnameFromData != "" \
      #     and (str(dataFromAvayaUsers[ext][3]).decode('utf-8').lower()).find(findUserLatinSurnameFromData) != -1:
      #   print "\t\tExtension =  ", ext
      #   print "\t\tfstr(dataFromAvayaUsers[ext][2]).decode('utf-8').lower() =  ", str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()
      #   print "\t\tfstr(dataFromAvayaUsers[ext][3]).decode('utf-8').lower() =  ", str(dataFromAvayaUsers[ext][3]).decode('utf-8').lower()
      #   message = "User найден в IPO (по учетке). Надо проверить в AD, - рассмотреть его к удалению из IPO Avaya. ( " + ext + " ) "
      #   print ("\t\t\t\t " + message + " Extension " + ext)
      #   logger.info("\t\t\t\t " + message + " Extension " + ext)
      #   accountImoprtantInfo = message + " | " + accountImoprtantInfo

        #---------------------------------------
        # если в FullName есть и имя и фамилия
        #---------------------------------------
      elif (str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()).find(findUserSurnameFromData) != -1 \
          and (str(dataFromAvayaUsers[ext][2]).decode('utf-8').lower()).find(findUserNameFromData) != -1:
        print "\t\tExtension =  ", ext
        print "\t\tfstr(dataFromAvayaUsers[ext][2]).decode('utf-8').lower() =  ", str(
          dataFromAvayaUsers[ext][2]).decode('utf-8').lower()
        print "\t\tfstr(dataFromAvayaUsers[ext][3]).decode('utf-8').lower() =  ", str(
          dataFromAvayaUsers[ext][3]).decode('utf-8').lower()
        message = "User найден в IPO (по фамилии, имени). Надо проверить в AD, - рассмотреть его к удалению из IPO Avaya. ( " + ext + " ) "
        print ("\t\t\t\t " + message + " Extension " + ext)
        logger.info("\t\t\t\t " + message + " Extension " + ext)
        accountImoprtantInfo = message + " | " + accountImoprtantInfo


    except:
      None




      # метка, если Пользователь в системах телефонии не найден
      # Условия:
      #     + не найден телефонный номер
      #       или номер у пользователя прописан, но определено что "в IPO такого номера нет" или "В IPO на номере другое имя"
      #     + не найдена предполагаемая учетка в IPO Avaya
      #     + не нуйдана регистрация учетки в Naumen
      #     + не найдено метки, что у пользователя есть FMTN или Zoiper номер
  if (telephoneNumberDismiss == "" or telephoneNumberDismiss.find("В IPO на номере другое имя") != -1 or telephoneNumberDismiss.find("в IPO такого номера нет") != -1) \
      and accountImoprtantInfo.find("User найден в IPO") == -1 \
      and nccGrAll_Dismiss == "" and numberFMTN == "": accountImoprtantInfo += " Пользователь в системах телефонии не найден"

    # новая инфо дописывается к имеющимся данным
  results[issueNumber][3] = str(accountImoprtantInfo)
  results[issueNumber][4] = str(telephoneNumberDismiss)

    # вывод в лог данных по Issue
  logIssueInfo(str(issueNumber), results[str(issueNumber)])

        ######################################################################################
        ###  КОНЕЦ
        ###    Поиск соответствий полученных ранее данных (из AD, Jira) и данных из Avaya IPO
        ######################################################################################



print "\n---------------------------------------\n\tПолучение данных из IPO Avaya завершена\n---------------------------------------\n\n\n"
logger.info(
  "\n---------------------------------------\n\tПолучение данных из IPO Avaya завершена\n---------------------------------------\n\n\n")




"""
КОНЕЦ
  Получение данных из IPO Avaya
_____________________________________________________________________________________________________________________________________________________"""







# sys.exit()





"""
    Внесение изменений в системы Наумен и Avaya IPO 
_____________________________________________________________________________________________________________________________________________________"""

print "\n_____________ Внесение изменений в системы Наумен и Avaya IPO _____________________________________________________________________________________\n"
logger.info ("\n_____________ Внесение изменений в системы Наумен и Avaya IPO")




try:

  for searchInNaumenCC in results.items():
    issueNumber = searchInNaumenCC[0]
    dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo, telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department = searchInNaumenCC[1]

      # вывод на экран собранных данных по этой issue
    printInfoAboutIssue(searchInNaumenCC, issueNumber, dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo,
                        telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department)

      # пропускаем рассмотрение этой issue, если определено, что это ОТМЕНА УВОЛЬНЕНИЯ или ТЕХНИЧЕСКОЕ увольнение
    if thisCancelOrTechDismissal(accountImoprtantInfo): continue

      # вывод в лог данных по Issue
    logIssueInfo(str(issueNumber), results[str(issueNumber)])
    # logger.info("\tissueNumber = " + issueNumber)  # вывод в лог инфо с какой issue сейчас работаем

    print "\t\t\tNow is (datetime.now().date()) = ", datetime.now()
    logger.info("\t\t\tNow is (datetime.now().date()) = " + str(datetime.now()))

    # если эта учетка  в системах телефонии  найдена, то рассмариваем дату увольнения пользователя.
    if accountImoprtantInfo.find("Пользователь в системах телефонии не найден") == -1:
      # проверка что дата увольнения уже в прошлом
      # если прихложит True - значит дата увольнения еще в будущем, и переходим к пассмотрению следующей Issue
      # если прихожит False, то значит дата увольнения уже наступила, или была в прошлом, и продолжаем рассмотрение данной Issue, и вносим изменения с системы
      if chackDataForChanger():
        # делаем пометку о том, что еще рано вносить изменения по данной учетке + новая инфо дописывается к имеющимся данным
        results[issueNumber][3] = str(
          "Еще рано обрабатывать данную Issue. Она получает статус В ожидании | " + accountImoprtantInfo)
        continue

      # но если учетка в системе телефонии найдена, и дата увольнения уже наступила (т.е. можно вносить изменения в учетку)
      #  то изначально удаляем все не нужные (старые) метки
    if accountImoprtantInfo.find("Еще рано обрабатывать данную Issue. Она получает статус В ожидании | ") != -1: accountImoprtantInfo = deleteMark(str(accountImoprtantInfo), "Еще рано обрабатывать данную Issue. Она получает статус В ожидании | ")


      #--------------------------------
      # Внести изменения в Avaya IPO
      # --------------------------------

          #--------------------
          # удаление User
          #--------------------
    if accountImoprtantInfo.find("User найден в IPO (по номер + фамилия + имя). Можно удалять его из IPO Avaya.") != -1:
      print "\t\tFrom Avaya IPO deleting user with number", telephoneNumberDismiss
      logger.info("\t\tFrom Avaya IPO deleting user with number " + telephoneNumberDismiss)
      accountImoprtantInfo = "From Avaya IPO deleting user with number " + telephoneNumberDismiss + " | " + accountImoprtantInfo
      # accountImoprtantInfo += "TEST (не выполнено) - From Avaya IPO deleting user with number " + telephoneNumberDismiss
      print "\t\tGUID = " + dataFromAvayaUsers[telephoneNumberDismiss][0]
      deleteUser = sessionDelete("users", dataFromAvayaUsers[telephoneNumberDismiss][0]) # удаление User
      # logger.info("\ttext delete User JSON:\n\t\t\t" + str(deleteUser.text))
      logger.info("\t\tabout delete User JSON:\n\t\t\t" + str(deleteUser.json()))
      # logger.info("\tabout delete User status_code:\n\t\t\t" + str(deleteUser.status_code))
      # logger.info("\tabout delete User content:\n\t\t\t" + str(deleteUser.content))
      # logger.info("\tabout delete User cookies:\n\t\t\t" + str(deleteUser.cookies))
      # logger.info("\tabout delete User history:\n\t\t\t" + str(deleteUser.history))
      # logger.info("\tabout delete User :\n\t\t\t" + str(deleteUser.headers))
      logger.info("\t\tabout delete User   elapsed:\n\t\t\t" + str(deleteUser.elapsed))

          # --------------------
          # удаление Extension
          # --------------------
      print "\t\tFrom Avaya IPO deleting extension ", telephoneNumberDismiss
      logger.info("\t\tFrom Avaya IPO deleting extension " + telephoneNumberDismiss)
      accountImoprtantInfo = "From Avaya IPO deleting extension " + telephoneNumberDismiss + " | " + accountImoprtantInfo
      # accountImoprtantInfo += "TEST (не выполнено) - From Avaya IPO deleting extension " + telephoneNumberDismiss
      print "\t\tGUID = " + dataFromAvayaExtensions[telephoneNumberDismiss][0]
      deleteExtension = sessionDelete("extensions", dataFromAvayaExtensions[telephoneNumberDismiss][0])
      # logger.info("\ttext delete Extension JSON:\n\t\t\t" + str(deleteExtension.text))
      logger.info("\t\tabout delete Extension JSON:\n\t\t\t" + str(deleteExtension.json()))
      # logger.info("\tabout delete Extension status_code:\n\t\t\t" + str(deleteExtension.status_code))
      # logger.info("\tabout delete Extension content:\n\t\t\t" + str(deleteExtension.content))
      # logger.info("\tabout delete Extension cookies:\n\t\t\t" + str(deleteExtension.cookies))
      # logger.info("\tabout delete Extension history:\n\t\t\t" + str(deleteExtension.history))
      # logger.info("\tabout delete Extension :\n\t\t\t" + str(deleteExtension.headers))
      logger.info("\t\tabout delete Extension elapsed:\n\t\t\t" + str(deleteExtension.elapsed))

      # --------------------------------
      # КОНЕЦ
      #     Внести изменения в Avaya IPO
      # --------------------------------




      # --------------------------------
      # Внести изменения в Наумен КЦ
      # --------------------------------

      # пропускаем, если в заявке не указана УЗ пользователя
    if accountDismiss == "в заявке не указана УЗ! Смотреть вручную." or accountDismiss == "" or accountImoprtantInfo.find("empty in issues_descriptionText") != -1:
      errorMassage = "\t\t !!! У пользователя не указано имя УЗ. Не рассматриваем. !!!\n"
      print errorMassage
      logger.info(errorMassage)
      continue


    print ("\t\tnccGrAll_Dismiss = " + nccGrAll_Dismiss)
    logger.info ("\t\tnccGrAll_Dismiss = " + nccGrAll_Dismiss)
    if nccGrAll_Dismiss != "":
      print ("\t\tNow this accaunt must delete from Naumen CC")
      logger.info("\t\tNow this accaunt must delete from Naumen CC")
      resultRemoveUserFormNaumen = remove_user_request(accountDismiss)   # раскомментировать  по окончании тестирования
      # resultRemoveUserFormNaumen = "TEST (не выполнено) - В системе Наумен удалена учетка"   # проверено 1 раз
      print ("\t\t" + resultRemoveUserFormNaumen)
      logger.info("\t\t" + resultRemoveUserFormNaumen)
      accountImoprtantInfo += " " + resultRemoveUserFormNaumen


      # --------------------------------
      # КОНЕЦ
      #     Внести изменения в   Наумен КЦ
      # --------------------------------



      # новая инфо дописывается к имеющимся данным
    results[issueNumber][3] = str(accountImoprtantInfo)



except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!!  when changing NaumenCC or Avaya IPO - A type error occurred: ', str(e)
  print '\n\tError when changing changer NaumenCC or Avaya IPO : ', str(sys.exc_info())
  logger.error('\n\n\t\tError when changing NaumenCC or Avaya IPO: ' + str(sys.exc_info()))
  sys.exit()

# finally:

print "\n---------------------------------------\n\tВнесение изменений в системы Наумен и Avaya IPO завершена\n---------------------------------------\n\n\n"
logger.info(
  "\n---------------------------------------\n\tВнесение изменений в системы Наумен и Avaya IPO завершена\n---------------------------------------\n\n\n")


"""
  КОНЕЦ
    Внесение изменений в системы Наумен и Avaya IPO
_____________________________________________________________________________________________________________________________________________________"""








# sys.exit()







"""
   Решение-закрытие issues Jira 
_____________________________________________________________________________________________________________________________________________________"""


print "\n-------- Решение-закрытие issues Jira\n_____________________________________________________________________________________________________________________________________________________\n\n"
logger.info ("\n-------- Решение-закрытие issues Jira\n_____________________________________________________________________________________________________________________________________________________")







try:

  jira = enterJira(jira_options, loginJira, passJira)  # подключение к Jira

  for issueJira_data in results.items():
    issueNumber = issueJira_data[0]
    dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo, telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department = issueJira_data[1]

      # вывод на экран собранных данных по этой issue
    printInfoAboutIssue(issueJira_data, issueNumber, dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo,
                        telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department)

    # logger.info('\t-------------------------------------------------------------------\n\t' + issueNumber + "\t\t\t" + dataDismiss + "\t" + nameDismiss + "\t" + accountDismiss)


      # запрос в Jira определенной issue
    changingIssue = jira.issue(issueNumber)

    print "\n\t\t------------рассматриваем ", changingIssue, "------------"
    logger.info ("\n\t\t------------рассматриваем " + str(changingIssue) + "------------")

    changingIssue_decision_YN = 0  # определяет требуется ли Решение в issue  (изначально ставим 0 = нет)

      # определение статуса issue
    changingIssue_status = jira.issue(changingIssue).fields.status.id
    print "\t\t\tстатус issue (changingIssue_status) = ", changingIssue_status  # показывает статус  issue

    print "\t\t\tjira.issue(changingIssue).fields.assignee = ", jira.issue(changingIssue).fields.assignee  # показывает исполнитель issue



      # если задача в статусе "Зарегистрирована" (код 1)
    if changingIssue_status == "1":
        # если issue ни на кого не назанчена
      if str(jira.issue(changingIssue).fields.assignee) == "None":
          # выполняем "Назначить на меня"
        print "\t\t\tchange transition_issue(changingIssue, transition='171')"
        jira.transition_issue(changingIssue, transition='171')

        # далее, когда есть исполнитель,
        # выполняем "В работу"
      print "\t\t\tchange transition_issue(changingIssue, transition='21')"
      jira.transition_issue(changingIssue, transition='21')



      # если задача в статусе "В ожидании" (код 10103)
    if changingIssue_status == "10103":
      #   # если заявка уже отправелена "В ожидание" до даты увольнения, - то пропускаем ее
      # print "\n\t\t\tjira.issue(changingIssue).fields.customfield_19624.id = ", jira.issue(changingIssue).fields.customfield_19624.id
      # if jira.issue(changingIssue).fields.customfield_19624.id == "45405":
      #   print "\n\t\t\tЗаявка уже отправлена В ожидание до даты увольнения "
      #   logger.info(" Заявка уже отправлена В ожидание до даты увольнения")
      #   if accountImoprtantInfo.find("Заявка уже отправлена В ожидание до даты увольнения | ") == -1: results[issueNumber][3] = str("Заявка уже отправлена В ожидание до даты увольнения | " + accountImoprtantInfo)
      #   continue
        # если не назначен исполнитель, выполняем "Назначить на меня"
      print "\n\t\t\tjira.issue(changingIssue).fields.assignee = ", jira.issue(changingIssue).fields.assignee
      if jira.issue(changingIssue).fields.assignee is None or str(jira.issue(changingIssue).fields.assignee) == "":
          print "\t\t\tchange transition_issue(changingIssue, transition='171') "
          jira.transition_issue(changingIssue, transition='171')
        # выполняется "Вернуть в работу" (меняется статус на "Зарегистрирована")
      print "\t\t\tchangingIssue_status2 = ", jira.issue(changingIssue).fields.status
      jira.transition_issue(changingIssue, transition='71')
      # time.sleep(3)
        # выполняется "В работу" (меняется статус на "В работе")
      print "\t\t\tchangingIssue_status3 = ", jira.issue(changingIssue).fields.status
      jira.transition_issue(changingIssue, transition='21')
      # time.sleep(3)
      print "\t\t\tchangingIssue_status4 = ", jira.issue(changingIssue).fields.status

      # если задача в статусе "Первичная обработка" (код 10713)
    if changingIssue_status == "10713":
        # если не назначен исполнитель, выполняем "Назначить на меня"
      print "\n\t\t\tjira.issue(changingIssue).fields.assignee = ", jira.issue(changingIssue).fields.assignee
      if jira.issue(changingIssue).fields.assignee is None or jira.issue(changingIssue).fields.assignee != "":
        print "\t\t\tchange transition_issue(changingIssue, transition='171') "
        jira.transition_issue(changingIssue, transition='171')
      print "\t\t\tchangingIssue_status2 = ", jira.issue(changingIssue).fields.status
        # выполняется "Обработать" (меняется статус на "Зарегистрирована")
      jira.transition_issue(changingIssue, transition='321')
      # time.sleep(3)
      print "\t\\ttchangingIssue_status3 = ", jira.issue(changingIssue).fields.status
      # если не назначен исполнитель, выполняем "Назначить на меня"
      if jira.issue(changingIssue).fields.assignee is None or jira.issue(changingIssue).fields.assignee != "":
        print "\t\t\tchange transition_issue(changingIssue, transition='171') "
        jira.transition_issue(changingIssue, transition='171')
        # выполняется "В работу" (меняется статус на "В работе")
      jira.transition_issue(changingIssue, transition='21')
      # time.sleep(3)
      print "\t\t\tchangingIssue_status4 = ", jira.issue(changingIssue).fields.status




      # обработка issue , на которых стоит метка "Еще рано обрабатывать данную Issue. Она получает статус В ожидании | "
      #   (т.е. данная Issue отправляется-получаетСтатус "В ожидании"
      # ------------------------------------------------------
    if accountImoprtantInfo.find("Еще рано обрабатывать данную Issue. Она получает статус В ожидании | ") != -1:
      print "\t\t\t Еще рано обрабатывать данную Issue. Она получает статус В ожидании"
      logger.info(" Еще рано обрабатывать данную Issue. Она получает статус В ожидании")
      # commentIssue = 'отложено до 16:00 даты увольнения \n' + telephoneNumberDismiss + "\n" + accountImoprtantInfo + "\n" +  nccGrAll_Dismiss + "\n" + numberFMTN + "\n" + department
      commentIssue = 'отложено до 16:00 даты увольнения \n' + telephoneNumberDismiss + "\n" +  nccGrAll_Dismiss + "\n" + numberFMTN + "\n" + department
      executionTime = "9m"    # определяем  потреченного времени
      returnTime = str(dataDismiss) + 'T15:51:33.000+0300'   # определяем дату и время выхода issue из режима ожиданния
      accountImoprtantInfo = "Заявка отправлена В ожидание " + accountImoprtantInfo
      jira.add_worklog(changingIssue, timeSpent=executionTime)  # укаханием потреченного времени (executionTime)
      jira.transition_issue(changingIssue, transition="61", comment=commentIssue, fields={'customfield_19624': {'id': '45405'},'customfield_10400': returnTime})  # меняется статус issue на "В ожидание" - "Дата оформления/увольнения" с укаханием даты/времени окончания ожидания и комментария
      continue




      # обработка issue , которые !!! ОТМЕНА УВОЛЬНЕНИЯ !!!
      #------------------------------------------------------
    if accountImoprtantInfo.find("!!! ОТМЕНА УВОЛЬНЕНИЯ !!!") != -1:
      print "\t\t\t операция Решение по ОТМЕНА УВОЛЬНЕНИЯ активировируктся "
      logger.info(" операция Решение по ОТМЕНА УВОЛЬНЕНИЯ активировируктся ")
      changingIssue_decision_YN = 1  # определяет требуется ли Решение в issue  (ставим 1 = да)
      commentIssue = 'указано ОТМЕНА УВОЛЬНЕНИЯ. Изменения не вносились.'
      executionTime = "9m"
      accountImoprtantInfo = "Заявка закрыта без изменений " + accountImoprtantInfo
      # print " операция по ОТМЕНА УВОЛЬНЕНИЯ активировано "

      # обработка issue , которые !!! ТЕХНИЧЕСКОЕ увольнение !!!
      #------------------------------------------------------
    elif accountImoprtantInfo.find("!!! ТЕХНИЧЕСКОЕ увольнение !!!") != -1:
      print "\t\t\t операция Решение по ТЕХНИЧЕСКОЕ увольнение активируется "
      logger.info(" операция Решение по ТЕХНИЧЕСКОЕ увольнение активируется ")
      changingIssue_decision_YN = 1  # определяет требуется ли Решение в issue  (ставим 1 = да)
      commentIssue = 'указано ТЕХНИЧЕСКОЕ УВОЛЬНЕНИЕ. Изменения не вносились'
      executionTime = "9m"
      accountImoprtantInfo = "Заявка закрыта без изменений " + accountImoprtantInfo
      # print " операция по ТЕХНИЧЕСКОЕ увольнение активировано "

      # обработка issue , которые "Пользователь в системах телефонии не найден"
      # ------------------------------------------------------
    elif accountImoprtantInfo.find("Пользователь в системах телефонии не найден") != -1:
      print "\t\t\t операция 'Решение по Пользователь в системах телефонии не найден' активируется "
      logger.info(" операция 'Решение по Пользователь в системах телефонии не найден' активируется ")
      changingIssue_decision_YN = 1  # определяет требуется ли Решение в issue  (ставим 1 = да)
      commentIssue = 'не найден телефонный номер, закрепленный за указанным пользователем.\nПо телефонии изменений не вносилось.'
      executionTime = "9m"
      accountImoprtantInfo = "Заявка закрыта без изменений " + accountImoprtantInfo
      # print " операция Решение по Пользователь в системах телефонии не найден активировано "

      # обработка issue , которые "From Avaya IPO deleting user with number"
      # ------------------------------------------------------
    if accountImoprtantInfo.find("From Avaya IPO deleting user with number") != -1:
      print "\t\t\t операция 'From Avaya IPO deleting user with number' активируется "
      logger.info(" операция 'From Avaya IPO deleting user with number' активируется ")
      changingIssue_decision_YN = 1  # определяет требуется ли Решение в issue  (ставим 1 = да)
      commentIssue = 'удален User с внутренним номером ' + str(telephoneNumberDismiss) +', закрепленный за указанным пользователем'
      executionTime = "9m"
      # accountImoprtantInfo = "Удален User с внутренним номером " + accountImoprtantInfo
      # print " операция Решение по From Avaya IPO deleting user with numberн активировано "

      # обработка issue , которые "From Avaya IPO deleting extension"
      # ------------------------------------------------------
    if accountImoprtantInfo.find("From Avaya IPO deleting extension") != -1:
      print "\t\t\t операция 'From Avaya IPO deleting extension' активируется "
      logger.info(" операция 'From Avaya IPO deleting extension' активируется ")
      changingIssue_decision_YN = 1  # определяет требуется ли Решение в issue  (ставим 1 = да)
      commentIssue = 'удален внутренний номер ' + str(telephoneNumberDismiss) +', закрепленный за указанным пользователем'
      executionTime = "9m"
      # accountImoprtantInfo = "Удален внутренний номер " + telephoneNumberDismiss + " | " + accountImoprtantInfo
      # print " операция Решение по From Avaya IPO deleting extension активировано "

      # обработка issue , которые "Учетка удалилена в Naumen"
      # ------------------------------------------------------
    if accountImoprtantInfo.find("В системе Наумен удалена учетка") != -1:
      print "\t\t\t операция 'Решение по В системе Наумен удалена учетка' активируется "
      logger.info(" операция 'Решение по В системе Наумен удалена учетка' активируется ")
      changingIssue_decision_YN = 1  # определяет требуется ли Решение в issue  (ставим 1 = да)
      commentIssue = 'данные удалены в Naumen (пользователь)'
      executionTime = "9m"
      if numberFMTN.find("Zoiper") != -1 and numberFMTN.find("FMTN") != -1:
        accountImoprtantInfo = "Не забыть вручную удалить данные по FMTM и Zoiper (номер в проекте и на сайте https://fmc.beeline.ru или https://fmtn.beeline.ru/) ! | " + accountImoprtantInfo
      elif numberFMTN.find("FMTN") != -1:
        accountImoprtantInfo = "Не забыть вручную удалить данные по FMTN (номер в проекте и на сайте https://fmtn.beeline.ru/) ! | " + accountImoprtantInfo
      elif numberFMTN.find("Zoiper") != -1:
        accountImoprtantInfo = "Не забыть вручную удалить данные по Zoiper (номер в проекте и на сайте https://fmc.beeline.ru/) ! | " + accountImoprtantInfo
      # print " операция Решение по Учетка удалилена в Naume активировано "




      # Рещение Issue
    if changingIssue_decision_YN == 1:
      print "\t\t\tРешнеие задачи активируется с commentIssue = ' ", commentIssue, " '"
      logger.info("Решнеие задачи активируется с commentIssue = ' " + commentIssue + " '")
      jira.add_comment(changingIssue, commentIssue)    # оставляется коммент  (т.к. не срабатывает при transition_issue...)
      # jira.transition_issue(changingIssue, transition = "31", comment = commentIssue, fields={'resolution ':{'id': '3'}})
      # jira.transition_issue(changingIssue, transition = "31", fields={'customfield_19626':'46800'})
      # jira.transition_issue(changingIssue, transition = "31", comment = commentIssue, worklog="16m", fields={'customfield_19626':{'id':'46800'}})
      jira.transition_issue(changingIssue, transition = "31", worklog=executionTime, fields={'customfield_19626':{'id':'46800'}})  # меняется статус issue на "Решение" - "Решено" с укаханием потреченного времени (executionTime)
      # jira.transition_issue(changingIssue, transition = "31", comment = commentIssue, fields={'customfield_19626':{'id':'46800'}})
      # jira.add_worklog(changingIssue, timeSpent="16m")
      # results[issueNumber][3] = commentIssue + results[issueNumber][3]
      # print "Решнеие задачи активировано"



















    # jira.close()



      # новая инфо дописывается к имеющимся данным
    results[issueNumber][3] = str(accountImoprtantInfo)



except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!!  change issues Jira - Возникла ошибка типа: ', str(e)
  print '\n\tError by change issues Jira: ', str(sys.exc_info())
  logger.error('\n\n\t\tchange issues Jira - This is error: ' + str(sys.exc_info()))
  sys.exit()

finally:
  jira.close()


print "\nРешение-закрытие issues Jira закончено\n_____________________________________________________________________________________________________________________________________________________\n\n"
logger.info ("\nРешение-закрытие issues Jira закончено\n_____________________________________________________________________________________________________________________________________________________\n\n")


"""
  КОНЕЦ
    Решение-закрытие issues Jira
_____________________________________________________________________________________________________________________________________________________"""







"""
   Вывод итоговых данных
_____________________________________________________________________________________________________________________________________________________"""


print "\nВывод итоговых данных\n_____________________________________________________________________________________________________________________________________________________\n\n"
logger.info ("\nВывод итоговых данных\n_____________________________________________________________________________________________________________________________________________________\n\n")




try:

  for searchInData in results.items():
    issueNumber = searchInData[0]
    dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo, telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department = searchInData[1]

      # вывод на экран собранных данных по этой issue
    printInfoAboutIssue(searchInData, issueNumber, dataDismiss, nameDismiss, accountDismiss, accountImoprtantInfo,
                        telephoneNumberDismiss, nccGrAll_Dismiss, numberFMTN, department)

      # вывод в лог данных по Issue
    logIssueInfo (str(issueNumber), results[str(issueNumber)])


except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!!  EndData - Возникла ошибка типа: ', str(e)
  print '\n\tError by EndData import: ', str(sys.exc_info())
  logger.error('\n\n\t\tEndData import - This is error: ' + str(sys.exc_info()))
  sys.exit()

finally:





 """
  КОНЕЦ
   Вывод итоговых данных
_____________________________________________________________________________________________________________________________________________________"""













print "\n---------------------------------------\n\tРабота программы завершена\n---------------------------------------\n\n\n"
logger.info(
  "\n---------------------------------------\n\tРабота программы завершена\n---------------------------------------\n|\n|\n|\n|\n|\n|\n|\n\n\n\n\n\n\n\n\n\n\n")








