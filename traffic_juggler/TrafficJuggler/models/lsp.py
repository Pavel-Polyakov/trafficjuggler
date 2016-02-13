from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

from TrafficJuggler.models.interface import Interface
from TrafficJuggler.models.image import Image
from TrafficJuggler.models.base import Base

class LSP(Base):
    __tablename__ = "lsps"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    to = Column(String)
    path = Column(String)
    bandwidth = Column(Integer)
    rbandwidth = Column(Float)
    state = Column(String)
    output = Column(Integer)
    interface_id = Column(Integer, ForeignKey('interfaces.id'))
    interface = relationship(Interface, backref="lsps")
    image_id = Column(Integer, ForeignKey('images.id'))
    image = relationship(Image, backref="lsps")

    def __repr__(self):
        return "<LSP ({name})>".format(name=self.name)
