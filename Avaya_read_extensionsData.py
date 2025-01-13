#  coding: utf-8

import base64
import sys
import requests
import logging


  # определение кодировки
reload(sys)
sys.setdefaultencoding('utf8')
  # _______________________________

"""
  Описание скрипта
  -----------------


С помощью этого скрипта можно получить данные по Exteisions и их GUIDs из иситемы Avaya IP Office

  Возможны варианты исполнения:
    1. в разделе "настойки систем -> # IPO Settings " прописываются IPaddress сервера и логин, пароль API доступа на него
    2. есть раздел "### ----------> чтение данных с API IPO"
                при его активации, данные читаются с API IPO
    3. есть раздел "### ----------> работа с файлом, чтобы не постоянно читать данные с сисьемы IPO" в который входят подразделы 
            "# сохранения данных в файл Avaya_extensionsData_response'"
              и
            "# чтение данных из файла Avaya_extensionsData_response.content.data'
      
      3.1 при активации "# сохранения данных в файл Avaya_extensionsData_response'" данные, прочитанные в API IPO сохраняются в файл.
                 В дальнейшем можно использовать их при праверках, чтобы "не дергать" системы
      3.2 при активации "# чтение данных из файла Avaya_extensionsData_response.content.data'"  данные, ранее полученные с API IPO м записанные в файл, 
                 читаются из этого файла. 
                 Т.е. в данном случае чтение данных API и из запись в файл надо отключить


Работает с любого компа где установлен Python 2.7

_____________________________________________________________________________________________________________________________________________________"""







"""
  здесь собраны все DEFs
_____________________________________________________________________________________________________________________________________________________"""



 # Авторизация на IPO
