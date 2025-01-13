#  coding: utf-8

import base64
import sys
import requests
import logging
import collections



  # определение кодировки
reload(sys)
sys.setdefaultencoding('utf8')
  # _______________________________


"""
  Описание скрипта
  -----------------


С помощью этого скрипта можно получить данные по Users и их GUIDs из сиситемы Avaya IP Office

  Возможны варианты исполнения:
    1. в разделе "настойки систем -> # IPO Settings " прописываются IPaddress сервера Avaya IPO, и логин, пароль API доступа на него
    2. есть раздел "### ----------> чтение данных с API IPO"
                при его активации, данные читаются с API IPO
    3. есть раздел "### ---------->  работа с файлами, чтобы не постоянно читать данные с системы IPO и получить доп.данные" 
            "# сохранения данных в файл 'Avaya_readUsersData_response.content.data'"
              и
            "# чтение данных из файла 'Avaya_readUsersData_response.content.data'

      3.1 при активации "# сохранения данных в файл 'Avaya_readUsersData_response.content.data'" данные, прочитанные в API IPO сохраняются в файл.
                 В дальнейшем можно использовать их при проверках, чтобы "не дергать" системы
      3.2 при активации "# чтение данных из файла 'Avaya_readUsersData_response.content.data'"  данные, ранее полученные с API IPO м записанные в файл, 
                 читаются из этого файла. 
                 Т.е. в данном случае чтение данных API и из запись в файл надо отключить
    4. есть раздел "# чтение данных из файла usersFromWEB.xml для получения дополнительных данных (о forwrad & twinning)"
              Дело в том, что при API bp IPO загружаются не все данные по Users. 
              Дополнительные нужные данные можно получить из .xml файла, полученного при Tools -> Export -> User (данное есть и в IPOmanager, и в WEB IPOmanager)


Работает с любого компа где установлен Python 2.7

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
    print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ', str(e)
    print ('\n\tError by IPO import: ' + str(sys.exc_info()))
    sys.exit()

  finally:
    session.close()


 # GET запрос на IPO
def sessionGet(APIfunction):
  try:
    link = "https://" + server + ":7070/WebManagement/ws/sdk/admin/v1/" + APIfunction
    return session.get(link, headers=headers, verify=False)

  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ', str(e)
    print ('\n\tError by IPO import: ' + str(sys.exc_info()))
    sys.exit()

  finally:
    session.close()


 # берет значение из строки Json формата "имяПеременной : значениеПеременной"
def takeValueJson(searching):
  searching = searching.split(":", 1)
  return searching[1].strip()


 # берет значение из строки XML формата c отрезанным первым знаком "<" - "имяПеременной>значениеПеременной</имяПеременной>"
def takeValueXML(searching):
  startIndex = searching.find(">") + 1
  endIndex = searching.find("</")
  return searching[startIndex:endIndex].strip()



"""
  КОНЕЦ 
    здесь собраны все DEFs
_____________________________________________________________________________________________________________________________________________________"""




"""
  настойки систем
_____________________________________________________________________________________________________________________________________________________"""

 # IPO Settings
server = "IPaddress сервера IPO"
username = "логин аккаунта SDK"
password = "пароль аккаунта SDK"

authStr = username+":"+password
authBytesStrEncoded = str(base64.b64encode(bytes(authStr)))

  #################
  # set loggimg
  #################

 # Logging initializing
log_file = './Avaya_read_usersData_fromAPIandWEB_Pythin2.7.log'
 #logging.basicConfig()
logger = logging.getLogger("importldap")
 #Set logging level
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(log_file, encoding='utf-8')  # , encoding='utf-8' - это уже я прописал, и стало часто выдавать ошибку в жтом месте
# handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
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

dataFromAvaya = {}
dataFromAvayaWEB = {}


"""
  КОНЕЦ
    настойки систем
