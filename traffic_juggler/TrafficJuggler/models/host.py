from sqlalchemy import Column, Integer, String, UniqueConstraint
from TrafficJuggler.models.base import Base

class Host(Base):
    __tablename__ = "hosts"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    ip = Column(String)

    def __repr__(self):
        return "<Host ({name}, {ip})>".format(name=self.name, ip=self.ip)
