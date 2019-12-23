"""
=========================================================================
Tile.py
=========================================================================

Author : Cheng Tan
  Date : Dec 11, 2019
"""

from pymtl3             import *
from pymtl3.stdlib.ifcs import SendIfcRTL, RecvIfcRTL
from ..noc.Crossbar     import Crossbar
from ..noc.Channel      import Channel

from ..mem.ctrl.CtrlMem import CtrlMem

class Tile( Component ):

  def construct( s, Fu, DataType, CtrlType, RoutingTableType,
                 ctrl_mem_size, num_ctrl ):

    # Constant

    num_xbar_inports  = 6
    num_xbar_outports = 8
    num_fu_inports    = 4
    num_fu_outports   = 2
    num_mesh_ports    = 4

    AddrType = mk_bits( clog2( ctrl_mem_size ) )

    # Interfaces

    s.recv_routing = RecvIfcRTL( RoutingTableType )
    s.recv_data    = [ RecvIfcRTL( DataType ) for _ in range ( num_mesh_ports ) ]
    s.send_data    = [ SendIfcRTL( DataType ) for _ in range ( num_mesh_ports ) ]

    s.recv_waddr = RecvIfcRTL( AddrType )
    s.recv_wopt  = RecvIfcRTL( CtrlType )

    # Components

    s.element  = Fu( DataType, CtrlType )
    s.crossbar = Crossbar( DataType, RoutingTableType,
                           num_xbar_inports, num_xbar_outports )
    s.ctrl_mem = CtrlMem( CtrlType, ctrl_mem_size, num_ctrl )
    s.channel  = [ Channel ( DataType ) for _ in range( num_xbar_outports ) ]

    # Connections

    s.ctrl_mem.recv_waddr //= s.recv_waddr
    s.ctrl_mem.recv_ctrl  //= s.recv_wopt 

    s.recv_routing        //= s.crossbar.recv_routing
    s.element.recv_opt    //=  s.ctrl_mem.send_ctrl

    for i in range( num_mesh_ports  ):
      s.recv_data[i] //= s.crossbar.recv_data[i]

    for i in range( num_xbar_outports ):
      s.crossbar.send_data[i] //= s.channel[i].recv

    for i in range( num_mesh_ports ):
      s.channel[i].send //= s.send_data[i]

    s.channel[num_mesh_ports+0].send //= s.element.recv_in0
    s.channel[num_mesh_ports+1].send //= s.element.recv_in1
    s.channel[num_mesh_ports+2].send //= s.element.recv_in2
    s.channel[num_mesh_ports+3].send //= s.element.recv_in3

    s.element.send_out0 //= s.crossbar.recv_data[num_mesh_ports+0]
    s.element.send_out1 //= s.crossbar.recv_data[num_mesh_ports+1]

  # Line trace
  def line_trace( s ):

    channel_str = "|".join([ str(x.msg) for x in s.recv_data ])
#    out_str = "|".join([ str(x.msg) for x in s.send_out ])
    out_str  = "|".join([ x.line_trace() for x in s.send_data ])
    return f"{channel_str} => [{s.crossbar.recv_routing.msg}] ({s.element.line_trace()}) => {out_str}"
