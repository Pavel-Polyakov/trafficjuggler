from TrafficJuggler.models.base import Base
from TrafficJuggler.models.interface import Interface
from TrafficJuggler.models.lsp import LSP
from TrafficJuggler.models.image import Image
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine('sqlite:///tj.db')
Base.metadata.bind = engine
Base.metadata.create_all(engine)

Session = sessionmaker(bind = engine)
session = Session()
