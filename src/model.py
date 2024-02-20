import numpy as np
# from numba import jit # removed, couldn't figure out how to implement with class

# Using the odeint routine
from odeintw import odeintw


class ThermalState:

    def __init__(self, Ta, Tset, Tstart):

        t_length = 25
        t_steps = 25
        self.t_vec = np.linspace(0, t_length, t_steps)

        # Initial conditions
        nb_of_states = 2
        temp_states = 50

        x_0 = np.zeros((temp_states, nb_of_states, nb_of_states,))
        x_0[Tstart] = .25 # uniform distribution

        # Tset = 20
        self.Ph = []
        self.Pc = []
        for i in range(temp_states):
            x = self.tProb(i, Tset, -2, .8)
            self.Pc.append(x)
            self.Ph.append(1 - x)

        self.Ta = Ta
        self.x_0 = x_0

    # Probabilities for heating and cooling based on Ti
    def tProb(self,x,mu,lag,slope=.25):
        y = 1/(1+np.e**-(slope*(x-mu-lag)))
        return y

    # Efficiency curves - based on technology & Ta
    def hEfficiency(self):
        eff = -.05*np.e**(-.2*self.Ta)+1
        return eff

    def fEfficiency(self):
        eff = 0.9 + 1/1000 * self.Ta
        return eff


    # Master Equations with Temperature
    # @jit(nopython=True)
    def J3(self, x):
        """
        Time derivative of the occupation numbers.

            * x is the state distribution (array like)
            * alpha - transition b/t p[00] and p[01]
            * phi - transition b/t p[00] and p[01]
            * gamma - transition b/t p[00] and p[01]
            * beta - transition b/t p[00] and p[01]
            * L - loss from no heat
            * F - heating for fossil
            * H - heating for heat pump
            * omega - heating for both
            * Tset - desired setpoint inside
            * Ta - ambient temperature (outside)
        """
        # Functions
        h_eff = self.hEfficiency()
        f_eff = self.fEfficiency()

        # Parameters
        alpha_p = .126
        alpha_m = .13
        phi_p = .874
        phi_m = .13
        gamma_p = .87
        gamma_m = .874
        beta_p = .87
        beta_m = .126

        # Temp Transitions
        L = .8
        F = .5
        H = .3
        omega = .8

        K = x.shape[0]

        dx = 0 * x
        for Ti, h, f in np.ndindex(x.shape):

            Cadj = self.Pc[Ti]  # setpoint range for cooling
            Hadj = self.Ph[Ti]  # setpoint range for heating

            # Teff = # heating becomes less efficient at colder temperatures

            if h == 0 and f == 0:  # all off p[0,0]
                dx[Ti, h, f] -= x[Ti, h, f] * alpha_p * Hadj  # f on
                dx[Ti, h, f] += x[Ti, h, f + 1] * alpha_m * Cadj  # f off
                dx[Ti, h, f] -= x[Ti, h, f] * phi_p * Hadj  # h on
                dx[Ti, h, f] += x[Ti, h + 1, f] * phi_m * Cadj  # h off

                if Ti < x.shape[0] - 1:
                    dx[Ti, h, f] += x[Ti + 1, h, f] * L  # cooling off from above
                if Ti > 0:
                    dx[Ti, h, f] -= x[Ti, h, f] * L  # cooling off to Ti-1

            if h == 1 and f == 0:  # hp on p[1,0]
                dx[Ti, h, f] -= x[Ti, h, f] * gamma_p * Hadj
                dx[Ti, h, f] += x[Ti, h, f + 1] * gamma_m * Cadj
                dx[Ti, h, f] -= x[Ti, h, f] * phi_m * Cadj
                dx[Ti, h, f] += x[Ti, h - 1, f] * phi_p * Hadj

                if Ti < x.shape[0] - 1:
                    dx[Ti, h, f] -= x[Ti, h, f] * H * h_eff  # leaving to hotter state
                if Ti > 0:
                    dx[Ti, h, f] += x[Ti - 1, h, f] * H * h_eff  # entering from cooler state

            if h == 0 and f == 1:  # f on p[0,1]
                dx[Ti, h, f] -= x[Ti, h, f] * beta_p * Hadj
                dx[Ti, h, f] += x[Ti, h + 1, f] * beta_m * Cadj
                dx[Ti, h, f] -= x[Ti, h, f] * alpha_m * Cadj
                dx[Ti, h, f] += x[Ti, h, f - 1] * alpha_p * Hadj

                if Ti < x.shape[0] - 1:
                    dx[Ti, h, f] -= x[Ti, h, f] * F * f_eff  # leaving to hotter state
                if Ti > 0:
                    dx[Ti, h, f] += x[Ti - 1, h, f] * F * f_eff  # entering from cooler state

            if h == 1 and f == 1:  # all on h[1,1]
                dx[Ti, h, f] -= x[Ti, h, f] * gamma_m * Cadj
                dx[Ti, h, f] += x[Ti, h, f - 1] * gamma_p * Hadj
                dx[Ti, h, f] -= x[Ti, h, f] * beta_m * Cadj
                dx[Ti, h, f] += x[Ti, h - 1, f] * beta_p * Hadj

                if Ti < x.shape[0] - 1:
                    dx[Ti, h, f] -= x[Ti, h, f] * omega  # leaving to hotter state
                if Ti > 0:
                    dx[Ti, h, f] += x[Ti - 1, h, f] * omega  # entering from cooler state

        return dx

    def runIt(self):

        G = lambda x, t: self.J3(x)
        x_path = odeintw(G, self.x_0, self.t_vec)

        return x_path
