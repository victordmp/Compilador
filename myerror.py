import configparser
import inspect

config = None

class MyError():

  def __init__(self, et, showErrorMessage=False):
    self.config = configparser.RawConfigParser()
    self.config.read('ErrorMessages.properties')
    self.errorType = et
    self.showErrorMessage = showErrorMessage

  def newError(self, key, **data):
    message = ''
    if (self.showErrorMessage):
      if(key):
        message = self.config.get(self.errorType, key)
      if(data):
        for key, value in data.items():
          message = message + ", " f"{key}: {value}"
    else:
      message = key

    return message