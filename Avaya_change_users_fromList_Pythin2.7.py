#  coding: utf-8

import base64
import sys
import requests
import logging
from logging.handlers import RotatingFileHandler
import collections


  # определение кодировки
reload(sys)
sys.setdefaultencoding('utf8')
  # _______________________________


"""
  Описание скрипта
  -----------------

      С помощью этого скрипта на IPO меняе(ю)тся параметр(ы) на позиции Users сразу у нескольких учеток
        Притом, у каждой учетки могут быть отдельные изменения (т.е. отдельно для каждой учетки прописывается что  в ней изменить)
          У каких именно учеток, и какие именно параметры поменять,  указывается в файле Avaya_change_users_fromList.lst 

                В файл Avaya_change_users_fromList.lst данные пишутся ПОСТРОЧНО со знаков "запятая" в качестве разделителя параметров в формате: 
                
                          номер, имя учетки (Name), имя абонента (Full Name), <имяПараметраКоторыйМеняется1>новоеЗначение</имяПараметраКоторыйМеняется1>[<имяПараметраКоторыйМеняется2>новоеЗначение</имяПараметраКоторыйМеняется2><имяПараметраКоторыйМеняется3>новоеЗначение</имяПараметраКоторыйМеняется3>]
					                
					                    (в [ ] указано, что можно прописать не один параметр, а несволько друг за другом. При этом сами [ ] не нужны)
						                  Запятые должны разделять параметры, и не встречеться в их составе
						                  
         		      Пример: 
                        6061, s_belyakov, Беляков Сергей, <FullName>ethel E129</FullName>
                      или
                        6061, s_belyakov, Беляков Сергей, <FullName>ethel E129</FullName><Name>sERG</Name>



Работает с любого компа где установлен Python 2.7


_____________________________________________________________________________________________________________________________________________________"""





"""
  настойки систем
_____________________________________________________________________________________________________________________________________________________"""

 # IPO Settings
server = IPaddress сервера IPO (в кавычках)
username = имя пользователя IPO (в кавычках)
password = пароль IPO (в кавычках)  
authStr = username+":"+password
authBytesStrEncoded = str(base64.b64encode(bytes(authStr)))



#################
# set loggimg
#################

  # Logging initializing
log_file = './Avaya_change_users_fromList_Pythin2.7.log'
  #logging.basicConfig()
logger = logging.getLogger("Avaya_change_users_fromList_Pythin2.7")
logger.setLevel(logging.DEBUG)
  # Set logging level @ params
maxBytes = 300000  # когда размер текущего лог-файла достигнет размера,  следующие записи будут попадать в другие файлы
backupCount = 1  # сколько всего будет сохраняться старых файлов логов (старые будут стираться) (+ рабочий файл)
handler = RotatingFileHandler(log_file, maxBytes=maxBytes, backupCount=backupCount, mode='a', encoding=None, delay=0)
# handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s line %(lineno)d:   %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)



##########################
# используемые в программе
##########################

headersAuth = {"X-User-Client": "Avaya-WebAdmin",
            "X-User-Agent": "Avaya-SDKUser",
            "Content-Type": "application/json",
            "Authorization": "Basic " + authBytesStrEncoded}
headersJson = {"X-User-Client": "Avaya-WebAdmin",
            "X-User-Agent": "Avaya-SDKUser",
            "Content-Type": "application/json"}
headersXML = {"X-User-Client": "Avaya-WebAdmin",
            "X-User-Agent": "Avaya-SDKUser",
            "Content-Type": "application/xml"}

changeDataFromFile = {}           # данные где и что менять, полученные из файда
dataFromAvayaUsers = {}           # данные конечной обработка по Users


"""
  КОНЕЦ
    настойки систем
_____________________________________________________________________________________________________________________________________________________"""







"""
  здесь собраны все DEFs
_____________________________________________________________________________________________________________________________________________________"""


 # Авторизация на IPO
