from sqlalchemy import Column, Integer, String, UniqueConstraint
from TrafficJuggler.models.base import Base

class Host(Base):
    __tablename__ = "hosts"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    ip = Column(String(255))

    def __repr__(self):
        return "<Host ({name}, {ip})>".format(name=self.name, ip=self.ip)
