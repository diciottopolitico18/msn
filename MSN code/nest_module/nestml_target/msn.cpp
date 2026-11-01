#define DEBUG 1
/*
 *  msn.cpp
 *
 *  This file is part of NEST.
 *
 *  Copyright (C) 2004 The NEST Initiative
 *
 *  NEST is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  NEST is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with NEST.  If not, see <http://www.gnu.org/licenses/>.
 *
 *  Generated from NESTML at time: 2022-05-15 09:39:21.684610
**/

// C++ includes:
#include <limits>

// Includes from libnestutil:
#include "numerics.h"

// Includes from nestkernel:
#include "exceptions.h"
#include "kernel_manager.h"
#include "universal_data_logger_impl.h"

// Includes from sli:
#include "dict.h"
#include "dictutils.h"
#include "doubledatum.h"
#include "integerdatum.h"
#include "lockptrdatum.h"

#include "msn.h"

// ---------------------------------------------------------------------------
//   Recordables map
// ---------------------------------------------------------------------------
nest::RecordablesMap<msn> msn::recordablesMap_;
namespace nest
{

  // Override the create() method with one call to RecordablesMap::insert_()
  // for each quantity to be recorded.
template <> void RecordablesMap<msn>::create()
  {
    // add state variables to recordables map
   insert_(msn_names::_V_m, &msn::get_V_m);
   insert_(msn_names::_U_m, &msn::get_U_m);
   insert_(msn_names::_I, &msn::get_I);
   insert_(msn_names::_dop, &msn::get_dop);
   insert_(msn_names::_kernel_ampa__X__spikes_ampa, &msn::get_kernel_ampa__X__spikes_ampa);
   insert_(msn_names::_kernel_nmda__X__spikes_nmda, &msn::get_kernel_nmda__X__spikes_nmda);
   insert_(msn_names::_kernel_gaba__X__spikes_gaba, &msn::get_kernel_gaba__X__spikes_gaba);

    // Add vector variables  
  }
}

// ---------------------------------------------------------------------------
//   Default constructors defining default parameters and state
//   Note: the implementation is empty. The initialization is of variables
//   is a part of msn's constructor.
// ---------------------------------------------------------------------------

msn::Parameters_::Parameters_()
{
}

msn::State_::State_()
{
}

// ---------------------------------------------------------------------------
//   Parameter and state extractions and manipulation functions
// ---------------------------------------------------------------------------

msn::Buffers_::Buffers_(msn &n):
  logger_(n)
  , spike_inputs_( std::vector< nest::RingBuffer >( SUP_SPIKE_RECEPTOR - 1 ) )
  , __s( 0 ), __c( 0 ), __e( 0 )
{
  // Initialization of the remaining members is deferred to init_buffers_().
}

msn::Buffers_::Buffers_(const Buffers_ &, msn &n):
  logger_(n)
  , spike_inputs_( std::vector< nest::RingBuffer >( SUP_SPIKE_RECEPTOR - 1 ) )
  , __s( 0 ), __c( 0 ), __e( 0 )
{
  // Initialization of the remaining members is deferred to init_buffers_().
}

// ---------------------------------------------------------------------------
//   Default constructor for node
// ---------------------------------------------------------------------------

