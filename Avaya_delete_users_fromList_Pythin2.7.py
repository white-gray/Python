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


С помощью этого скрипта из IPO удаляются Users и соответствующие Exteisions, прописанные в файле Avaya_delete_users_fromList.lst 

  В данный файл данные пишутся построчно в формате: номер, имя абонента (должно совпадать с Full Name на IPO)
                                             Пример: 6061, Беляков Сергей
    
  Если нет указанного User, или его Extension, или имя (Full Name) User не соответствует прописанному, - об этом сообщается, и задается вопрос удалять ли.
  
  Но если есть прописанный User c указанным Full Name и Extensiom, но у него нет Extension, - данный User удалится без отдельного оповещения.
 

Возможны варианты исполнения:
  1. в разделе "настойки систем -> # IPO Settings " прописываются IPaddress сервера Avaya IPO, и логин, пароль API доступа на него

  2. есть раздел "###  чтение данных из IPO"
              при его активации, данные читаются с API IPO

  3. для использования при тестировании, есть раздел "### ----------> работа с файлами, чтобы не постоянно читать данные с системы IPO, в который входят подразделы 
          "# сохранения данных в файлы" 
            и
          "# чтение данных из файлов"

    3.1 при активации "# сохранения данных в файлы" данные, прочитанные в API IPO сохраняются в файлы
                                                                      Avaya_userData_response.content.data
                                                                      Avaya_extensionsData_response.content.data
               Если такие файлы уже есть, но данные в них ПЕРЕЗАПИСЫВАЮТСЯ

    3.2 при активации "# чтение данных из файлов"  данные, ранее полученные с API IPO м записанные в указанные выше файлы, берутся из них. 



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
log_file = './Avaya_delete_users_fromList.log'
 #logging.basicConfig()
logger = logging.getLogger("Avaya_delete_users_fromList")
logger.setLevel(logging.DEBUG)
 #Set logging level @ params
maxBytes = 300000         # когда размер текущего лог-файла достигнет размера,  следующие записи будут попадать в другие файлы
backupCount = 1  # сколько всего будет сохраняться старых файлов логов (старые будут стираться) (+ рабочий файл)
handler = RotatingFileHandler(log_file, maxBytes = maxBytes, backupCount = backupCount, mode='a', encoding=None, delay=0)
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
headers = {"X-User-Client": "Avaya-WebAdmin",
            "X-User-Agent": "Avaya-SDKUser",
            "Content-Type": "application/json"}

deleteDataFromFile = {}           # данные что удалЯть, полученные из файда
dataFromAvayaUsers = {}           # данные конечной обработка по Users
dataFromAvayaExtensions = {}      # данные конечной обработка по Extensions


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



 # GET запрос на IPO
