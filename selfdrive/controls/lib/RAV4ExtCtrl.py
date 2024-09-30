import numpy as np
from numbers import Number

DT_CTRL = 0.01

################################ Some util functions #########################################
def clip(x, lo, hi):
  return max(lo, min(hi, x))

def interp(x, xp, fp):
  N = len(xp)

  def get_interp(xv):
    hi = 0
    while hi < N and xv > xp[hi]:
      hi += 1
    low = hi - 1
    return fp[-1] if hi == N and xv > xp[low] else (
      fp[0] if hi == 0 else
      (xv - xp[low]) * (fp[hi] - fp[low]) / (xp[hi] - xp[low]) + fp[low])

  return [get_interp(v) for v in x] if hasattr(x, '__iter__') else get_interp(x)

def mean(x):
  return sum(x) / len(x)


################################ Longitudinal Control Params #########################################
class CP:
    def __init__(self, DT_CTRL):
        self.longitudinalTuning_kpBP = [0.0]
        self.longitudinalTuning_kpV = [0.0]
        self.longitudinalTuning_kiBP = [0., 5., 35.]
        self.longitudinalTuning_kiV = [3.6, 2.4, 1.5]
        self.longitudinalTuning_kf = 1.
        self.rate = 1 / DT_CTRL

        self.ACEEL_MAX = 2
        self.ACCEL_MIN = -4

################################ Longitudinal PID Controller #########################################
class PIDController:
  def __init__(self, k_p, k_i, k_f=0., k_d=0., pos_limit=1e308, neg_limit=-1e308, rate=100):
    self._k_p = k_p
    self._k_i = k_i
    self._k_d = k_d
    self.k_f = k_f   # feedforward gain
    if isinstance(self._k_p, Number):
      self._k_p = [[0], [self._k_p]]
    if isinstance(self._k_i, Number):
      self._k_i = [[0], [self._k_i]]
    if isinstance(self._k_d, Number):
      self._k_d = [[0], [self._k_d]]

    self.pos_limit = pos_limit
    self.neg_limit = neg_limit

    self.i_unwind_rate = 0.3 / rate
    self.i_rate = 1.0 / rate
    self.speed = 0.0

    self.reset()

  @property
  def k_p(self):
    return interp(self.speed, self._k_p[0], self._k_p[1])

  @property
  def k_i(self):
    return interp(self.speed, self._k_i[0], self._k_i[1])

  @property
  def k_d(self):
    return interp(self.speed, self._k_d[0], self._k_d[1])

  @property
  def error_integral(self):
    return self.i/self.k_i

  def reset(self):
    self.p = 0.0
    self.i = 0.0
    self.d = 0.0
    self.f = 0.0
    self.control = 0

  def update(self, error, error_rate=0.0, speed=0.0, override=False, feedforward=0., freeze_integrator=False):
    self.speed = speed

    self.p = float(error) * self.k_p
    self.f = feedforward * self.k_f
    self.d = error_rate * self.k_d

    if override:
      self.i -= self.i_unwind_rate * float(np.sign(self.i))
    else:
      i = self.i + error * self.k_i * self.i_rate
      control = self.p + i + self.d + self.f

      # Update when changing i will move the control away from the limits
      # or when i will move towards the sign of the error
      if ((error >= 0 and (control <= self.pos_limit or i < 0.0)) or
          (error <= 0 and (control >= self.neg_limit or i > 0.0))) and \
         not freeze_integrator:
        self.i = i

    control = self.p + self.i + self.d + self.f

    self.control = clip(control, self.neg_limit, self.pos_limit)
    return self.control

################################ The control process to get acceleration command #########################################
class LongControl:
  def __init__(self, CP):
    self.CP = CP(DT_CTRL)
    self.pid = PIDController((self.CP.longitudinalTuning_kpBP, self.CP.longitudinalTuning_kpV),
                             (self.CP.longitudinalTuning_kiBP, self.CP.longitudinalTuning_kiV),
                             k_f=self.CP.longitudinalTuning_kf, rate=self.CP.rate)
    self.last_output_accel = 0.0

  def reset(self):
    self.pid.reset()

  def update(self, active, vEgo, aEgo, a_target):
    """Update longitudinal control. This updates the state machine and runs a PID loop"""
    self.pid.neg_limit = self.CP.ACCEL_MIN
    self.pid.pos_limit = self.CP.ACCEL_MAX

    error = a_target - aEgo
    output_accel = self.pid.update(error, speed=vEgo, feedforward=a_target)

    self.last_output_accel = clip(output_accel, self.pid.neg_limit, self.pid.pos_limit)
    return self.last_output_accel

################################ A gas/brake function derived from Honda to compuate gas/brake using acceleration command #########################################
def compute_gb(accel, speed):
  creep_brake = 0.0
  creep_speed = 2.3
  creep_brake_value = 0.15
  if speed < creep_speed:
    creep_brake = (creep_speed - speed) / creep_speed * creep_brake_value
  gb = float(accel) / 4.8 - creep_brake
  return clip(gb, 0.0, 1.0), clip(-gb, 0.0, 1.0)