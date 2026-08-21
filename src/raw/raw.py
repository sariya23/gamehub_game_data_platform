from abc import ABC, abstractmethod
from io import BytesIO


class S3(ABC):
    @abstractmethod
    def upload_file(self, data: BytesIO, object_name: str, l: int):
        pass


class RawStorage:
    def __init__(self, s3: S3):
        self.__s3 = s3
    
    # @staticmethod
    # def make_object_name(source: str)