"""
==========================================================================
Acc_test.py
==========================================================================
Test cases for HLS in terms of accelerator design.

Author : Cheng Tan
  Date : Feb 3, 2020

"""

from pymtl3 import *
from pymtl3.stdlib.test              import TestSinkCL
from pymtl3.stdlib.test.test_srcs    import TestSrcRTL

from ...lib.opt_type                 import *
from ...lib.messages                 import *
from ..Acc                           import Acc
from ...fu.single.Alu          import Alu
from ...fu.single.Mul          import Mul
from ...fu.single.MemUnit      import MemUnit

import json

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DUT, FuDFG, DataType, CtrlType, src_data, src_opt, sink_out ):

    s.src_data  = [ TestSrcRTL( DataType, src_data[i]  )
                  for i in range( 4  ) ]
    s.sink_out  = [ TestSinkCL( DataType, sink_out[i] )
                  for i in range( 1 ) ]
#    s.src_opt   = [ TestSrcRTL( CtrlType, src_opt[i]  )
#                  for i in range( 3  ) ]

    s.dut = DUT( FuDFG, DataType, CtrlType )

    for i in range( 4 ):
      connect( s.src_data[i].send, s.dut.recv_data[i] )
    for i in range( 1 ):
      connect( s.dut.send_data[i], s.sink_out[i].recv )
#    for i in range( 3 ):
#      connect( s.src_opt[i].send, s.dut.recv_opt[i] )

  def done( s ):
    done_flag = True
    for i in range(1):
      if not s.sink_out[i].done():
        done_flag = False
    return done_flag

  def line_trace( s ):
    return s.dut.line_trace()

def run_sim( test_harness, max_cycles=10 ):
  test_harness.elaborate()
  test_harness.apply( SimulationPass() )
  test_harness.sim_reset()

  # Run simulation

  ncycles = 0
  print()
  print( "{}:{}".format( ncycles, test_harness.line_trace() ))
  while not test_harness.done() and ncycles < max_cycles:
    test_harness.tick()
    ncycles += 1
    print( "{}:{}".format( ncycles, test_harness.line_trace() ))

  # Check timeout

  assert ncycles < max_cycles

  test_harness.tick()
  test_harness.tick()
  test_harness.tick()

class Element:
  def __init__( s, _id, FuType, opt, const, input, output ):
    s.id      = _id
    s.fu_type = FuType
    s.opt     = opt
    s.const   = const
    s.input   = input
    s.output  = output

class DFG:

  def __init__( s ):
    s.elements = []

  def add_element( s, element ):
    s.elements.append( element )

  def get_element( s, _id ):
    for e in s.elements:
      if e.id == _id:
        return e
    return None

def test_acc():
  fu_dfg = DFG()
  unit_map = { "ALU": Alu, "MUL": Mul }
  opt_map  = { "OPT_ADD": OPT_ADD, "OPT_SUB": OPT_SUB, "OPT_MUL": OPT_MUL }
  with open('dfg.json') as json_file:
    dfg = json.load(json_file)
    print(dfg)
    for i in range( len(dfg) ):
      e = Element( i, unit_map[dfg[i]['fu']], opt_map[dfg[i]['opt']],
                   dfg[i]['in_const'], dfg[i]['in'], dfg[i]['out'] )
      fu_dfg.add_element( e )

#  e0 = Element( 0, Alu)
#  e1 = Element( 1, Alu)
#  e2 = Element( 2, Mul)
#  fu_dfg.add_element( e0 )
#  fu_dfg.add_element( e1 )
#  fu_dfg.add_element( e2 )
#  e0.append(e2)
#  e1.append(e2)
  
  DUT      = Acc
  DataType = mk_data( 16, 1 )
  CtrlType = mk_ctrl()
  src_opt  = [[CtrlType(OPT_ADD)], [CtrlType(OPT_SUB)], [CtrlType(OPT_MUL)]]
  src_data = [ [DataType(2, 1)],
               [DataType(3, 1)],
               [DataType(4, 1)],
               [DataType(2, 1)] ]
  sink_out = [ [DataType(10, 1)] ]
  th = TestHarness( DUT, fu_dfg, DataType, CtrlType, src_data, src_opt, sink_out )
  run_sim( th )

