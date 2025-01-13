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


С помощью этого скрипта можно узнать какие пулы Exteisions в системе Avaya IP Office свободны.
  Помогает, когда, например, надо прописать несколько номеров для одного отдела, - чтобы у них были "похожие" номера.
  
  --- Это программа написана, исходя из предположения, что у каждого User в система IPO есть соответствующий Extension (!!!как и должно быть!!!) ---
  
  При выполнении программы запрашивается "Введите размер пула номеров который вам требуется (от 1 до 99)". 
    Там вводится сколько новых номеров требуется прописать в системе Avaya IPO.
    
    Далее прога рассматривает разницу между соседними номерами, и показывает сколько номеров можно прописать "между двумя соседними" (это надпись "pool = ... ")
       Нумерная емкость менее 6200 (это значение устанавливается переменной first) не рассматривается.
       
  Если найден пул свободных номеров равный, или больший, запрашиваемого, программа останавливается, и выводится инфо "Найден подходящий пул не используемой нумерации: ... "
    
Данные выводятся на экран, и (более подробные) в лог файл Avaya_extensions_searchEmptyPool.log
  

  Возможны варианты исполнения:
    1. в разделе "настойки систем -> # IPO Settings " прописываются IPaddress сервера Avaya IPO, и логин, пароль API доступа на него
    
    2. есть раздел "### ----------> чтение данных с API IPO"
                при его активации, данные читаются с API IPO
                
    3. есть раздел "### ----------> работа с файлом, чтобы не постоянно читать данные с системы IPO" в который входят подразделы 
            "# сохранения данных в файл Avaya_extensionsData_response" 
              и
            "# чтение данных из файла Avaya_extensionsData_response.content.data"
      
      3.1 при активации "# сохранения данных в файл Avaya_extensionsData_response'" данные, прочитанные в API IPO сохраняются в файл.
                 Если такой файл уже есть, но данные в нем ПЕРЕЗАПИСЫВАЮТСЯ
                                   
      3.2 при активации "# чтение данных из файла Avaya_extensionsData_response.content.data'"  данные, ранее полученные с API IPO м записанные в файл, 
                 читаются из этого файла. 
                 
                 Т.е. в данном случае чтение данных API и из запись в файл надо отключить.

                 
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
    print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e)
    logger.info('\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e))
    print ('\n\tError by authorizationIPO(): ' + str(sys.exc_info()))
    logger.info('\n\tError by authorizationIPO(): ' + str(sys.exc_info()))
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




      #-------------------------------------------
      # ввод данных от пользователя
      # и проверка, что введена цифра от 1 до 99,
      # а не что-то другое
      #--------------------------------------------

def question_answer(question):
  answer = raw_input(question)
  while chackItIsDigit(answer) == 0:
    answer = raw_input(question)
  return str(answer)

def chackItIsDigit(answer):
  try:
    if int(answer) > 0 and int(answer) < 100:
      return 1
    return 0
  except ValueError:
    return 0

      # -------------------------------------------
      # КОНЕЦ
      #   ввод данных от пользователя
      #   и проверка, что введена цифра от 1 до 99,
      #   а не что-то другое
      # --------------------------------------------


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
log_file = './Avaya_extensions_searchEmptyPool.log'
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


dictExtensionsFromAvaya = {}  # - dict, полученный от API Avaya IPO
dataFromAvayaExtensions = {}  # - dict номеров


"""
  КОНЕЦ
    настойки систем
_____________________________________________________________________________________________________________________________________________________"""





logger.info("\n\n\n\n\n\n\n\n\n------------------------------------ The program starts \n---------------------------------------")
print "\n---------------------------------------\n\tThe program starts\n---------------------------------------"

try:


# ------------------------------------------------
###  чтение данных из IPO
# _________________________________________________

    # аутентификация в Avaya IPO
  authorizationIPO()


   # чтение данных по Extensions из Avaya
  response_extensionsData = sessionGet("extensions")

  textExtensionsFromAvaya = response_extensionsData.content  # активировать при чтении данных с IPO !!!

# ------------------------------------------------
###  КОНЕЦ
###    чтение данных из IPO
# _________________________________________________



  ### ----------> работа с файлом, чтобы не постоянно читать данные с системы IPO

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
  #  # ________________________________ конец  чтение данных из файла Avaya_extensionsData_response.content.data'

   ### <---------- КОНЕЦ работа с файлом





# ------------------------------------------------
###    парсинг полученных данных
# _________________________________________________


  exec ('dictExtensionsFromAvaya = ' + textExtensionsFromAvaya)
  logger.info("--- получено dictExtensionsFromAvaya ___________________________________________\n\t" + str(dictExtensionsFromAvaya))
  # print ("--- получено dictExtensionsFromAvaya _____")



    # захват первого-отдельного описанного в dictExtensionsFromAvaya значения Extansion
  dataFromAvayaExtensions.update({str(dictExtensionsFromAvaya["response"]["data"]["ws_object"]["Extension"][1]):
                                    [str(dictExtensionsFromAvaya["response"]["data"]["ws_object"]["Extension"][1]),
                                     str(dictExtensionsFromAvaya["response"]["data"]["ws_object"]["Extension"][0]["@GUID"])]})



    # парсинг остальных описанных в dictExtensionsFromAvaya значений Extansions
  for dataExtension in dictExtensionsFromAvaya["ws_object"]:
    logger.info("--- получено dataExtension from textExtensionsFromAvaya ___________________________________________\n\t"+ str(dataExtension))
    # print ("--- получено dataExtension from textExtensionsFromAvaya ___________________________________________")
    extension = str(dataExtension['Extension'][1])
    # print "\t\t\textension = " + extension
    guid = str(dataExtension['Extension'][0]['@GUID'])
    # print "\t\t\tguid = " + guid

     # сохранение полученных результатов в словаре dataFromAvaya, где за ключ берется extension
    dataFromAvayaExtensions.update({extension:[extension, guid]})

# ------------------------------------------------
#  КОНЕЦ
#    парсинг полученных данных
# _________________________________________________




      # сорторивка словаря с extensions по extension
  dataFromAvayaExtensions = collections.OrderedDict(sorted(dataFromAvayaExtensions.items()))





###########################
# вывод полученных данных
# и поискт пула не занятых номеров
###########################

    # запрос - пул не занятых номеров какого размера требуется
  poolSize = question_answer("Введите размер пула номеров который вам требуется (от 1 до 99): ")
  print "\t\tВы запросили пул для " + poolSize + " номеров"

  first = 6200   # определяет номер менее которого новую нумерацию не рассматривать
  for extension in dataFromAvayaExtensions.keys():
    print extension               # вывод рассматриваемого extension на экран
    logger.info(str(extension))   # вывод рассматриваемого extension в логфвйл
    if int(extension) < first:
      print "\t\tНумерная емкость менее " + str(first) + " не рассматривается"
      logger.info("\t\tНумерная емкость менее " + str(first) + " не рассматривается")
      continue
    last = int(extension)
    pool = last - first - 1
    print "\t\tpool = " + str(pool)                # вывод рассччитанного пула номеров на экран
    logger.info("\t\tpool = " + str(pool))         # вывод рассччитанного пула номеров в логфвйл
    if pool >= int(poolSize):
      print "\tНайден подходящий пул не используемой нумерации: " + str(first+1) + " - " +  str(last-1)
      logger.info("\tНайден подходящий пул не используемой нумерации: " + str(first+1) + " - " +  str(last-1))
      break
    first = last

###########################
#  КОНЕЦ
#   вывод полученных данных
#     и поискт пула не занятых номеров
###########################



except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e)
  logger.info('\n\t!!!!!!!!!!!!!!!!! Возникла ошибка типа: ' + str(e))
  print '\n\tError by basic Proga: ' + str(sys.exc_info())
  logger.info('\n\tError by basic Proga: ' + str(sys.exc_info()))
  sys.exit()

finally:
  session.close()

  
logger.info("\n------------------------------------ The program ends \n---------------------------------------\n\n\n\n\n")
print "\n---------------------------------------\n\tThe program ends\n---------------------------------------"
