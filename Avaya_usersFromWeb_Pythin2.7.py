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
  Описание скрипта
  -----------------


С помощью этого скрипта можно получить данные по Users из файла Avaya_usersFromWEB.xml
  Сам .xml файл берется из IPO WebManagement при выборе Call Management -> Users, 
                                                                и там Tools -> Export -> User 
  
      Данный файл надо переименовать в Avaya_usersFromWEB.xml, и поместить в папку с данным скриптом

  В этом файле более полная выгрузка по Users, чем посредством IPO API
          
    В разделе  "### парсинг данных из файла from IPO manager" указывается какие данные читаются
          
    В разделе "### вывод данны из файла from IPO manager"   данные выводятся на экран (процессы); и конечные данные - в логфайл Avaya_usersFromWeb_Pythin2.7.log
          


Работает с любого компа где установлен Python 2.7

_____________________________________________________________________________________________________________________________________________________"""








"""
  настойки систем
_____________________________________________________________________________________________________________________________________________________"""


  #################
  # set loggimg
  #################

  # Logging initializing
log_file = './Avaya_usersFromWeb_Pythin2.7.log'
  #logging.basicConfig()
logger = logging.getLogger("Avaya_usersFromWeb_Pythin2.7")
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


dataFromAvaya_FilefromWEB = {}


"""
  КОНЕЦ
    настойки систем
_____________________________________________________________________________________________________________________________________________________"""















logger.info("\n\n\n\n\n\n\n\n\n------------------------------------ The program starts \n---------------------------------------")
print "\n---------------------------------------\n\tThe program starts\n---------------------------------------"

try:

        # ------------------------------------------------
        ### работа с файлом
        # ------------------------------------------------

    # чтение данных из файла Avaya_usersFromIPOmanager.xml для получения дополнительных данных (о forward & twinning)

  treeXML_fromWEBfile = ET.parse('Avaya_usersFromWEB.xml').getroot()

    # ________________________________ конец  чтение данных из файла Avaya_usersFromIPOmanager.xml'


        # ------------------------------------------------
        ### <---------- КОНЕЦ работа с файлом
        # ------------------------------------------------




        # ------------------------------------------------
        ###    парсинг полученных данных
        # _________________________________________________



        # ---------------------------------------------------
        ### парсинг данных из файла from IPO manager
        # ---------------------------------------------------

  logger.info("--- получение данных из файла Avaya_usersFromWEB.xml  ___________________________________________\n\t")
  print ("--- получение данных из файла Avaya_usersFromWEB.xml   _____")

  extension_IPOmanager = "-zero-"
  fullName_IPOmanager = "-zero-"
  name_IPOmanager = "-zero-"
  DownloadRecordings_IPOmanager = "-zero-"


  for ws_object in treeXML_fromWEBfile[0]:
    for user in ws_object.findall('User'):
      # print "\n\n----------------\n\tUser = ", user, "\n\t\t User.text = ", user.text, "\n\t\t User.tag = ", user.tag, "\n\t\t User.attrib = ", user.attrib
        # определение Extension
      extension_WEB = user.find('Extension').text
      print "Extension = ", extension_WEB
        # определение Name
      name_WEB =  user.find('Name').text
      # print "Name = ", fullName_WEB
        # определение FullName
      fullName_WEB  = user.find('FullName').text
      # print "FullName = ", name_WEB
        # определение DownloadRecordings
      DownloadRecordings_WEB =  user.find('DownloadRecordings').text
      # print "forwardWEB = ", DownloadRecordings_WEB



     # сохранение полученных результатов в словаре dataFromAvaya, где за ключ берется extension
    dataFromAvaya_FilefromWEB.update({extension_WEB:[extension_WEB, name_WEB, fullName_WEB, DownloadRecordings_WEB]})



     # запись данных в логфайл
    # logger.info ("\t" + dataFromAvaya_FilefromWEB[extension_WEB][0] + "\t" + dataFromAvaya_FilefromWEB[extension_WEB][1] + "\t" + dataFromAvaya_FilefromWEB[extension_WEB][2] + "\t" + dataFromAvaya_FilefromWEB[extension_WEB][3])



        # ---------------------------------------------------------
        ### КОНЕЦ парсинг данных из файла from IPO manager
        # ---------------------------------------------------------




        # ------------------------------------------------
        ### вывод данны из файла from IPO manager
        # ------------------------------------------------

  logger.info("\n\n___________________________________________\n Данные из файла from IPO manager")
  print("\n\n___________________________________________\n Данные из файла from IPO manager")
    # заголовок таблицы данных
  logger.info("\t\t\tExtension" + "\t" + "Name" + "\t" + "FullName" + "\t" + "DownloadRecordings")
  # print "dataFromAvayaWEB.keys()= ", dataFromAvayaWEB.keys()
  for ext in dataFromAvaya_FilefromWEB.keys():
    logger.info(str(ext) + "\t\t\t" + str(dataFromAvaya_FilefromWEB[ext][0]) + "\t" + str(dataFromAvaya_FilefromWEB[ext][1]) + "\t" + str(dataFromAvaya_FilefromWEB[ext][2]) + "\t" + str(dataFromAvaya_FilefromWEB[ext][3]))
    print "log из файла from IPO manager OK for ext", ext

        # ------------------------------------------------
        ### КОНЕЦ вывод данны из файла from IPO manager
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
