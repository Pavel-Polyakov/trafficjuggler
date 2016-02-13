from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from TrafficJuggler.models.base import Base

class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    speed = Column(Integer)
    output = Column(Integer)
    state = Column(String)
    image_id = Column(Integer, ForeignKey('images.id'))
    image = relationship(Image, back_populates="interfaces")

    def __repr__(self):
        return "<Interface ({name})>".format(name=self.name)
