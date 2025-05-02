#  coding: utf-8

import base64
import sys
import requests
import logging
from logging.handlers import RotatingFileHandler
import collections
import xml.etree.ElementTree as ET



  # определение кодировки
reload(sys)
sys.setdefaultencoding('utf8')
  # _______________________________




"""
  Не сделано:
  -----------------
  
    в описании п.4
    
    
"""



"""
  Описание скрипта
  -----------------


С помощью этого скрипта можно получить данные по Users и их GUIDs из системы Avaya IP Office

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
    4. есть раздел "# чтение данных из файла Avaya_usersFromWEB.xml для получения дополнительных данных (о forward & twinning например)"
              Дело в том, что при API из IPO загружаются не все данные по Users. 
              Дополнительные нужные данные можно получить из .xml файла, полученного из WebManagement при выборе Call Management -> Users, 
                                                                и там Tools -> Export -> User (данное есть и в IPOmanager, и в WEB IPOmanager)

                  Данный файл надо переименовать в Avaya_usersFromWEB.xml, и поместить в папку с данным скриптом
          
          И в разделе  "### парсинг данных из файла с IPO WEB" указывается какие данные читаются
          
          В разделе "### вывод данны из файла с WEB IPO"   данные выводятся на экран и в логфайл
          
          Также есть раздел  "### проверка что данные API и файла с WEB совпадают" где проверяется соответствие данных, прочитанных на IPO API и IPO WEB
          


Работает с любого компа где установлен Python 2.7

_____________________________________________________________________________________________________________________________________________________"""








"""
  настойки систем
_____________________________________________________________________________________________________________________________________________________"""

  #################
  # IPO Settings
  #################

server = IPaddress сервера IPO (в кавычках)
username = имя пользователя IPO (в кавычках)
password = пароль IPO (в кавычках) 
authStr = username+":"+password
authBytesStrEncoded = str(base64.b64encode(bytes(authStr)))

  #################
  # set loggimg
  #################

 # Logging initializing
log_file = './Avaya_read_usersData_fromAPIandWEB_Pythin2.7.log'
 #logging.basicConfig()
logger = logging.getLogger("Avaya_read_usersData_fromAPIandWEB_Pythin2.7")
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
headers = {"X-User-Client": "Avaya-WebAdmin",
            "X-User-Agent": "Avaya-SDKUser",
            "Content-Type": "application/json"}

dataFromAvaya = {}
dataFromAvayaWEB = {}


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







logger.info("\n\n\n\n\n\n\n\n\n------------------------------------ The program starts \n---------------------------------------")
print "\n---------------------------------------\n\tThe program starts\n---------------------------------------"