msn::msn():ArchivingNode(), P_(), S_(), B_(*this)
{
  const double __resolution = nest::Time::get_resolution().get_ms();  // do not remove, this is necessary for the resolution() function

  calibrate();

  // use a default "good enough" value for the absolute error. It can be adjusted via `node.set()`
  P_.__gsl_error_tol = 1e-3;
  // initial values for parameters
    
    P_.a = 0.03; // as real
    
    P_.b = (-(2.0)); // as real
    
    P_.c = (-(50)); // as mV
    
    P_.d = 100; // as real
    
    P_.I_e = 0; // as pA
    
    P_.V_th = 35; // as mV
    
    P_.V_min = (-(std::numeric_limits<double_t>::infinity())) * 1.0; // as mV
    
    P_.Kplus = 0.7; // as real
    
    P_.vp = (-(60.0)); // as mV
    
    P_.V_T = (-(40.0)); // as mV
    
    P_.C_m = 100.0; // as pF
    
    P_.c_1 = 0.0289; // as real
    
    P_.c_2 = 0.331; // as real
    
    P_.y1 = 0.3; // as real
    
    P_.y2 = 0.3; // as real
    
    P_.alpha_1 = 0.5; // as real
    
    P_.alpha_2 = 0.5; // as real
    
    P_.alpha = 0.032; // as real
    
    P_.tau_decay_AMPA = 2.0; // as ms
    
    P_.tau_decay_GABA_A = 2.0; // as ms
    
    P_.tau_decay_NMDA = 2.0; // as ms
    
    P_.E_rev_AMPA = 0.0; // as real
    
    P_.E_rev_GABA_A = 0.0; // as real
    
    P_.E_rev_NMDA = 0.0; // as real
  // initial values for state variables
    
    S_.ode_state[State_::V_m] = (-(65.0)); // as mV
    
    S_.ode_state[State_::U_m] = 0.0; // as real
    
    S_.ode_state[State_::I] = 0.0; // as pA
    
    S_.ode_state[State_::dop] = 0.0; // as real
    
    S_.ode_state[State_::kernel_ampa__X__spikes_ampa] = 0; // as real
    
    S_.ode_state[State_::kernel_nmda__X__spikes_nmda] = 0; // as real
    
    S_.ode_state[State_::kernel_gaba__X__spikes_gaba] = 0; // as real
  recordablesMap_.create();
}

// ---------------------------------------------------------------------------
//   Copy constructor for node
// ---------------------------------------------------------------------------

msn::msn(const msn& __n):
  ArchivingNode(), P_(__n.P_), S_(__n.S_), B_(__n.B_, *this) {

  // copy parameter struct P_
  P_.a = __n.P_.a;
  P_.b = __n.P_.b;
  P_.c = __n.P_.c;
  P_.d = __n.P_.d;
  P_.I_e = __n.P_.I_e;
  P_.V_th = __n.P_.V_th;
  P_.V_min = __n.P_.V_min;
  P_.Kplus = __n.P_.Kplus;
  P_.vp = __n.P_.vp;
  P_.V_T = __n.P_.V_T;
  P_.C_m = __n.P_.C_m;
  P_.c_1 = __n.P_.c_1;
  P_.c_2 = __n.P_.c_2;
  P_.y1 = __n.P_.y1;
  P_.y2 = __n.P_.y2;
  P_.alpha_1 = __n.P_.alpha_1;
  P_.alpha_2 = __n.P_.alpha_2;
  P_.alpha = __n.P_.alpha;
  P_.tau_decay_AMPA = __n.P_.tau_decay_AMPA;
  P_.tau_decay_GABA_A = __n.P_.tau_decay_GABA_A;
  P_.tau_decay_NMDA = __n.P_.tau_decay_NMDA;
  P_.E_rev_AMPA = __n.P_.E_rev_AMPA;
  P_.E_rev_GABA_A = __n.P_.E_rev_GABA_A;
  P_.E_rev_NMDA = __n.P_.E_rev_NMDA;

  // copy state struct S_
  S_.ode_state[State_::V_m] = __n.S_.ode_state[State_::V_m];
  S_.ode_state[State_::U_m] = __n.S_.ode_state[State_::U_m];
  S_.ode_state[State_::I] = __n.S_.ode_state[State_::I];
  S_.ode_state[State_::dop] = __n.S_.ode_state[State_::dop];
  S_.ode_state[State_::kernel_ampa__X__spikes_ampa] = __n.S_.ode_state[State_::kernel_ampa__X__spikes_ampa];
  S_.ode_state[State_::kernel_nmda__X__spikes_nmda] = __n.S_.ode_state[State_::kernel_nmda__X__spikes_nmda];
  S_.ode_state[State_::kernel_gaba__X__spikes_gaba] = __n.S_.ode_state[State_::kernel_gaba__X__spikes_gaba];


  // copy internals V_
  V_.__h = __n.V_.__h;
  V_.__P__kernel_ampa__X__spikes_ampa__kernel_ampa__X__spikes_ampa = __n.V_.__P__kernel_ampa__X__spikes_ampa__kernel_ampa__X__spikes_ampa;
  V_.__P__kernel_nmda__X__spikes_nmda__kernel_nmda__X__spikes_nmda = __n.V_.__P__kernel_nmda__X__spikes_nmda__kernel_nmda__X__spikes_nmda;
  V_.__P__kernel_gaba__X__spikes_gaba__kernel_gaba__X__spikes_gaba = __n.V_.__P__kernel_gaba__X__spikes_gaba__kernel_gaba__X__spikes_gaba;
}

