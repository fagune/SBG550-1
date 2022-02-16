from email.policy import default
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, arp, icmp
from ryu.lib.packet import ether_types
import re, urllib.request

def regex():
 try:
  urllib.request.urlretrieve("https://www.usom.gov.tr/url-list.txt", r"/home/fatih/Desktop/usom.txt")
  ip=[]
  url=[]
  with open(r"/home/fatih/Desktop/usom.txt") as fh: 
   fstring = fh.readlines()
   for line in fstring:
    if re.findall(r'^\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b$',str(line)):
     ip.append(line)
    else:
     url.append(line)
  with open(r"/home/fatih/Desktop/ip_usom.txt","a") as ip_file: 
   for line in ip:
    ip_file.write(str(line) + "\n")   
  with open(r"/home/fatih/Desktop/url_usom.txt","a") as url_file:
   for line2 in url:
    url_file.write(str(line2) + "\n")    
 except ValueError:
  print("Hata oluştu!")
regex()

class SDNHub(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SDNHub, self).__init__(*args, **kwargs)
        # initialize mac address table.
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        arp_pkt = pkt.get_protocol(arp.arp)
        dst = eth_pkt.dst
        src = eth_pkt.src


        # get the received port number from packet_in message.
        in_port = msg.match['in_port']            

        # self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # if the destination mac address is already learned,
        # decide which port to output the packet, otherwise FLOOD.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        # boş arrayi action olarak verirsek drop olur
        # construct action list.
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time.

	 with open(r"/home/fatih/Desktop/ip_usom.txt","a") as ip_file: 
   	    for line in ip:
               if ipv4_pkt and (ipv4_pkt.src == ip or ipv4_pkt.dst == ip):
            	default_match_1 = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_src=ipv4_pkt.src,
                ipv4_dst=ipv4_pkt.dst
            )
            
            default_match_2 = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_src=ipv4_pkt.dst,
                ipv4_dst=ipv4_pkt.src
            )

            self.add_flow(datapath, 5, default_match_1, [])
            self.add_flow(datapath, 4, default_match_2, [])

            self.logger.info("packet drop %s %s %s", dpid, ipv4_pkt.src, ipv4_pkt.dst)
        elif out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)