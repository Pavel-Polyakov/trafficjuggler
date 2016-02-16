from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from TrafficJuggler.models.base import Base


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime(timezone=True), default=func.now())
    router = Column(String)

    def __repr__(self):
        return "<Image ({router},{time})>".format(router=self.router,
                                                  time=self.time)