// ---------------------------------------------------------------------------
//   Destructor for node
// ---------------------------------------------------------------------------

msn::~msn()
{
  // GSL structs may not have been allocated, so we need to protect destruction

  if (B_.__s)
  {
    gsl_odeiv_step_free( B_.__s );
  }

  if (B_.__c)
  {
    gsl_odeiv_control_free( B_.__c );
  }

  if (B_.__e)
  {
    gsl_odeiv_evolve_free( B_.__e );
  }
}

// ---------------------------------------------------------------------------
//   Node initialization functions
// ---------------------------------------------------------------------------

#if NEST2_COMPAT
void msn::init_state_(const Node& proto)
{
  const msn& pr = downcast<msn>(proto);
  S_ = pr.S_;
}
#endif

void msn::init_buffers_()
{
  get_spikes_ampa().clear(); //includes resize
  get_spikes_nmda().clear(); //includes resize
  get_spikes_gaba().clear(); //includes resize
  get_I_stim().clear(); //includes resize
  B_.logger_.reset(); // includes resize

  if ( B_.__s == 0 )
  {
    B_.__s = gsl_odeiv_step_alloc( gsl_odeiv_step_rkf45, 7 );
  }
  else
  {
    gsl_odeiv_step_reset( B_.__s );
  }

  if ( B_.__c == 0 )
  {
    B_.__c = gsl_odeiv_control_y_new( P_.__gsl_error_tol, 0.0 );
  }
  else
  {
    gsl_odeiv_control_init( B_.__c, P_.__gsl_error_tol, 0.0, 1.0, 0.0 );
  }

  if ( B_.__e == 0 )
  {
    B_.__e = gsl_odeiv_evolve_alloc( 7 );
  }
  else
  {
    gsl_odeiv_evolve_reset( B_.__e );
  }

  B_.__sys.function = msn_dynamics;
  B_.__sys.jacobian = NULL;
  B_.__sys.dimension = 7;
  B_.__sys.params = reinterpret_cast< void* >( this );
  B_.__step = nest::Time::get_resolution().get_ms();
  B_.__integration_step = nest::Time::get_resolution().get_ms();
}

void msn::calibrate_variables(bool exclude_timestep) {
  const double __resolution = nest::Time::get_resolution().get_ms();  // do not remove, this is necessary for the resolution() function

  if (exclude_timestep) {    
    V_.__P__kernel_ampa__X__spikes_ampa__kernel_ampa__X__spikes_ampa =std::exp((-(V_.__h)) / P_.tau_decay_AMPA);
    V_.__P__kernel_nmda__X__spikes_nmda__kernel_nmda__X__spikes_nmda =std::exp((-(V_.__h)) / P_.tau_decay_NMDA);
    V_.__P__kernel_gaba__X__spikes_gaba__kernel_gaba__X__spikes_gaba =std::exp((-(V_.__h)) / P_.tau_decay_GABA_A);
  }
  else {
    // internals V_
    V_.__h =__resolution;
    V_.__P__kernel_ampa__X__spikes_ampa__kernel_ampa__X__spikes_ampa =std::exp((-(V_.__h)) / P_.tau_decay_AMPA);
    V_.__P__kernel_nmda__X__spikes_nmda__kernel_nmda__X__spikes_nmda =std::exp((-(V_.__h)) / P_.tau_decay_NMDA);
    V_.__P__kernel_gaba__X__spikes_gaba__kernel_gaba__X__spikes_gaba =std::exp((-(V_.__h)) / P_.tau_decay_GABA_A);
  }
}