def authorizationIPO():
  try:
    # линк для авторизации
    linkAuth ="https://" + server + ":7070/WebManagement/ws/sdk/security/authenticate"

     # процесс авторизации
    global session
    session = requests.session()  # создаём сессию
    session.get(linkAuth, headers=headersAuth, timeout=(1, 3), verify=False)  # получаем cookie c токеном


  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by def authorizationIPO(): ' + str(sys.exc_info()))
    sys.exit()

  finally:
    session.close()
    # print "session.verify sessionGet(APIfunction) = ", session.verify


 # GET запрос на IPO
def sessionGet(APIfunction):
  try:
    link = "https://" + server + ":7070/WebManagement/ws/sdk/admin/v1/" + APIfunction
    return session.get(link, headers=headersJson, verify=False)

  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by IPO GET: ' + str(sys.exc_info()))
    sys.exit()

  finally:
    session.close()
    # print "session.verify sessionGet(APIfunction) = ", session.verify


 # PUT запрос на IPO
def sessionPut(APIfunction, dataChange):
  print "\t\tPut DATA ", dataChange
  logger.info("\tPut DATA " + dataChange)
  try:
    link = "https://" + server + ":7070/WebManagement/ws/sdk/admin/v1/" + APIfunction
    return session.put(link, data = dataChange, headers=headersXML, verify=False)

  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by IPO PUT: ' + str(sys.exc_info()))
    sys.exit()

  finally:
    session.close()
    # print "session.verify sessionPut(APIfunction, guid) = ", session.verify




 # конструкцию вопрос-ответ
  # (присылается вопрос, и список ответов.
  # Если ответ из списка, он возвращается.
  # Если данного ответа в списке нет, - вопрос повторяется)
def question_answer (question, answers):
  answer =  raw_input(question)
  while str(answer) not in answers:
    print "ожидаемые варианты ответе указаны !"
    answer = raw_input(question)
  return str(answer)


"""
  КОНЕЦ 
    здесь собраны все DEFs
_____________________________________________________________________________________________________________________________________________________"""





logger.info("\n\n\n\n\n\n\n\n\n------------------------------------ The program starts \n---------------------------------------")
print "\n---------------------------------------\n\tThe program starts\n---------------------------------------"