_____________________________________________________________________________________________________________________________________________________"""





logger.info("\n\n\n\n\n\n\n\n\n------------------------------------ The program starts \n---------------------------------------")
print "\n---------------------------------------\n\tThe program starts\n---------------------------------------"

try:

      # ------------------------------------------------
      ###  чтение данных из IPO API
      # _________________________________________________

  #     # аутентификация в Avaya IPO
  # authorizationIPO()
  #
  #
  #  # чтение данных по User из Avaya
  # response_usersData = sessionGet("users")
  #
  # logger.info("________ получено response_usersData _______\n\t\t" + str(response_usersData))
  # # logger.info("________ получено response_usersData.status_code _______\n\t\t" + str(response_usersData.status_code))
  # # logger.info("________ получено response_usersData.text _______\n\t\t" + str(response_usersData.text))
  # # logger.info("________ получено response_usersData.json _______\n\t\t" + str(response_usersData.json()))
  # # logger.info("________ получено response_usersData.cookies _______\n\t\t" + str(response_usersData.cookies))
  # # logger.info("________ получено response_usersData.history _______\n\t\t" + str(response_usersData.history))
  # # logger.info("________ получено response_usersData.headers _______\n\t\t" + str(response_usersData.headers))
  # # logger.info("________ получено response_usersData.elapsed _______\n\t\t" + str(response_usersData.elapsed))
  # # logger.info("________ получено response_usersData.content _______\n\t\t" + str(response_usersData.content))
  #
  #    # данные из IPO API
  #
  # # textUsersFromAvaya_API = response_usersData.content.rsplit('"User":')  # активировать при чтении данных с IPO и разборе полученного текста!!!
  # textUsersFromAvaya_API = response_usersData.content  # активировать при чтении данных с IPO и разборе полученноого DICT !!!
  # logger.info("--- получено textUsersFromAvaya_API ___________________________________________\n\t" + str(textUsersFromAvaya_API))
  # print ("--- получено textUsersFromAvaya_API _____")

        # ------------------------------------------------
        ###  КОНЕЦ
        ###    чтение данных из IPO API
        # _________________________________________________



        # ------------------------------------------------
        ### ----------> работа с файлами, чтобы не постоянно читать данные с системы IPO и получить доп.данные
        # ------------------------------------------------

  #     # сохранения данных в файл 'Avaya_userData_response.content.data'
  # file = open(r'.\Avaya_userData_response.content.data', 'w')
  # print "file Avaya_userData_response.content.data is writiung"
  # logger.info("file Avaya_userData_response.content.data is writiung")
  # try:
  #   file.write(response_usersData.content)
  #   print "file Avaya_userData_response.content.data wrote"
  #   logger.info("file Avaya_userData_response.content.data wrote")
  # except Exception as e:
  #   print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ', str(e)
  #   print ('\n\tError by file write: ' + str(sys.exc_info()))
  #   sys.exit()
  # finally:
  #   file.close()
  #  # ________________________________ конец  сохранения данных в файл userData_FromAvaya_response.content.data'



    # чтение данных из файла 'Avaya_userData_response.content.data'
  file = open(r'.\Avaya_userData_response.content.data', 'r')
  logger.info("----------------------- data from file   Avaya_userData_response.content.data is reading ____________________")
  print "data from file   Avaya_userData_response.content.data is reading"
  try:
    textUsersFromAvaya_API = file.read()
    logger.info("----------------------- data from file   Avaya_userData_response.content.data had read ____________________")
    print "data from file   Avaya_userData_response.content.data had read"
  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ', str(e)
    print ('\n\tError by open file: ' + str(sys.exc_info()))
    sys.exit()
  finally:
    file.close()

  logger.info("--- получено textUsersFromAvaya_API ___________________________________________\n\t" + str(textUsersFromAvaya_API))
  print ("--- получено textUsersFromAvaya_API _____")


    # ________________________________ конец  чтение данных из файла userData_FromAvaya_response.content.data'



    # чтение данных из файла usersFromWEB.xml для получения дополнительных данных (о forwrad & twinning)
  file = open(r'.\Avaya_usersFromWEB.xml', 'r')
  logger.info("-----------------------read data from file  Avaya_usersFromWEB.xml")
  print "read data from file   Avaya_usersFromWEB.xml"
  try:
    textUsersFromAvaya_WEB = file.read()
  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ', str(e)
    print ('\n\tError by open .xml file : ' + str(sys.exc_info()))
    sys.exit()
  finally:
    file.close()

    # данные из IPO WEB
  logger.info("--- получено textUsersFromAvaya_WEB ___________________________________________\n\t" + str(textUsersFromAvaya_WEB))
  print ("--- получено textUsersFromAvaya_WEB _____")\

    # ________________________________ конец  чтение данных из файла usersFromWEB.xml'

        # ------------------------------------------------
        ### <---------- КОНЕЦ работа с файлом
        # ------------------------------------------------




        # ------------------------------------------------
        ###    парсинг полученных данных
        # _________________________________________________


    # подготовка к парсингу даееых  (из-за того, что в файлах эти значения указаны без кавычек)
  false = "false"
  true = "true"
  dictUsersFromAvaya_API = {}


    # парсинг данных из IPO API
  exec ('dictUsersFromAvaya_API = ' + textUsersFromAvaya_API)
  # dictUsersFromAvaya_API = textUsersFromAvaya_API
  print " type(dictUsersFromAvaya_API) = ", type(dictUsersFromAvaya_API)
  logger.info("--- получено dictUsersFromAvaya_API ___________________________________________\n\t" + str(dictUsersFromAvaya_API))
  print ("--- получено dictUsersFromAvaya_API _____")


      # в логе выводится оглавление и заголовок таблицы данных
  logger.info("\n\n___________________________________________\n Получено из API IPO:\n\t\t\t" + "Extension" + "\t" + "FullName" + "\t" + "Name" + "\t" + "Etag" + "\t" + "Last-Modified")


  for dataUser in dictUsersFromAvaya_API["response"]["data"]["ws_object"]:
    extension = "-zero-"
    fullName = "-zero-"
    name = "-zero-"
    etag = "-zero-"
    last_modified = "-zero-"
    # logger.info("--- получено dataUser textUsersFromAvaya_API\n\t"+ str(dataUser))
    print ("--- получено dataUser textUsersFromAvaya_API ___________")
    extension = str(dataUser['User']['Extension'])
    print "\t\t\textension = " + extension
    fullName = str(dataUser['User']['FullName'])
    print "\t\t\tfullName = " + fullName
    name = str(dataUser['User']['Name'])
    print "\t\t\tname = " + name
    etag = str(dataUser['User']['Etag'])
    print "\t\t\tetag = " + etag
    last_modified = str(dataUser['User']['Last-Modified'])
    print "\t\t\tlast_modified = " + last_modified



      # сохранение полученных результатов в словаре dataFromAvaya, где за ключ берется extension
    # print "получкенные данные ", extension, " ", fullName, " ", name, " ", etag, " ", last_modified, " прописываются в dataFromAvaya"
    dataFromAvaya.update({extension:[extension, fullName, name, etag, last_modified]})
    #   # запись данных а логфайл
    # logger.info("\t\t\t" + extension + "\t" + fullName + "\t" + name + "\t"  + etag + "\t" + last_modified)
    # print "теперь dataFromAvaya = ", dataFromAvaya

        # ------------------------------------------------
        ### КОНЕЦ парсинг данных из IPO API
        # ------------------------------------------------


  # print "dataFromAvaya = ", dataFromAvaya

        # ------------------------------------------------
        ### парсинг данных из IPO WEB
        # ------------------------------------------------

    # for dataUser in textUsersFromAvaya_WEB:
    #   logger.info("--- получено dataUser textFromAvayaWEB  ___________________________________________\n\t"+ str(dataUser))
    #   print ("--- получено dataUser textFromAvayaWEB  ___________")
    #   words_dataUserWEB = dataUser.strip().rsplit("><")
    #   # logger.info("--- получено words_dataUserWEB textFromAvayaWEB   ___________________________________________\n\t"+ str(words_dataUserWEB))
    #   print ("--- получено words_dataUser textFromAvayaWEB ___________")
    #
    #   extensionWEB = "-zero-"
    #   fullNameWEB = "-zero-"
    #   nameWEB = "-zero-"
    #   etagWEB = "-zero-"
    #   last_modifiedWEB = "-zero-"
    #   forwardWEB = "-zero-"
    #   twinningWEB = "-zero-"
    #   ReplayAllRecordingsWEB = "-zero-"
    #   ReplayOtherRecordingsWEB = "-zero-"
    #
    #   for searching in words_dataUserWEB:
    #       # !!!!!!!!!!! позиции ниже обязательно располагать по последовательности !!!!!!!!!!!
    #     # logger.info("--- получено searching ___________________________________________\n\t" + str(searching))
    #     # print ("--- получено searching ____________")
    #      # определение даты изменения (Etag)
    #     if searching.strip().startswith('Etag>'):
    #       etagWEB = takeValueXML(searching)
    #       print "string 49 - Etag ", etagWEB
    #     # определение Extension
    #     if searching.strip().startswith('Extension>'):
    #       extensionWEB = takeValueXML(searching)
    #       print "string 51 - Extension ", extensionWEB
    #      # определение Name
    #     if searching.strip().startswith('ForwardNumber>'):
    #       forwardWEB = takeValueXML(searching)
    #       print "string 64 - forwardWEB ", forwardWEB
    #      # определение FullName
    #     if searching.strip().startswith('FullName>'):
    #       fullNameWEB = takeValueXML(searching)
    #       print "string 69 - FullName ", fullNameWEB
    #      # определение даты изменения (Last-Modified)
    #     if searching.strip().startswith('Last-Modified>'):
    #       last_modifiedWEB = takeValueXML(searching)
    #       print "string 86 - Last-Modified ", last_modifiedWEB
    #      # определение Name
    #     if searching.strip().startswith('Name>'):
    #       nameWEB = takeValueXML(searching)
    #       print "string 104 - Name ", nameWEB
    #      # определение Name
    #     if searching.strip().startswith('TwinnedMobileNumber>'):
    #       twinningWEB = takeValueXML(searching)
    #       print "string 173 - twinningWEB ", twinningWEB
    #      # определение Name
    #     if searching.strip().startswith('ReplayAllRecordings>'):
    #       ReplayAllRecordingsWEB = takeValueXML(searching)
    #       print "string 327 - ReplayAllRecordingsWEB ", ReplayAllRecordingsWEB
    #      # определение Name
    #     if searching.strip().startswith('ReplayOtherRecordings>'):
    #       ReplayOtherRecordingsWEB = takeValueXML(searching)
    #       print "string 331 - ReplayOtherRecordingsWEB ", ReplayOtherRecordingsWEB
    #
    #
    #    # сохранение полученных результатов в словаре dataFromAvaya, где за ключ берется extension
    #   dataFromAvayaWEB.update({extensionWEB:[extensionWEB, fullNameWEB, nameWEB, etagWEB, last_modifiedWEB, forwardWEB, twinningWEB, ReplayAllRecordingsWEB, ReplayOtherRecordingsWEB]})
    #
    #
    #
    #    # запись данных в логфайл
    #   logger.info (dataFromAvayaWEB[extensionWEB][0] + "\t" + dataFromAvayaWEB[extensionWEB][1] + "\t" + dataFromAvayaWEB[extensionWEB][2] + "\t" + dataFromAvayaWEB[extensionWEB][3] + "\t" + dataFromAvayaWEB[extensionWEB][4] + "\t" + dataFromAvayaWEB[extensionWEB][5] + "\t" + dataFromAvayaWEB[extensionWEB][6] + "\t" + dataFromAvayaWEB[extensionWEB][7] + "\t" + dataFromAvayaWEB[extensionWEB][8])

        # ------------------------------------------------
        ### КОНЕЦ парсинг данных из IPO WEB
        # ------------------------------------------------




        # ------------------------------------------------
        # вывод данны из API IPO
        # ------------------------------------------------

  logger.info("\n\n___________________________________________\n Данные из API IPO")

      # сорторивка словаря с issues по значениям issues
  dataFromAvaya = collections.OrderedDict(sorted(dataFromAvaya.items()))

    # заголовок таблицы данных
  logger.info("\t\t\t" + "Extension" + "\t" + "FullName" + "\t" + "Name" + "\t" + "Etag" + "\t" + "Last-Modified")
  for ext in dataFromAvaya.keys():
    # print ext
    logger.info("\t\t\t" + dataFromAvaya[ext][0] + "\t" + dataFromAvaya[ext][1] + "\t" + dataFromAvaya[ext][2] +
                  "\t" + dataFromAvaya[ext][3] + "\t" + dataFromAvaya[ext][4])
    # logger.info(ext + "\n\t\t from API \n\t\t\t" + dataFromAvaya[ext][0] + "\t" + dataFromAvaya[ext][1] + "\t" + dataFromAvaya[ext][2] +
    #               "\t" + dataFromAvaya[ext][3] + "\t" + dataFromAvaya[ext][4])
    # print "log API OK"

        # ------------------------------------------------
        ### КОНЕЦ вывод данны из API IPO
        # ------------------------------------------------




        # ------------------------------------------------
        ###       # вывод данны из WEB IPO
        # ------------------------------------------------

  # logger.info("\n\n___________________________________________\n Данные из API WEB")
  #   # заголовок таблицы данных
  # logger.info("Extension" + "\t" + "FullName" + "\t" + "Name" + "\t" + "Etag" + "\t" + "Last-Modified" + "\t" + "forward" + "\t" + "twinning" + "\t" + "ReplayAllRecordings" + "\t" + "ReplayOtherRecordings")
  # for ext in dataFromAvayaWEB.keys():
  #   print ext
  #   logger.info(ext + "\n\t\t from WEB \n\t\t\t" "\t" + dataFromAvayaWEB[ext][0] + "\t" + dataFromAvayaWEB[ext][
  #                 1] + "\t" + dataFromAvayaWEB[ext][2] + "\t" + dataFromAvayaWEB[ext][3] + "\t" +
  #               dataFromAvayaWEB[ext][4] + "\t" + dataFromAvayaWEB[ext][5] + "\t" + dataFromAvayaWEB[ext][6])
  #   print "log WEB OK"

        # ------------------------------------------------
        ### КОНЕЦ вывод данны из WEB IPO
        # ------------------------------------------------



        # ------------------------------------------------
        ### проверка что данные API и WEB совпадают
        # ------------------------------------------------


  # logger.info("\n\n___________________________________________\n Сравненеие данных")
  # for ext in dataFromAvaya.keys():
  #   print ext
  #   logger.info(ext + "\n\t\t from API \n\t\t\t" + dataFromAvaya[ext][0] + "\t" + dataFromAvaya[ext][1] + "\t" + dataFromAvaya[ext][2] + "\t" + dataFromAvaya[ext][3] + "\t" + dataFromAvaya[ext][4] + "\n\t\t from WEB \n\t\t\t" "\t" + dataFromAvayaWEB[ext][0] + "\t" + dataFromAvayaWEB[ext][1] + "\t" + dataFromAvayaWEB[ext][2] + "\t" + dataFromAvayaWEB[ext][3] + "\t" + dataFromAvayaWEB[ext][4] + "\t" + dataFromAvayaWEB[ext][5] + "\t" + dataFromAvayaWEB[ext][6])
  #   print "log OK"
  #   if dataFromAvaya[ext][0] != dataFromAvayaWEB[ext][0]: logger.info("ExtensionAPI !- ExtensionWEB")
  #   if dataFromAvaya[ext][1] != dataFromAvayaWEB[ext][1]: logger.info("fullNameAPI !- fullNameWEB")
  #   if dataFromAvaya[ext][2] != dataFromAvayaWEB[ext][2]: logger.info("nameAPI !- nameWEB")
  #   if dataFromAvaya[ext][3] != dataFromAvayaWEB[ext][3]: logger.info("etagAPI !- etagWEB")
  #   if dataFromAvaya[ext][4] != dataFromAvayaWEB[ext][4]: logger.info("last_modifiedAPI !- last_modifiedWEB")

        # ------------------------------------------------
        ### КОНЕЦ проверка что данные API и WEB совпадают
        # ------------------------------------------------



except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ', str(e)
  logger.info('\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e))
  print '\n\tError by IPO import: ', str(sys.exc_info())
  logger.info('\n\tError by IPO import: ' + str(sys.exc_info()))
  sys.exit()

# finally:
#   # print "session.verify 3.1 = ", sesison.verify
#   session.close()
#   print "session.verify 3.2 = ", session.verify

logger.info("\n------------------------------------ The program ends \n---------------------------------------\n\n\n\n\n")
print "\n---------------------------------------\n\tThe program ends\n---------------------------------------"
