#  coding: utf-8

import sys
from ldap3 import Server, Connection, ALL
import logging
from logging.handlers import RotatingFileHandler



# для изменения кодировки 1
import sys
  # определение кодировки
reload(sys)
sys.setdefaultencoding('utf8')
  # _______________________________


"""
  Описание скрипта
  -----------------

  Читает Users в AD , и выдает по ним все (или указанные) данные
    
    В разделе "# какие атрибуты показать" определено какие именно данные учеток показывать
  
  Обрабатывает только 1000 записей
  
    Но даже при этом ограничении, размера log файлов может не хватить.
      Тогда надо или увеличить максимальный размер log файле (переменная maxBytes - в байтах)
        или увеличить количество log файлов (переменная backupCount )


Работает с любого компа где установлен Python 2.7

_____________________________________________________________________________________________________________________________________________________"""






"""
  настойки систем
_____________________________________________________________________________________________________________________________________________________"""


  #------------------ логирование -----------------

   # Logging initializing
log_file = './AD_listUsersWithData_Pythin2.7.log'
logger = logging.getLogger("AD_listUsersWithData_Pythin2.7")
logger.setLevel(logging.DEBUG)
  # Set logging level @ params
maxBytes = 500000  # когда размер текущего лог-файла достигнет размера,  следующие записи будут попадать в другие файлы
backupCount = 1  # сколько всего будет сохраняться старых файлов логов (старые будут стираться) (+ рабочий файл)
handler = RotatingFileHandler(log_file, maxBytes=maxBytes, backupCount=backupCount, mode='a', encoding=None, delay=0)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s line %(lineno)d:   %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)




 # ------------------ LDAP Settings -----------------
ldaphost = имя хоста LDAP (в кавычках)
ldaproot = 'dc=...,dc=LOCAL' вместо точек - требуемые параметры
ldapuser = 'cn=...,ou=...,ou=service users,dc=..,dc=local' вместо точек - требуемые параметры
ldappass = пароль доступа LDAP (в кавычках)
LDAPServer = Server(ldaphost, get_info=ALL)


      #------------------------------------------------
      # какие атрибуты показать
      #------------------------------------------------

attributes = ['*']   # выводит все атрибуты каждой найденной записи в AD
# attributes = ['telephoneNumber', 'memberOf']  # или здесь можно прописать какие атрибуты показать
# attributes = ['telephoneNumber']  # или здесь можно прописать какие атрибуты показать


"""
  КОНЕЦ 
    настойки систем
_____________________________________________________________________________________________________________________________________________________"""





"""
    сама прога
_____________________________________________________________________________________________________________________________________________________"""


print "\nЗапусквется поиск в AD\n_____________________________________________________________________________________________________________________________________________________\n\n"
logger.info("\n\n\n\n\n\n\n\n\n------------------------------------ The program starts \n---------------------------------------")



try:

    # LDAP initializing - Получение из LDAP данных по пользователям
  LDAPConn = Connection(LDAPServer, ldapuser, ldappass, auto_bind=True)


  LDAPConn.search(ldaproot, '(&(objectClass=person))', attributes=attributes)
  print("LDAPConn.search  OK ")
  logger.info("LDAPConn.search  OK ")
  len_LDAPConnEntries = len(LDAPConn.entries)
  print("Сколько учеток прочитано прочиьанно: " + str(len_LDAPConnEntries))
  logger.info("Сколько учеток прочитано прочиьанно: " + str(len_LDAPConnEntries))


  i = 0
  while i < len_LDAPConnEntries:
      print "\n--------------------------------------------"
      logger.info ("--------------------------------------------")
        # если считаем сразу все данные
      if attributes == ['*']:
          print(str(LDAPConn.entries[i]))
          logger.info(str(LDAPConn.entries[i]))
          continue
        # если определено какие именно данные прочитать и показать
      for attribute in attributes:
          print(attribute + " = " + str(LDAPConn.entries[i][attribute]))
          logger.info(attribute + " = " + str(LDAPConn.entries[i][attribute]))
      i = i + 1


except Exception as e:
  print '\n\t!!!!!!!!!!!!!!!!!  find in LDAP - A type error occurred: ', str(e)
  print '\tError by find in LDAP: ' + str(sys.exc_info())
  sys.exit()




"""
  КОНЕЦ
    сама прога
_____________________________________________________________________________________________________________________________________________________"""



logger.info("\n------------------------------------ The program ends \n---------------------------------------\n\n\n\n\n")
print "\n---------------------------------------\n\tThe program ends\n---------------------------------------"