#!/usr/bin/python
from mpls import *
import re

def getSnmpOids():
    result = {}
    executor = mExecutor('m9-r0')
    lsps_tree = executor.execute('show snmp mib walk decimal 1.3.6.1.4.1.2636.3.2.3.1.17.109.57')
    lsps_objects = lsps_tree.xpath('//snmp-object')
    for lsp in lsps_objects:
        oid = lsp.xpath('string(oid/text())')
        name = lsp.xpath('string(object-value/text())')
        result[name] = oid
    return result

lsps = getSnmpOids()

for l in lsps:
    lsps[l] = re.sub('1.3.6.1.4.1.2636.3.2.3.1.17.','',lsps[l])

items = ""
graphs = ""
for name, oid in lsps.iteritems():
	items += """
               <item>
                    <name>""" + name + """ bandwith</name>
                    <type>4</type>
                    <snmp_community>qwsxczasde</snmp_community>
                    <multiplier>1</multiplier>
                    <snmp_oid>SNMPv2-SMI::enterprises.2636.3.2.3.1.21.""" + oid + """</snmp_oid>
                    <key>""" + name + """_bandwith</key>
                    <delay>300</delay>
                    <history>90</history>
                    <trends>365</trends>
                    <status>0</status>
                    <value_type>3</value_type>
                    <allowed_hosts/>
                    <units>bps</units>
                    <delta>0</delta>
                    <snmpv3_contextname/>
                    <snmpv3_securityname/>
                    <snmpv3_securitylevel>0</snmpv3_securitylevel>
                    <snmpv3_authprotocol>0</snmpv3_authprotocol>
                    <snmpv3_authpassphrase/>
                    <snmpv3_privprotocol>0</snmpv3_privprotocol>
                    <snmpv3_privpassphrase/>
                    <formula>1000</formula>
                    <delay_flex/>
                    <params/>
                    <ipmi_sensor/>
                    <data_type>0</data_type>
                    <authtype>0</authtype>
                    <username/>
                    <password/>
                    <publickey/>
                    <privatekey/>
                    <port/>
                    <description/>
                    <inventory_link>0</inventory_link>
                    <applications/>
                    <valuemap/>
                </item>
                <item>
                    <name>""" + name + """ name</name>
                    <type>4</type>
                    <snmp_community>qwsxczasde</snmp_community>
                    <multiplier>0</multiplier>
                    <snmp_oid>SNMPv2-SMI::enterprises.2636.3.2.3.1.17.""" + oid + """</snmp_oid>
                    <key>""" + name + """_name</key>
                    <delay>3600</delay>
                    <history>90</history>
                    <trends>365</trends>
                    <status>0</status>
                    <value_type>1</value_type>
                    <allowed_hosts/>
                    <units/>
                    <delta>0</delta>
                    <snmpv3_contextname/>
                    <snmpv3_securityname/>
                    <snmpv3_securitylevel>0</snmpv3_securitylevel>
                    <snmpv3_authprotocol>0</snmpv3_authprotocol>
                    <snmpv3_authpassphrase/>
                    <snmpv3_privprotocol>0</snmpv3_privprotocol>
                    <snmpv3_privpassphrase/>
                    <formula>1</formula>
                    <delay_flex/>
                    <params/>
                    <ipmi_sensor/>
                    <data_type>0</data_type>
                    <authtype>0</authtype>
                    <username/>
                    <password/>
                    <publickey/>
                    <privatekey/>
                    <port/>
                    <description/>
                    <inventory_link>0</inventory_link>
                    <applications/>
                    <valuemap/>
                </item>
                <item>
                    <name>""" + name + """ octets</name>
                    <type>4</type>
                    <snmp_community>qwsxczasde</snmp_community>
                    <multiplier>1</multiplier>
                    <snmp_oid>SNMPv2-SMI::enterprises.2636.3.2.3.1.3.""" + oid + """</snmp_oid>
                    <key>""" + name + """_octets</key>
                    <delay>120</delay>
                    <history>90</history>
                    <trends>365</trends>
                    <status>0</status>
                    <value_type>3</value_type>
                    <allowed_hosts/>
                    <units>bps</units>
                    <delta>1</delta>
                    <snmpv3_contextname/>
                    <snmpv3_securityname/>
                    <snmpv3_securitylevel>0</snmpv3_securitylevel>
                    <snmpv3_authprotocol>0</snmpv3_authprotocol>
                    <snmpv3_authpassphrase/>
                    <snmpv3_privprotocol>0</snmpv3_privprotocol>
                    <snmpv3_privpassphrase/>
                    <formula>8</formula>
                    <delay_flex/>
                    <params/>
                    <ipmi_sensor/>
                    <data_type>0</data_type>
                    <authtype>0</authtype>
                    <username/>
                    <password/>
                    <publickey/>
                    <privatekey/>
                    <port/>
                    <description/>
                    <inventory_link>0</inventory_link>
                    <applications/>
                    <valuemap/>
                </item>
"""
	graphs += """
        <graph>
            <name>LSP """ + name + """</name>
            <width>900</width>
            <height>200</height>
            <yaxismin>0.0000</yaxismin>
            <yaxismax>100.0000</yaxismax>
            <show_work_period>1</show_work_period>
            <show_triggers>1</show_triggers>
            <type>0</type>
            <show_legend>1</show_legend>
            <show_3d>0</show_3d>
            <percent_left>0.0000</percent_left>
            <percent_right>0.0000</percent_right>
            <ymin_type_1>0</ymin_type_1>
            <ymax_type_1>0</ymax_type_1>
            <ymin_item_1>0</ymin_item_1>
            <ymax_item_1>0</ymax_item_1>
            <graph_items>
                <graph_item>
                    <sortorder>0</sortorder>
                    <drawtype>2</drawtype>
                    <color>6666FF</color>
                    <yaxisside>1</yaxisside>
                    <calc_fnc>2</calc_fnc>
                    <type>0</type>
                    <item>
                        <host>LSP m9-r0</host>
                        <key>""" + name + """_octets</key>
                    </item>
                </graph_item>
                <graph_item>
                    <sortorder>1</sortorder>
                    <drawtype>3</drawtype>
                    <color>FF33FF</color>
                    <yaxisside>1</yaxisside>
                    <calc_fnc>2</calc_fnc>
                    <type>0</type>
                    <item>
                        <host>LSP m9-r0</host>
                        <key>""" + name + """_bandwith</key>
                    </item>
                </graph_item>
            </graph_items>
        </graph>"""

final_result = """<?xml version="1.0" encoding="UTF-8"?>
<zabbix_export>
    <version>2.0</version>
    <date>2015-10-08T12:16:37Z</date>
    <groups>
        <group>
            <name>Routers</name>
        </group>
        <group>
            <name>Templates</name>
        </group>
    </groups>
    <templates>
        <template>
            <template>LSP m9-r0</template>
            <name>LSP m9-r0</name>
            <groups>
                <group>
                    <name>Routers</name>
                </group>
                <group>
                    <name>Templates</name>
                </group>
            </groups>
            <applications/>
            <items>""" + items + """            </items>
            <discovery_rules/>
            <macros/>
            <templates/>
            <screens/>
        </template>
    </templates>
    <graphs>
""" + graphs + """
    </graphs>
</zabbix_export>
"""

with open('lsps.xml','wr') as f:
    f.write(final_result)