void msn::calibrate() {
  B_.logger_.init();

  calibrate_variables();

  // buffers B_
}

// ---------------------------------------------------------------------------
//   Update and spike handling functions
// ---------------------------------------------------------------------------

extern "C" inline int msn_dynamics(double, const double ode_state[], double f[], void* pnode)
{
  typedef msn::State_ State_;
  // get access to node so we can almost work as in a member function
  assert( pnode );
  const msn& node = *( reinterpret_cast< msn* >( pnode ) );

  // ode_state[] here is---and must be---the state vector supplied by the integrator,
  // not the state vector in the node, node.S_.ode_state[].
  f[State_::V_m] = (-(1.0)) * node.get_E_rev_AMPA() * node.get_alpha_2() * ode_state[State_::kernel_ampa__X__spikes_ampa] * node.get_y2() * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 0.28 * node.get_E_rev_AMPA() * node.get_alpha_2() * ode_state[State_::kernel_ampa__X__spikes_ampa] * node.get_y2() / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + 1.0 * node.get_E_rev_AMPA() * ode_state[State_::kernel_ampa__X__spikes_ampa] * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + 0.28 * node.get_E_rev_AMPA() * ode_state[State_::kernel_ampa__X__spikes_ampa] / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + 1.0 * node.get_E_rev_GABA_A() * ode_state[State_::kernel_gaba__X__spikes_gaba] * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + 0.28 * node.get_E_rev_GABA_A() * ode_state[State_::kernel_gaba__X__spikes_gaba] / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + 1.0 * node.get_E_rev_NMDA() * node.get_alpha_1() * ode_state[State_::kernel_nmda__X__spikes_nmda] * node.get_y1() * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + 1.0 * node.get_E_rev_NMDA() * ode_state[State_::kernel_nmda__X__spikes_nmda] * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 1.0 * node.get_Kplus() * pow(ode_state[State_::V_m], 2) * node.get_alpha() * node.get_y2() * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 0.28 * node.get_Kplus() * pow(ode_state[State_::V_m], 2) * node.get_alpha() * node.get_y2() / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + 1.0 * node.get_Kplus() * pow(ode_state[State_::V_m], 2) * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + 0.28 * node.get_Kplus() * pow(ode_state[State_::V_m], 2) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 1.0 * ode_state[State_::U_m] * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 0.28 * ode_state[State_::U_m] / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 1.0 * ode_state[State_::V_m] * node.get_alpha_1() * ode_state[State_::kernel_nmda__X__spikes_nmda] * node.get_y1() * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + 1.0 * ode_state[State_::V_m] * node.get_alpha_2() * ode_state[State_::kernel_ampa__X__spikes_ampa] * node.get_y2() * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + 0.28 * ode_state[State_::V_m] * node.get_alpha_2() * ode_state[State_::kernel_ampa__X__spikes_ampa] * node.get_y2() / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 1.0 * ode_state[State_::V_m] * ode_state[State_::kernel_ampa__X__spikes_ampa] * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 0.28 * ode_state[State_::V_m] * ode_state[State_::kernel_ampa__X__spikes_ampa] / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 1.0 * ode_state[State_::V_m] * ode_state[State_::kernel_gaba__X__spikes_gaba] * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 0.28 * ode_state[State_::V_m] * ode_state[State_::kernel_gaba__X__spikes_gaba] / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) - 1.0 * ode_state[State_::V_m] * ode_state[State_::kernel_nmda__X__spikes_nmda] * std::exp(0.062 * ode_state[State_::V_m]) / (1.0 * node.get_C_m() * std::exp(0.062 * ode_state[State_::V_m]) + 0.28 * node.get_C_m()) + ode_state[State_::V_m] * (1.0 * node.get_Kplus() * node.get_V_T() * node.get_alpha() * node.get_y2() / node.get_C_m() - 1.0 * node.get_Kplus() * node.get_V_T() / node.get_C_m() + 1.0 * node.get_Kplus() * node.get_alpha() * node.get_c_1() * node.get_vp() * node.get_y1() * node.get_y2() / node.get_C_m() + 1.0 * node.get_Kplus() * node.get_alpha() * node.get_vp() * node.get_y2() / node.get_C_m() - 1.0 * node.get_Kplus() * node.get_c_1() * node.get_vp() * node.get_y1() / node.get_C_m() - 1.0 * node.get_Kplus() * node.get_vp() / node.get_C_m()) + 1.0 * ode_state[State_::I] / node.get_C_m() + 1.0 * node.get_I_e() / node.get_C_m() - 1.0 * node.get_Kplus() * node.get_V_T() * node.get_alpha() * node.get_c_1() * node.get_vp() * node.get_y1() * node.get_y2() / node.get_C_m() - 1.0 * node.get_Kplus() * node.get_V_T() * node.get_alpha() * node.get_vp() * node.get_y2() / node.get_C_m() + 1.0 * node.get_Kplus() * node.get_V_T() * node.get_c_1() * node.get_vp() * node.get_y1() / node.get_C_m() + 1.0 * node.get_Kplus() * node.get_V_T() * node.get_vp() / node.get_C_m();
  f[State_::U_m] = node.get_a() * ((-(1.0)) * ode_state[State_::U_m] + 1.0 * ode_state[State_::V_m] * node.get_b() - 1.0 * node.get_b() * node.get_c_1() * node.get_vp() * node.get_y1() - 1.0 * node.get_b() * node.get_vp());
  f[State_::kernel_ampa__X__spikes_ampa] = (-(ode_state[State_::kernel_ampa__X__spikes_ampa])) / node.get_tau_decay_AMPA();
  f[State_::kernel_nmda__X__spikes_nmda] = (-(ode_state[State_::kernel_nmda__X__spikes_nmda])) / node.get_tau_decay_NMDA();
  f[State_::kernel_gaba__X__spikes_gaba] = (-(ode_state[State_::kernel_gaba__X__spikes_gaba])) / node.get_tau_decay_GABA_A();
  f[State_::I] = 0.;
  f[State_::dop] = 0.;

  return GSL_SUCCESS;
}

