from cnc.logger import get_logger

log = get_logger(__name__)


class AmazonAppServiceAccount:
    def __init__(self, collection):
        self.collection = collection