def aythorisationIPO():
  try:
    # линк для авторизации
    linkAuth ="https://" + server + ":7070/WebManagement/ws/sdk/security/authenticate"

     # процесс авторизации
    global session
    session = requests.session()  # создаём сессию
    session.get(linkAuth, headers=headersAuth, timeout=(1, 3), verify=False)  # получаем cookie c токеном


  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e)
    logger.info('\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e))
    print ('\n\tError by aythorisationIPO(): ' + str(sys.exc_info()))
    logger.info('\n\tError by aythorisationIPO(): ' + str(sys.exc_info()))
    sys.exit()

  finally:
    session.close()


 # GET запрос на IPO
def sessionGet(APIfunction):
  try:
    link = "https://" + server + ":7070/WebManagement/ws/sdk/admin/v1/" + APIfunction
    return session.get(link, headers=headers, verify=False)

  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e)
    logger.info('\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e))
    print ('\n\tError by sessionGet(APIfunction): ' + str(sys.exc_info()))
    logger.info('\n\tError by sessionGet(APIfunction): ' + str(sys.exc_info()))
    sys.exit()

  finally:
    session.close()

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


 # Logging initializing
log_file = './Avaya_read_extensionsData.log'
 #logging.basicConfig()
logger = logging.getLogger("importldap")
 #Set logging level
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(log_file, encoding='utf-8')  # , encoding='utf-8' - это уже я прописал, и стало часто выдавать ошибку в жтом месте
# handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


 # используемые в программе

headersAuth = {"X-User-Client": "Avaya-WebAdmin",
            "X-User-Agent": "Avaya-SDKUser",
            "Content-Type": "application/json",
            "Authorization": "Basic " + authBytesStrEncoded}
headers = {"X-User-Client": "Avaya-WebAdmin",
            "X-User-Agent": "Avaya-SDKUser",
            "Content-Type": "application/json"}


dictExtensionsFromAvaya = {}
dataFromAvayaExtensions = {}


"""
  КОНЕЦ
    настойки систем
_____________________________________________________________________________________________________________________________________________________"""





logger.info("\n\n\n\n\n\n\n\n\n------------------------------------ The program starts \n---------------------------------------")
print "\n---------------------------------------\n\tThe program starts\n---------------------------------------"

try:

  ### ----------> чтение данных с API IPO

    # аутентификация в Avaya IPO
  aythorisationIPO()


   # чтение данных по User из Avaya
  response_extensionsData = sessionGet("extensions")

  logger.info("________ по Extensions получено response _______\n\t\t" + str(response_extensionsData))
  logger.info("________ по Extensions получено text _______\n\t\t" + str(response_extensionsData.text))
  logger.info("________ по Extensions получено json _______\n\t\t" + str(response_extensionsData.json()))
  logger.info("________ по Extensions получено response.status_code _______\n\t\t" + str(response_extensionsData.status_code))
  logger.info("________ по Extensions получено response.cookies _______\n\t\t" + str(response_extensionsData.cookies))
  logger.info("________ по Extensions получено response.history _______\n\t\t" + str(response_extensionsData.history))
  logger.info("________ по Extensions получено response.headers _______\n\t\t" + str(response_extensionsData.headers))
  logger.info("________ по Extensions получено response.elapsed _______\n\t\t" + str(response_extensionsData.elapsed))
  logger.info("________ по Extensions получено response.content _______\n\t\t" + str(response_extensionsData.content))

  textExtensionsFromAvaya = response_extensionsData.content  # активировать при чтении данных с IPO !!!

  ### <---------- КОНЕЦ чтение данных с API IPO



  ### ----------> работа с файлом, чтобы не постоянно читать данные с сисьемы IPO

  #  # сохранения данных в файл Avaya_extensionsData_response'
  # file = open(r'.\Avaya_extensionsData_response.content.data', 'w')
  # print "write  Avaya_extensionsData_response.content.data"
  # try:
  #   file.write(str(response_extensionsData.content))
  # except Exception as e:
  #   print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e)
  #   logger.info('\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e))
  #   print ('\n\tError by file write: ' + str(sys.exc_info()))
  #   logger.info('\n\tError by file write: ' + str(sys.exc_info()))
  #   sys.exit()
  # finally:
  #   file.close()
  #  # ________________________________ конец  сохранения данных в файл Avaya_extensionsData_response.content.data'

  #  # чтение данных из файла Avaya_extensionsData_response.content.data'
  # file = open(r'.\Avaya_extensionsData_response.content.data', 'r')
  # logger.info("\n\n-----------------------read data from file   Avaya_extensionsData_response.content.data")
  # print "read data from files   Avaya_..._response.content.data"
  # try:
  #   response_extensionsData = file.read()
  # except Exception as e:
  #   print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e)
  #   logger.info('\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e))
  #   print ('\n\tError by file write: ' + str(sys.exc_info()))
  #   logger.info('\n\tError by file write: ' + str(sys.exc_info()))
  #   sys.exit()
  # finally:
  #   file.close()
  #
  # textExtensionsFromAvaya = response_extensionsData  # активировать при работе с данными из файла !!!
  #
  #  # ________________________________ конец  чтение данных и файла Avaya_extensionsData_response.content.data'

   ### <---------- КОНЕЦ работа с файлом





  # ------------------------------------------------
  ###    парсинг полученных данных
  # _________________________________________________

    # по данные из IPO API

  exec ('dictExtensionsFromAvaya = ' + textExtensionsFromAvaya)
  logger.info("--- получено dictExtensionsFromAvaya ___________________________________________\n\t" + str(dictExtensionsFromAvaya))
  print ("--- получено dictExtensionsFromAvaya _____")



    # захват первого-отдельного описанного в dictExtensionsFromAvaya значения Extansion
  dataFromAvayaExtensions.update({str(dictExtensionsFromAvaya["response"]["data"]["ws_object"]["Extension"][1]):
                                    [str(dictExtensionsFromAvaya["response"]["data"]["ws_object"]["Extension"][1]),
                                     str(dictExtensionsFromAvaya["response"]["data"]["ws_object"]["Extension"][0]["@GUID"])]})



    # парсинг остальных описанных в dictExtensionsFromAvaya значений Extansions
  for dataExtension in dictExtensionsFromAvaya["ws_object"]:
    # logger.info("--- получено dataExtension from textExtensionsFromAvaya ___________________________________________\n\t"+ str(dataExtension))
    print ("--- получено dataExtension from textExtensionsFromAvaya ___________________________________________")
    extension = str(dataExtension['Extension'][1])
    print "\t\t\textension = " + extension
    guid = str(dataExtension['Extension'][0]['@GUID'])
    print "\t\t\tguid = " + guid




     # сохранение полученных результатов в словаре dataFromAvaya, где за ключ берется extension
    dataFromAvayaExtensions.update({extension:[extension, guid]})

    ###########################
    # вывод полученных данных
    ###########################

    # заголовок таблицы данных
  logger.info("Extension" + "\t" + "GUID")

  for data in dataFromAvayaExtensions.values():
    print data
     # запись данных в логфайл
    logger.info (str((data[0]) + "\t" + data[1]))


    ###########################
    #  КОНЕЦ
    #     вывод полученных данных
    ###########################





except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e)
  logger.info('\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e))
  print '\n\tError by basic Proga: ' + str(sys.exc_info())
  logger.info('\n\tError by basic Proga: ' + str(sys.exc_info()))
  sys.exit()

# finally:

logger.info("\n------------------------------------ The program ends \n---------------------------------------\n\n\n\n\n")
print "\n---------------------------------------\n\tThe program ends\n---------------------------------------"
