from TrafficJuggler.models.base import Base
from TrafficJuggler.models.host import Host
from TrafficJuggler.models.interface import Interface
from TrafficJuggler.models.image import Image
from TrafficJuggler.models.lsp import LSP
from TrafficJuggler.models.prefix import Prefix
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import FULL_PATH

# engine = create_engine('sqlite:///{path}/tj.db'.format(path=FULL_PATH))
engine = create_engine('mysql+pymysql://tj:trafficjuggler@localhost/tj')
Base.metadata.bind = engine
Base.metadata.create_all(engine)

Session = sessionmaker(bind = engine)
session = Session()
