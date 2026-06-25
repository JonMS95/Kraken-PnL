import logging
from inspect import stack

class DataLogger:
    """
    Provides a logging utility for a Python module.

    This class initializes a logger instance for a module and sets its
    logging level to DEBUG by default. It can be used to log messages
    throughout the module consistently.

    Attributes:
        _logger : logging.Logger
            Instance of a Python logger used for recording debug and info messages.
    """
    
    __log_format    : str               = "%(asctime)s - %(filename)s - %(levelname)s - %(message)s"
    __logger        : logging.Logger    = None
    __log_caller_fn : bool              = None

    def __init__(self, name: str = __name__, level: int = logging.DEBUG, log_caller_fn: bool = True):
        """
            Initializer logger object (constructor method).
            
            Args:
                name            : Logger's target name.
                level           : Logger's level (the closer to DEBUG / lower, the more detailed the output will be).
                log_caller_fn   : Tells whether the calling function's name should be logged.
        """
                
        self.__logger = logging.getLogger(name)
        self.__logger.setLevel(level)
        self.__logger.propagate = False # Just in case.

        if not self.__logger.handlers:  # Only add a handler if none exists
            self.handler = logging.StreamHandler()
            self.handler.setFormatter(logging.Formatter(self.__log_format))
            self.__logger.addHandler(self.handler)

        self.__log_caller_fn = log_caller_fn


    def _add_calling_fn_name(self, msg: str) -> str:
        """
            Adds caller function's name (if required).
            
            Args:
                msg : Message to be logged.
            
            Returns:
                Processed message.
        """
        return ('(' + stack()[2].function + ") " + msg) if self.__log_caller_fn else msg


    def log_dbg(self, msg: str = "") -> None:
        """
            Logs debug message.
            
            Args:
                msg : Message to be logged.
        """
        self.__logger.debug(self._add_calling_fn_name(msg))
    

    def log_inf(self, msg: str = "") -> None:
        """
            Logs info message.
            
            Args:
                msg : Message to be logged.
        """
        self.__logger.info(self._add_calling_fn_name(msg))
    

    def log_wng(self, msg: str = "") -> None:
        """
            Logs warning message.
            
            Args:
                msg : Message to be logged.
        """
        self.__logger.warning(self._add_calling_fn_name(msg))
    

    def log_err(self, msg: str = "") -> None:
        """
            Logs error message.
            
            Args:
                msg : Message to be logged.
        """
        self.__logger.error(self._add_calling_fn_name(msg))
    
    
    def log_crt(self, msg: str = "") -> None:
        """
            Logs critical message.
            
            Args:
                msg : Message to be logged.
        """
        self.__logger.critical(self._add_calling_fn_name(msg))