void msn::update(nest::Time const & origin,const long from, const long to)
{
  const double __resolution = nest::Time::get_resolution().get_ms();  // do not remove, this is necessary for the resolution() function

  for ( long lag = from ; lag < to ; ++lag )
  {
    B_.spikes_ampa_grid_sum_ = get_spikes_ampa().get_value(lag);
    B_.spikes_nmda_grid_sum_ = get_spikes_nmda().get_value(lag);
    B_.spikes_gaba_grid_sum_ = get_spikes_gaba().get_value(lag);
    B_.I_stim_grid_sum_ = get_I_stim().get_value(lag);

    // NESTML generated code for the update block:
  double kernel_ampa__X__spikes_ampa__tmp = V_.__P__kernel_ampa__X__spikes_ampa__kernel_ampa__X__spikes_ampa * get_kernel_ampa__X__spikes_ampa();
  double kernel_nmda__X__spikes_nmda__tmp = V_.__P__kernel_nmda__X__spikes_nmda__kernel_nmda__X__spikes_nmda * get_kernel_nmda__X__spikes_nmda();
  double kernel_gaba__X__spikes_gaba__tmp = V_.__P__kernel_gaba__X__spikes_gaba__kernel_gaba__X__spikes_gaba * get_kernel_gaba__X__spikes_gaba();
  double __t = 0;
  // numerical integration with adaptive step size control:
  // ------------------------------------------------------
  // gsl_odeiv_evolve_apply performs only a single numerical
  // integration step, starting from t and bounded by step;
  // the while-loop ensures integration over the whole simulation
  // step (0, step] if more than one integration step is needed due
  // to a small integration step size;
  // note that (t+IntegrationStep > step) leads to integration over
  // (t, step] and afterwards setting t to step, but it does not
  // enforce setting IntegrationStep to step-t; this is of advantage
  // for a consistent and efficient integration across subsequent
  // simulation intervals
  while ( __t < B_.__step )
  {
    const int status = gsl_odeiv_evolve_apply(B_.__e,
                                              B_.__c,
                                              B_.__s,
                                              &B_.__sys,              // system of ODE
                                              &__t,                   // from t
                                              B_.__step,              // to t <= step
                                              &B_.__integration_step, // integration step size
                                              S_.ode_state);          // neuronal state

    if ( status != GSL_SUCCESS )
    {
      throw nest::GSLSolverFailure( get_name(), status );
    }
  }
  /* replace analytically solvable variables with precisely integrated values  */
  S_.ode_state[State_::kernel_ampa__X__spikes_ampa] = kernel_ampa__X__spikes_ampa__tmp;
  S_.ode_state[State_::kernel_nmda__X__spikes_nmda] = kernel_nmda__X__spikes_nmda__tmp;
  S_.ode_state[State_::kernel_gaba__X__spikes_gaba] = kernel_gaba__X__spikes_gaba__tmp;
      S_.ode_state[State_::kernel_ampa__X__spikes_ampa] += (B_.spikes_ampa_grid_sum_) / (1.0);
      S_.ode_state[State_::kernel_nmda__X__spikes_nmda] += (B_.spikes_nmda_grid_sum_) / (1.0);
      S_.ode_state[State_::kernel_gaba__X__spikes_gaba] += (B_.spikes_gaba_grid_sum_) / (1.0);
      S_.ode_state[State_::V_m] = ((get_V_m()<P_.V_min)) ? (P_.V_min) : (get_V_m());
  if (get_V_m()>=30)
  {
      S_.ode_state[State_::dop] = P_.d * (1.0 - P_.c_2 * P_.y1);
      S_.ode_state[State_::V_m] = P_.c;
      S_.ode_state[State_::U_m] += get_dop();
  set_spiketime(nest::Time::step(origin.get_steps()+lag+1));
  nest::SpikeEvent se;
  nest::kernel().event_delivery_manager.send(*this, se, lag);
  }

    // voltage logging
    B_.logger_.record_data(origin.get_steps() + lag);
  }
}

// Do not move this function as inline to h-file. It depends on
// universal_data_logger_impl.h being included here.
void msn::handle(nest::DataLoggingRequest& e)
{
  B_.logger_.handle(e);
}

void msn::handle(nest::SpikeEvent &e)
{
  assert(e.get_delay_steps() > 0);
  assert( e.get_rport() < static_cast< int >( B_.spike_inputs_.size() ) );

  B_.spike_inputs_[ e.get_rport() ].add_value(
    e.get_rel_delivery_steps( nest::kernel().simulation_manager.get_slice_origin() ),
    e.get_weight() * e.get_multiplicity() );
}

void msn::handle(nest::CurrentEvent& e)
{
  assert(e.get_delay_steps() > 0);

  const double current = e.get_current();     // we assume that in NEST, this returns a current in pA
  const double weight = e.get_weight();
  get_I_stim().add_value(
               e.get_rel_delivery_steps( nest::kernel().simulation_manager.get_slice_origin()),
               weight * current );
}
