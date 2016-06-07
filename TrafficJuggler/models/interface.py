from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from TrafficJuggler.models.base import Base
from TrafficJuggler.models.image import Image

class Interface(Base):
    __tablename__ = "interfaces"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(String(255))
    speed = Column(Integer)
    output = Column(Integer)
#    state = Column(String(255))
    utilization = Column(Integer)
    image_id = Column(Integer, ForeignKey('images.id'))
    image = relationship(Image, backref='interfaces')


    def __repr__(self):
        return "<Interface ({name})>".format(name=self.name)
