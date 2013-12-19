#!/usr/bin/python2.7

import web,os,json,re
from common.restfulclient import RestfulClient
from common.restfulclient import RestfulError

from common import deal_array_data_for_client_ui,get_method_query_to_map

urls = (
    '/adaptors', 'Adaptors',
    '/nameserver', 'Nameserver',
    '/hostname', "Hostname",
    '/route', 'Route',
    '/iptables', "Iptables",
    '/iptablesmodel', "IptablesModel",
    '/tools', "Tools"
)

class Adaptors:
    def GET(self):
        render = web.template.frender("./view/templates/network_adaptors.html")
        return render()
        
class Nameserver:
    def GET(self):
        try:
            res = RestfulClient.getresponse("GET", "/network/nameserver")
        except Exception as e:
            raise RestfulError(e.message)
        else:
            render = web.template.frender("./view/templates/network_dns.html")
            #res = re.sub("\\\\\"", "\\\\\\\\\"", res)
            return render()

class Hostname:
    def GET(self):
        try:
            res = RestfulClient.getresponse("GET", "/network/hostname")
        except Exception as e:
            raise RestfulError(e.message)
        else:
            render = web.template.frender("./view/templates/network_hostname.html")
            return render(res)

class Route:
    def GET(self):
        render = web.template.frender("./view/templates/network_routes.html")
        return render()

class Iptables:
    def GET(self):
        render = web.template.frender("./view/templates/network_iptables.html")
        return render()
        
class IptablesModel:
    def repack_data(self, data, query):
        query = get_method_query_to_map(query)
        data_list = []
        for type in data.keys():
            if "type" in query and type != query["type"]:
                continue;
            for chain in data[type].keys():
                if "chain" in query and chain != query["chain"]:
                    continue;
                data_array = data[type][chain]
                for d in data_array:
                    d["type"] = type
                    d["chain"] = chain
                    data_list.append(d)
        return data_list
        
    def GET(self):
        try:
            query = web.ctx.query[1:]
            res = RestfulClient.getresponse("GET", "/network/iptables")
            record_set = json.loads(res);
            record_set = self.repack_data(record_set, query);
            #record_set = deal_array_data_for_client_ui(query, record_set);
            res = json.dumps(record_set)
        except Exception as e:
            raise RestfulError(e.message)
        else:
            return res

class Tools:
    def GET(self):
        render = web.template.frender("./view/templates/network_tools.html")
        return render()

app = web.application(urls, locals())