try:

        #############################
        ### КОНЕЦ работа с файлом
        #############################

      # ------------------------------------------------
      ###  чтение данных из IPO API
      # _________________________________________________

      # аутентификация в Avaya IPO
  authorizationIPO()


   # чтение данных по User из Avaya
  response_usersData = sessionGet("users")

  logger.info("________ получено response_usersData _______\n\t\t" + str(response_usersData))
  # logger.info("________ получено response_usersData.status_code _______\n\t\t" + str(response_usersData.status_code))
  # logger.info("________ получено response_usersData.text _______\n\t\t" + str(response_usersData.text))
  # logger.info("________ получено response_usersData.json _______\n\t\t" + str(response_usersData.json()))
  # logger.info("________ получено response_usersData.cookies _______\n\t\t" + str(response_usersData.cookies))
  # logger.info("________ получено response_usersData.history _______\n\t\t" + str(response_usersData.history))
  # logger.info("________ получено response_usersData.headers _______\n\t\t" + str(response_usersData.headers))
  # logger.info("________ получено response_usersData.elapsed _______\n\t\t" + str(response_usersData.elapsed))
  # logger.info("________ получено response_usersData.content _______\n\t\t" + str(response_usersData.content))

     # данные из IPO API

  # textUsersFromAvaya_API = response_usersData.content.rsplit('"User":')  # активировать при чтении данных с IPO и разборе полученного текста!!!
  textUsersFromAvaya_API = response_usersData.content  # активировать при чтении данных с IPO и разборе полученноого DICT !!!
  logger.info("--- получено textUsersFromAvaya_API ___________________________________________\n\t" + str(textUsersFromAvaya_API))
  print ("--- получено textUsersFromAvaya_API _____")

        # ------------------------------------------------
        ###  КОНЕЦ
        ###    чтение данных из IPO API
        # _________________________________________________



        # ------------------------------------------------
        ### ----------> работа с файлами, чтобы не постоянно читать данные с системы IPO и получить доп.данные
        # ------------------------------------------------

      # сохранения данных в файл 'Avaya_readUsersData_response.content.data'
  file = open(r'.\Avaya_readUsersData_response.content.data', 'w')
  print "file Avaya_readUsersData_response.content.data is writing"
  logger.info("file Avaya_readUsersData_response.content.data is writing")
  try:
    file.write(response_usersData.content)
    print "file Avaya_readUsersData_response.content.data wrote"
    logger.info("file Avaya_readUsersData_response.content.data wrote")
  except Exception as e:
    print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ', str(e)
    print ('\n\tError by file write: ' + str(sys.exc_info()))
    sys.exit()
  finally:
    file.close()
   # ________________________________ конец  сохранения данных в файл userData_FromAvaya_response.content.data'



  #   # чтение данных из файла 'Avaya_readUsersData_response.content.data'
  # file = open(r'.\Avaya_readUsersData_response.content.data', 'r')
  # logger.info("----------------------- data from file   Avaya_readUsersData_response.content.data is reading ____________________")
  # print "data from file   Avaya_readUsersData_response.content.data is reading"
  # try:
  #   textUsersFromAvaya_API = file.read()
  #   logger.info("----------------------- data from file   Avaya_readUsersData_response.content.data had read ____________________")
  #   print "data from file   Avaya_readUsersData_response.content.data had read"
  # except Exception as e:
  #   print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ', str(e)
  #   print ('\n\tError by open file: ' + str(sys.exc_info()))
  #   sys.exit()
  # finally:
  #   file.close()

    # данные из IPO API, сохоаненные в файле
  logger.info("--- получено textUsersFromAvaya_API ___________________________________________\n\t" + str(textUsersFromAvaya_API))
  print ("--- получено textUsersFromAvaya_API _____")


    # ________________________________ конец  чтение данных из файла userData_FromAvaya_response.content.data'



    # чтение данных из файла Avaya_usersFromWEB.xml для получения дополнительных данных (о forward & twinning)

  treeXML_fromWEBfile = ET.parse('Avaya_usersFromWEB.xml').getroot()

    # ________________________________ конец  чтение данных из файла Avaya_usersFromWEB.xml'



        ######################################
        ### <---------- КОНЕЦ работа с файлом
        ######################################




        # ------------------------------------------------
        ###    парсинг полученных данных
        # _________________________________________________


    # подготовка к парсингу даееых  (из-за того, что в файлах эти значения указаны без кавычек)
  false = "false"
  true = "true"
  dictUsersFromAvaya_API = {}



      # ------------------------------------------------
      # парсинг данных из IPO API
      # ------------------------------------------------

  # print " type(dictUsersFromAvaya_API) = ", type(dictUsersFromAvaya_API)
  exec ('dictUsersFromAvaya_API = ' + textUsersFromAvaya_API)
  # dictUsersFromAvaya_API = textUsersFromAvaya_API
  # print " type(dictUsersFromAvaya_API) = ", type(dictUsersFromAvaya_API)
  logger.info("--- получено dictUsersFromAvaya_API ___________________________________________\n\t" + str(dictUsersFromAvaya_API))
  print ("--- получено dictUsersFromAvaya_API _____")


      # в логе выводится оглавление и заголовок таблицы данных
  logger.info("\n\n___________________________________________\n Получено из API IPO:\n\t\t\t" + "Extension" + "\t" + "FullName" + "\t" + "Name" + "\t" + "Etag" + "\t" + "Last-Modified")


  for dataUser in dictUsersFromAvaya_API["response"]["data"]["ws_object"]:
    # logger.info("--- получено dataUser textUsersFromAvaya_API\n\t"+ str(dataUser))
    # print ("--- получено dataUser textUsersFromAvaya_API ___________")
    extension = str(dataUser['User']['Extension'])
    # print "\t\t\textension = " + extension
    fullName = str(dataUser['User']['FullName'])
    # print "\t\t\tfullName = " + fullName
    name = str(dataUser['User']['Name'])
    # print "\t\t\tname = " + name
    etag = str(dataUser['User']['Etag'])
    # print "\t\t\tetag = " + etag
    last_modified = str(dataUser['User']['Last-Modified'])
    # print "\t\t\tlast_modified = " + last_modified



      # сохранение полученных результатов в словаре dataFromAvaya, где за ключ берется extension
    # print "получкенные данные ", extension, " ", fullName, " ", name, " ", etag, " ", last_modified, " прописываются в dataFromAvaya"
    dataFromAvaya.update({extension:[extension, fullName, name, etag, last_modified]})
      # запись данных а логфайл
    logger.info("\t\t\t" + extension + "\t" + fullName + "\t" + name + "\t"  + etag + "\t" + last_modified)
    # print "теперь dataFromAvaya = ", dataFromAvaya

        # ------------------------------------------------
        ### КОНЕЦ
        #       парсинг данных из IPO API
        # ------------------------------------------------



        # ------------------------------------------------
        ### парсинг данных из файла с IPO WEB
        # ------------------------------------------------

  logger.info("--- получение данных из файла Avaya_usersFromWEB.xml  ___________________________________________\n\t" + str(
    dictUsersFromAvaya_API))
  print ("--- получение данных из файла Avaya_usersFromWEB.xml   _____")

  extensionWEB = "-zero-"
  fullNameWEB = "-zero-"
  nameWEB = "-zero-"
  etagWEB = "-zero-"
  last_modifiedWEB = "-zero-"
  forwardWEB = "-zero-"
  twinningWEB = "-zero-"
  ReplayAllRecordingsWEB = "-zero-"
  ReplayOtherRecordingsWEB = "-zero-"

  for ws_object in treeXML_fromWEBfile[0]:
    for user in ws_object.findall('User'):
      # print "\n\n----------------\n\tUser = ", user, "\n\t\t User.text = ", user.text, "\n\t\t User.tag = ", user.tag, "\n\t\t User.attrib = ", user.attrib
        # определение Extension
      extensionWEB = user.find('Extension').text
      print "Extension = ", extensionWEB
        # определение Name
      nameWEB =  user.find('Name').text
      # print "Name = ", nameWEB
        # определение FullName
      fullNameWEB = user.find('FullName').text
      # print "FullName = ", fullNameWEB
        # определение ForwardNumber
      forwardWEB =  user.find('ForwardNumber').text
      # print "forwardWEB = ", forwardWEB
        # определение TwinnedMobileNumber
      twinningWEB = user.find('TwinnedMobileNumber').text
      # print "TwinnedMobileNumber = ", twinningWEB
        # определение ReplayAllRecordings
      replayAllRecordingsWEB = user.find('ReplayAllRecordings').text
      # print "ReplayAllRecordings = ", replayAllRecordingsWEB
        # определение ReplayOtherRecordings
      replayOtherRecordingsWEB = user.find('ReplayOtherRecordings').text
      # print "ReplayOtherRecordings = ", replayOtherRecordingsWEB
        # определение даты изменения (Etag)
      etagWEB = user.find('Etag').text
      # print "Etag = ", etagWEB
        # определение даты изменения (Last-Modified)
      last_modifiedWEB = user.find('Last-Modified').text
      # print "Last-Modified = ", last_modifiedWEB


     # сохранение полученных результатов в словаре dataFromAvaya, где за ключ берется extension
    dataFromAvayaWEB.update({extensionWEB:[extensionWEB, fullNameWEB, nameWEB, etagWEB, last_modifiedWEB, forwardWEB, twinningWEB, ReplayAllRecordingsWEB, ReplayOtherRecordingsWEB]})



   # запись данных в логфайл
  logger.info (dataFromAvayaWEB[extensionWEB][0] + "\t" + dataFromAvayaWEB[extensionWEB][1] + "\t" + dataFromAvayaWEB[extensionWEB][2] + "\t" + dataFromAvayaWEB[extensionWEB][3] + "\t" + dataFromAvayaWEB[extensionWEB][4] + "\t" + dataFromAvayaWEB[extensionWEB][5] + "\t" + dataFromAvayaWEB[extensionWEB][6] + "\t" + dataFromAvayaWEB[extensionWEB][7] + "\t" + dataFromAvayaWEB[extensionWEB][8])



        # ------------------------------------------------
        ### КОНЕЦ парсинг данных из файла с IPO WEB
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
        ### вывод данны из файла с WEB IPO
        # ------------------------------------------------

  logger.info("\n\n___________________________________________\n Данные из файла с API WEB")
  print("\n\n___________________________________________\n Данные из файла с API WEB")
    # заголовок таблицы данных
  logger.info("Extension" + "\t" + "FullName" + "\t" + "Name" + "\t" + "Etag" + "\t" + "Last-Modified" + "\t" + "forward" + "\t" + "twinning" + "\t" + "ReplayAllRecordings" + "\t" + "ReplayOtherRecordings")
  # print "dataFromAvayaWEB.keys()= ", dataFromAvayaWEB.keys()
  for ext in dataFromAvayaWEB.keys():
    logger.info(str(ext) + "\t\t\t" + str(dataFromAvayaWEB[ext][0]) + "\t" + str(dataFromAvayaWEB[ext][1]) + "\t" + str(dataFromAvayaWEB[ext][2]) + "\t" + str(dataFromAvayaWEB[ext][3]) + "\t" + str(dataFromAvayaWEB[ext][4]) + "\t" + str(dataFromAvayaWEB[ext][5]) + "\t" + str(dataFromAvayaWEB[ext][6]))
    print "log WEB OK for ext", ext

        # ------------------------------------------------
        ### КОНЕЦ вывод данны из файла с WEB IPO
        # ------------------------------------------------



        # ------------------------------------------------
        ### проверка что данные API и файла с WEB совпадают
        # ------------------------------------------------


  logger.info("\n\n___________________________________________\n Сравненеие данных API IPO и файла с WEB IPO")
  print("\n\n___________________________________________\n Сравненеие данных API IPO и файла с WEB IPO")
  print "dataFromAvaya = ", dataFromAvaya
  for ext in dataFromAvaya.keys():
    print "ext = ", str(ext), " type(ext) = ", type(ext)
    if ext == '': continue            # там в dataFromAvaya прописан KEY со значением '' где 'RemoteManager'. Это создает ошибки; и нам не нужно. Поэтому не рассматривем
    if ext not in dataFromAvayaWEB:   # если рассматриваемого Extension нет в dataFromAvayaWEB
      print ("\t\t\tНомера " + ext + " нет в dataFromAvayaWEB")
      logger.inf("\t\t\tНомера " + ext + " нет в dataFromAvayaWEB")
      continue

    logger.info(str(ext) + "\n\t\t We habe from API \n\t\t\t" + str(dataFromAvaya[ext][0]) + "\t" + str(dataFromAvaya[ext][1]) + "\t" + str(dataFromAvaya[ext][2])+ "\t" + str(dataFromAvaya[ext][3]) + "\t" + str(dataFromAvaya[ext][4]) + "\n\t\t and from WEB \n\t\t" "\t" + str(dataFromAvayaWEB[ext][0]) + "\t" + str(dataFromAvayaWEB[ext][1]) + "\t" + str(dataFromAvayaWEB[ext][2]) + "\t" +str(dataFromAvayaWEB[ext][3]) + "\t" + str(dataFromAvayaWEB[ext][4]) + "\t" + str(dataFromAvayaWEB[ext][5]) + "\t" + str(dataFromAvayaWEB[ext][6]))

    # print "ext = ", str(ext)
    # logger.info(str(ext))
    # logger.info("\t\t We habe from API \n\t\t\t" + str(dataFromAvaya[ext][0]) + "\t" + str(dataFromAvaya[ext][1]) + "\t" + str(dataFromAvaya[ext][2])+ "\t" + str(dataFromAvaya[ext][3]) + "\t" + str(dataFromAvaya[ext][4]))
    # logger.info("\t\t from WEB \n\t\t\t" "\t" + str(dataFromAvayaWEB[ext][0]) + "\t" + str(dataFromAvayaWEB[ext][1]) + "\t" + str(dataFromAvayaWEB[ext][2]) + "\t" +str(dataFromAvayaWEB[ext][3]) + "\t" + str(dataFromAvayaWEB[ext][4]) + "\t" + str(dataFromAvayaWEB[ext][5]) + "\t" + str(dataFromAvayaWEB[ext][6]))


    if dataFromAvaya[ext][0] != dataFromAvayaWEB[ext][0]: logger.info("ExtensionAPI !- ExtensionWEB")
    if dataFromAvaya[ext][1] != dataFromAvayaWEB[ext][1]: logger.info("fullNameAPI !- fullNameWEB")
    if dataFromAvaya[ext][2] != dataFromAvayaWEB[ext][2]: logger.info("nameAPI !- nameWEB")
    if dataFromAvaya[ext][3] != dataFromAvayaWEB[ext][3]: logger.info("etagAPI !- etagWEB")
    if dataFromAvaya[ext][4] != dataFromAvayaWEB[ext][4]: logger.info("last_modifiedAPI !- last_modifiedWEB")
    print "log for ", ext, " end"

        # ------------------------------------------------
        ### КОНЕЦ проверка что данные API и файла с WEB совпадают
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