try:


    #################################################
    ###  чтение данных из IPO
    #           (для определение GUID)
    #################################################

    # аутентификация в Avaya IPO
  authorizationIPO()


   # чтение данных по User из Avaya
  response_usersData = sessionGet("users")

  logger.info("________ по Users получено response _______\n\t\t" + str(response_usersData))
  # logger.info("________ по Users получено text _______\n\t\t" + str(response_usersData.text))
  # logger.info("________ по Users получено json _______\n\t\t" + str(response_usersData.json()))
  # logger.info("________ по Users получено response.status_code _______\n\t\t" + str(response_usersData.status_code))
  # logger.info("________ по Users получено response.cookies _______\n\t\t" + str(response_usersData.content))
  # logger.info("________ по Users получено response.history _______\n\t\t" + str(response_usersData.history))
  # logger.info("________ по Users получено response.headers _______\n\t\t" + str(response_usersData.headers))
  logger.info("________ по Users получено response.elapsed _______\n\t\t" + str(response_usersData.elapsed))
  # logger.info("________ по Users получено response.content _______\n\t\t" + str(response_usersData.content))

  textUsersFromAvaya_API = response_usersData.content  # полученные данные по Users


    #################################################
    ###  КОНЕЦ
    ###    чтение данных из IPO
    #################################################





    #################################################
    ###    парсинг полученных данных
    #################################################



    # подготовка к парсингу данных  (из-за того, что в файлах эти значения указаны без кавычек)
  false = "false"
  true = "true"

  dictUsersFromAvaya_API = {}        # определяем dict чтобы не отображались ошибки в тексте проги



    #----------------------------
    # парсинг из IPO API по Users
    #----------------------------


  exec ('dictUsersFromAvaya_API = ' + textUsersFromAvaya_API)
  # print " type(dictUsersFromAvaya_API) = ", type(dictUsersFromAvaya_API)
  logger.info("--- получено dictUsersFromAvaya_API ___________________________________________\n\t")
  print ("--- получено dictUsersFromAvaya_API _____")



    # в логе выводится оглавление и заголовок таблицы данных
  logger.info("\n\n___________________________________________\n\t\t\t\t\t\t\t\t\tПолучено из API IPO:\n\t\t\t\t\t\t\t\t\t\t\t\t" + "GUID" + "\t" + "Extension" + "\t" + "FullName" + "\t" + "Name")



  for dataUser in dictUsersFromAvaya_API["response"]["data"]["ws_object"]:
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
    dataFromAvayaUsers.update({extension:[giud, extension, name, fullName]})

     # отправка данных в лог
    logger.info("---\t" + str(dataFromAvayaUsers[extension][0]) + "\t" + str(dataFromAvayaUsers[extension][1]) + "\t" + str(dataFromAvayaUsers[extension][2]) + "\t" + str(dataFromAvayaUsers[extension][3]))

      # --------------------------------
      # КОНЕЦ
      #     парсинг из IPO API по Users
      # --------------------------------




    #################################
    ###  КОНЕЦ
    ###    парсинг полученных данных
    #################################






    ##########################################################
    ###  оперделение в каких номерах и какие мзменения делать
    ##########################################################


      # чтение данных какие номера удалить из файла Avaya_change_users_fromList.lst   --->
  file = open(r'.\Avaya_change_users_fromList.lst ', 'r')
  logger.info("\n\n-----------------------read data from file   Avaya_change_users_fromList.lst ")
  print "read data from file   Avaya_change_users_fromList.lst "
  try:
    forChange = file.read()
  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by file Avaya_change_users_fromList.lst  load: ' + str(sys.exc_info()))
    sys.exit()
  finally:
    file.close()
      # <--- КОНЕЦ  чтение данных и файла userData_FromAvaya_response.content.data'




       # парсинг полученных данных  --->

  textForCahnge = forChange.strip().splitlines()
  logger.info("--- получено textForCahnge ___________________________________________\n\t" + str(textForCahnge))
  print ("--- получено textForCahnge _____")
  for data in textForCahnge:
     # пропускаем пустые строки, строки с пробелами, и строки комментария
    if data is None or len(str(data).strip()) == 0 or str(data).strip()[0] == "#":
      print "\t-------------\n\t this line is not considered\n\t\t", str(data).strip(), "\n\t---------------------"
      continue
    dataStr = data.strip().split(",")
     # пропускаем есои в файле строка прописана неверно
    if len(dataStr) != 4:
      print "\t-------------\n\t there is incorrect data in this line\n\t\t", str(data).strip(), "\n\t---------------------"
      continue
    # print "dataStr[0] = ", dataStr[0], "    type(dataStr[0]) = ", type(dataStr[0])
    # print "dataStr[1] = ", dataStr[1], "    type(dataStr[1]) = ", type(dataStr[1])

    changeDataFromFile.update({dataStr[0].strip():[dataStr[0].strip(), dataStr[1].strip(), dataStr[2].strip(), dataStr[3].strip()]})

    logger.info("---   " + changeDataFromFile[str(dataStr[0].strip())][0] + "\t" + changeDataFromFile[str(dataStr[0].strip())][1] + "\t" + changeDataFromFile[str(dataStr[0].strip())][2] + "\t" + changeDataFromFile[str(dataStr[0].strip())][3])
    # print "---   " +  changeDataFromFile[str(dataStr[0].strip())][0] + "\t" + changeDataFromFile[str(dataStr[0].strip())][1] + "\t" + changeDataFromFile[str(dataStr[0].strip())][2] + "\t" + changeDataFromFile[str(dataStr[0].strip())][3]

      # сорторивка словаря с issues по значениям issues
    changeDataFromFile = collections.OrderedDict(sorted(changeDataFromFile.items()))

      # <--- КОНЕЦ парсинг полученных данных  --->

    #############################################################
    ###   КОНЕЦ
    ###     оперделение в каких номерах и какие мзменения делать
    #############################################################




    #####################################
    ###  внесение изменений в Users
    #####################################

  logger.info("\n\n------------------------------------\n Changing users")
  print "\n\n------------------------------------\n Changing users"


  for changeNumber in changeDataFromFile.keys():
    print "\n\nChanging number ", changeNumber
    logger.info( "\n\nChanging number " + changeNumber)



      # если прописанного в Avaya_change_users_fromList.lst  номера пользователя нет в IPO
      #   то далее эта запись не рассматривается
    if changeNumber not in dataFromAvayaUsers:
      # ThereIsNoUserHere = true
      print "\t The User number ", changeNumber, " is not specified in the IPO"
      logger.info("\t The User number " + changeNumber + " is not specified in the IPO")
      continue




      # Если данные по имени изменяемого номера, полученные из файла и полученные из IPO не совпадают
      #   задается вопрос вносить ли указанные изменениия в денный номер
    if dataFromAvayaUsers[changeNumber][1] != changeDataFromFile[changeNumber][0] or dataFromAvayaUsers[changeNumber][2] != changeDataFromFile[changeNumber][1] or dataFromAvayaUsers[changeNumber][3] != changeDataFromFile[changeNumber][2]:
      print "It is specified to change an entry with a number ", changeDataFromFile[changeNumber][0], ", with a Name ", changeDataFromFile[changeNumber][1], ", with a FullName ", changeDataFromFile[changeNumber][2], \
                  " and we have a number ", dataFromAvayaUsers[changeNumber][1], " with a Name ", dataFromAvayaUsers[changeNumber][2], " with a FullName ", dataFromAvayaUsers[changeNumber][3]
      logger.info( "It is specified to change an entry with a number " + changeDataFromFile[changeNumber][0] + ", with a Name " + changeDataFromFile[changeNumber][1] +  ", with a FullName " + changeDataFromFile[changeNumber][2] + \
                  " and we have a number " + dataFromAvayaUsers[changeNumber][1] + " with a Name " + dataFromAvayaUsers[changeNumber][2] + " with a FullName " + dataFromAvayaUsers[changeNumber][3])
        # запрашивается удалить ли его
      if question_answer ("Change this entry ? (1 - yes; 0 - no) : ", ("1", "0")) == "0":
        print "\t The number ", changeNumber, " was not chabged in the IPO"
        logger.info("\t The number " + changeNumber + " was not chabged in the IPO")
        continue

        # а если данные совпадают, или удаление подтверждается, то
          # изменение параметров User ---->
    print "\tChange user with number", changeNumber
    logger.info("\tChange user with number " + changeNumber)
    print "changeDataFromFile[changeNumber][2] =", changeDataFromFile[changeNumber][2]
    changeData = "<?xml version='1.0' encoding='UTF-8'?><data><ws_object><User GUID='" + dataFromAvayaUsers[changeNumber][0] + "'>" + changeDataFromFile[changeNumber][3] + "</User></ws_object></data>"
    changeUser = sessionPut("users", changeData) # внесение изменений в User

    logger.info("\ttext chabge User TEXT:\n\t\t\t" + str(changeUser.text))
    # logger.info("\t\tabout change User JSON:\n\t\t\t" + str(changeUser.json()))
    logger.info("\tabout chabge User status_code:\n\t\t\t" + str(changeUser.status_code))
    logger.info("\tabout chabge User content:\n\t\t\t" + str(changeUser.content))
    # logger.info("\tabout chabge User cookies:\n\t\t\t" + str(changeUser.cookies))
    # logger.info("\tabout chabge User history:\n\t\t\t" + str(changeUser.history))
    # logger.info("\tabout chabge User :\n\t\t\t" + str(changeUser.headers))
    logger.info("\t\tabout chabge User   elapsed:\n\t\t\t" + str(changeUser.elapsed))
          # <----  КОНЕЦ изменение параметров User

    #####################################
    ###   КОНЕЦ
    ###     внесение изменений в Users
    #####################################







except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
  logger.info('\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ' + str(e))
  print '\n\tError by basic Proga: ', str(sys.exc_info())
  logger.info('\n\tError by basic Proga: ' + str(sys.exc_info()))
  sys.exit()

finally:
  session.close()
  # print "session.verify 3.2 = ", session.verify

logger.info("\n------------------------------------ The program ends \n---------------------------------------\n\n\n\n\n")
print "\n---------------------------------------\n\tThe program ends\n---------------------------------------"
