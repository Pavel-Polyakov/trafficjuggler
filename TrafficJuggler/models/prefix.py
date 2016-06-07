from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from TrafficJuggler.models.base import Base
from TrafficJuggler.models.host import Host


class Prefix(Base):
    __tablename__ = "prefixes"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    host_ip = Column(String(255))
    host_id = Column(Integer, ForeignKey('hosts.id'))
    host = relationship(Host, backref='prefixes')

    def __repr__(self):
        return "<Prefix ({name}, {host_ip})>".format(name=self.name, host_ip=self.host_ip)