def sessionGet(APIfunction):
  try:
    link = "https://" + server + ":7070/WebManagement/ws/sdk/admin/v1/" + APIfunction
    return session.get(link, headers=headers, verify=False)

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
    return session.delete(link, headers=headers, verify=False)

  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by IPO DELETE: ' + str(sys.exc_info()))
    sys.exit()

  finally:
    session.close()
    # print "session.verify sessionDelete(APIfunction, guid) = ", session.verify




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


    #------------------------------------------------
    ###  чтение данных из IPO
    #_________________________________________________

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

  textUsersFromAvaya_API = response_usersData.content  # полученные данные по Extensions!!!



    # чтение данных по Extensions из Avaya
  response_extensionsData = sessionGet("extensions")

  logger.info("________ about Extensions received response _______\n\t\t" + str(response_extensionsData))
  # logger.info("________ about Extensions received text _______\n\t\t" + str(response_extensionsData.text))
  # logger.info("________ about Extensions received json _______\n\t\t" + str(response_extensionsData.json()))
  # logger.info("________ about Extensions received response.status_code _______\n\t\t" + str(response_extensionsData.status_code))
  # logger.info("________ about Extensions received response.cookies _______\n\t\t" + str(response_extensionsData.cookies))
  # logger.info("________ about Extensions received response.history _______\n\t\t" + str(response_extensionsData.history))
  # logger.info("________ about Extensions received response.headers _______\n\t\t" + str(response_extensionsData.headers))
  logger.info("________ about Extensions received response.elapsed _______\n\t\t" + str(response_extensionsData.elapsed))
  # logger.info("________ about Extensions received response.content _______\n\t\t" + str(response_extensionsData.content))

  textExtensionsFromAvaya_API = response_extensionsData.content  # олученные данные по Extensions


    # ------------------------------------------------
    ###  КОНЕЦ
    ###    чтение данных из IPO
    # _________________________________________________




        # ------------------------------------------------
        ### ----------> работа с файлами, чтобы не постоянно читать данные с системы IPO
        # ------------------------------------------------

   # сохранения данных в файлы
  file1 = open(r'.\Avaya_userData_response.content.data', 'w')
  print "write  Avaya_userData_response.content.data"
  file2 = open(r'.\Avaya_extensionsData_response.content.data', 'w')
  print "write  Avaya_extensionsData_response.content.data"
  try:
    file1.write(str(response_usersData.content))
    file2.write(str(response_extensionsData.content))
  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by file write: ' + str(sys.exc_info()))
    sys.exit()
  finally:
    file1.close()
    file2.close()
   # ________________________________ конец  сохранения данных в файллы

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
  # # ________________________________ конец  чтение данных и файлов

        # ------------------------------------------------
        ### <---------- КОНЕЦ работа с файлом
        # ------------------------------------------------





        # ------------------------------------------------
        ###    парсинг полученных данных
        # _________________________________________________


      # подготовка к парсингу данных  (из-за того, что в файлах эти значения указаны без кавычек)
  false = "false"
  true = "true"

  dictUsersFromAvaya_API = {}        # определяем dict чтобы не отображались ошибки в тексте проги
  dictExtensionsFromAvaya = {}       # определяем dict чтобы не отображались ошибки в тексте проги



    ###################
    # парсинг по Users
    ###################

      #----------------------------
      # парсинг данных из IPO API
      # ----------------------------
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
    dataFromAvayaUsers.update({extension:[giud, extension, fullName, name]})

     # отправка данных в лог
    logger.info("---\t" + str(dataFromAvayaUsers[extension][0]) + "\t" + str(dataFromAvayaUsers[extension][1]) + "\t" + str(dataFromAvayaUsers[extension][2]) + "\t" + str(dataFromAvayaUsers[extension][3]))

      # ----------------------------
      # КОНЕЦ
      #     парсинг данных из IPO API
      # ----------------------------





      # ----------------------------
      # парсинг по Extensions
      # ----------------------------

    logger.info("--- received textExtensionsFromAvaya_API ___________________________________________\n\t")
  # logger.info("--- received textExtensionsFromAvaya_API ___________________________________________\n\t" + str(textExtensionsFromAvaya_API))
  # print ("--- received textExtensionsFromAvaya_API _____")



  exec ('dictExtensionsFromAvaya = ' + textExtensionsFromAvaya_API)
  logger.info("--- received dictExtensionsFromAvaya ___________________________________________\n\t" + str(dictExtensionsFromAvaya))
  # print ("--- received dictExtensionsFromAvaya _____")

   # захват первого-отдельного описанного в dictExtensionsFromAvaya значения Extansion
  dataFromAvayaExtensions.update({str(dictExtensionsFromAvaya["response"]["data"]["ws_object"]["Extension"][1]):
                                    [str(dictExtensionsFromAvaya["response"]["data"]["ws_object"]["Extension"][0]["@GUID"]),
                                     str(dictExtensionsFromAvaya["response"]["data"]["ws_object"]["Extension"][1])]})

   # парсинг остальных описанных в dictExtensionsFromAvaya значений Extansions
  for dataExtension in dictExtensionsFromAvaya["ws_object"]:
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
      #     парсинг по Extensions
      # ----------------------------


    #################################
    ###  КОНЕЦ
    ###    парсинг полученных данных
    #################################






    #####################################
    ###  оперделение какие номера удалить
    #####################################


      # чтение данных какие номера удалить из файла Avaya_delete_users_fromList.lst   --->
  file = open(r'.\Avaya_delete_users_fromList.lst ', 'r')
  logger.info("\n\n-----------------------read data from file   Avaya_delete_users_fromList.lst ")
  print "read data from file   Avaya_delete_users_fromList.lst "
  try:
    forDelete = file.read()
  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! A type error has occurred: ', str(e)
    print ('\n\tError by file Avaya_delete_users_fromList.lst  load: ' + str(sys.exc_info()))
    sys.exit()
  finally:
    file.close()
      # <--- КОНЕЦ  чтение данных и файла userData_FromAvaya_response.content.data'




       # парсинг полученных данных  --->

        # данные по удаляемым номерам
  textForDelete = forDelete.strip().splitlines()
  logger.info("--- получено textForDelete ___________________________________________\n\t" + str(textForDelete))
  # print ("--- получено textForDelete _____")
  for data in textForDelete:
    # print "\t\tdata = ", data
    # print "\t\tlen(data) = ", len(data)
    # print "\t\tstr(data).strip() = ", len(str(data).strip())
     # пропускаем пустые строки, строки с пробелами, и строки комментария
    if data is None or len(str(data).strip()) == 0 or str(data).strip()[0] == "#":
      print "\t-------------\n\t эта строка не рассматривается\n\t\t", str(data).strip(), "\n\t---------------------"
      continue
    dataStr = data.strip().split(",")
     # пропускаем есои в файле строка прописана неверно
    if len(dataStr) != 2:
      print "\t-------------\n\t в этой строке неверные данные\n\t\t", str(data).strip(), "\n\t---------------------"
      continue
    # print "dataStr[0] = ", dataStr[0], "    type(dataStr[0]) = ", type(dataStr[0])
    # print "dataStr[1] = ", dataStr[1], "    type(dataStr[1]) = ", type(dataStr[1])

    deleteDataFromFile.update({dataStr[0].strip():[dataStr[0].strip(), dataStr[1].strip()]})

    logger.info("---   " + deleteDataFromFile[str(dataStr[0].strip())][0] + "\t" + deleteDataFromFile[str(dataStr[0].strip())][1])
    # print "---   " +  deleteDataFromFile[str(dataStr[0].strip())][0] + "\t" + deleteDataFromFile[str(dataStr[0].strip())][1]

      # сорторивка словаря с issues по значениям issues
    deleteDataFromFile = collections.OrderedDict(sorted(deleteDataFromFile.items()))

      # <--- КОНЕЦ парсинг полученных данных  --->

    #####################################
    ###   КОНЕЦ
    ###     оперделение какие номера удалить
    #####################################




    #####################################
    ###  уделание users и extensions
    #####################################

  logger.info("------------------------------------\n Deleting users and  extensions")
  print "\n------------------------------------\n Deleting users and  extensions"


  for deleteNumber in deleteDataFromFile.keys():
    print "\n\nDeleting number ", deleteNumber
    logger.info( "\n\nDeleting number " + deleteNumber)



    ThereIsNoUserHere = false    # контролирует прописан ли данный User в IPO

    # если прописанного в Avaya_delete_users_fromList.lst  номера пользователя нет в IPO
    if deleteNumber not in dataFromAvayaUsers:
      ThereIsNoUserHere = true
      print "\t The User number ", deleteNumber, " is not specified in the IPO"
      logger.info("\t The User number " + deleteNumber + " is not specified in the IPO")
      if question_answer("\tDelete this extension ? (1 - yes; 0 - no) : ", ("1", "0")) == "0":
        print "\t\t The Extension ", deleteNumber, " was not deleted in the IPO\n"
        logger.info("\t\t The Extension " + deleteNumber + " was not deleted in the IPO\n")
        continue



    ThereIsNoExtensionHere = false    # контролирует прописан ли extension у данного удаляемого User

     # если прописанного в Avaya_delete_users_fromList.lst  номера extension нет в IPO
    if deleteNumber not in dataFromAvayaExtensions:
      ThereIsNoExtensionHere = true
      print "\t The Extension ", deleteNumber, " is not specified in the IPO\n"
      logger.info("\t The Extension " + deleteNumber + " is not specified in the IPO\n")


      # если не найдены ни User ни Extension, - перейти на рассмотрение следующего номера
    if ThereIsNoUserHere == true and ThereIsNoExtensionHere == true: continue


    # print "\tdataFromAvaya[deleteNumber] = ", dataFromAvaya[deleteNumber]
    # print "\tdeleteDataFromFile[deleteNumber] = ", deleteDataFromFile[deleteNumber]
    # print "\tdataFromAvaya[deleteNumber][1] = ", dataFromAvaya[deleteNumber][1]
    # print "\tdeleteDataFromFile[deleteNumber][0] = ", deleteDataFromFile[deleteNumber][0]
    # print "\tdataFromAvaya[deleteNumber][2] = ", dataFromAvaya[deleteNumber][2]
    # print "\tdeleteDataFromFile[deleteNumber][1] = ", deleteDataFromFile[deleteNumber][1]



      # рассматривается только в случае, если данный User есть в IPO
    if ThereIsNoUserHere == false:
        # Если данные в файле и полученные из IPO не совпадают
      if dataFromAvayaUsers[deleteNumber][1] != deleteDataFromFile[deleteNumber][0] or dataFromAvayaUsers[deleteNumber][2] != deleteDataFromFile[deleteNumber][1]:
        print "It is specified to delete an entry with a number ", deleteDataFromFile[deleteNumber][0], ", with a name ", deleteDataFromFile[deleteNumber][1], \
                    " and we have a number ", dataFromAvayaUsers[deleteNumber][1], " with a name ", dataFromAvayaUsers[deleteNumber][2]
        logger.info( "It is specified to delete an entry with a number " + deleteDataFromFile[deleteNumber][0] + ", with a name " + deleteDataFromFile[deleteNumber][1] + \
                    " and we have a number " + dataFromAvayaUsers[deleteNumber][1] + " with a name " + dataFromAvayaUsers[deleteNumber][2])
          # запрашивается удалить ли его
        if question_answer ("Delete this entry ? (1 - yes; 0 - no) : ", ("1", "0")) == "0":
          print "\t The number ", deleteNumber, " was not deleted in the IPO"
          logger.info("\t The number " + deleteNumber + " was not deleted in the IPO")
          continue

        # а если данные совпадают, или удаление подтверждается, то
          #--------------------
          # удаление User
          #--------------------
      # если User есть, то он удаляется
      print "\tDeleting user with number", deleteNumber
      logger.info("\tDeleting user with number " + deleteNumber)
      deleteUser = sessionDelete("users", dataFromAvayaUsers[deleteNumber][0]) # удаление User
      # logger.info("\ttext delete User JSON:\n\t\t\t" + str(deleteUser.text))
      logger.info("\t\tabout delete User JSON:\n\t\t\t" + str(deleteUser.json()))
      # logger.info("\tabout delete User status_code:\n\t\t\t" + str(deleteUser.status_code))
      # logger.info("\tabout delete User content:\n\t\t\t" + str(deleteUser.content))
      # logger.info("\tabout delete User cookies:\n\t\t\t" + str(deleteUser.cookies))
      # logger.info("\tabout delete User history:\n\t\t\t" + str(deleteUser.history))
      # logger.info("\tabout delete User :\n\t\t\t" + str(deleteUser.headers))
      logger.info("\t\tabout delete User   elapsed:\n\t\t\t" + str(deleteUser.elapsed))


          #--------------------
          # удаление Extension
          #--------------------
      # если Extension есть, и не указано его не удалять, - то он удаляется
    if ThereIsNoExtensionHere == false:
      print "\tDeleting extension ", deleteNumber
      logger.info("\tDeleting extension " + deleteNumber)
      deleteExtension = sessionDelete("extensions", dataFromAvayaExtensions[deleteNumber][0])
      # logger.info("\ttext delete Extension JSON:\n\t\t\t" + str(deleteExtension.text))
      logger.info("\t\tabout delete Extension JSON:\n\t\t\t" + str(deleteExtension.json()))
      # logger.info("\tabout delete Extension status_code:\n\t\t\t" + str(deleteExtension.status_code))
      # logger.info("\tabout delete Extension content:\n\t\t\t" + str(deleteExtension.content))
      # logger.info("\tabout delete Extension cookies:\n\t\t\t" + str(deleteExtension.cookies))
      # logger.info("\tabout delete Extension history:\n\t\t\t" + str(deleteExtension.history))
      # logger.info("\tabout delete Extension :\n\t\t\t" + str(deleteExtension.headers))
      logger.info("\t\tabout delete Extension elapsed:\n\t\t\t" + str(deleteExtension.elapsed))

    #####################################
    ###   КОНЕЦ
    ###     уделание номеров и extensions
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
