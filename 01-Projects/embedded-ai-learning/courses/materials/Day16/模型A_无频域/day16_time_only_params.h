#ifndef DAY16_TIME_ONLY_PARAMS_H
#define DAY16_TIME_ONLY_PARAMS_H

#include <stdint.h>

/*
 * Generated deployment parameters for time_only.
 * Feature order is part of the model ABI and must not be changed.
 * 00: lin_norm__mean
 * 01: lin_norm__std
 * 02: lin_norm__rms
 * 03: lin_norm__min
 * 04: lin_norm__max
 * 05: lin_norm__peak_to_peak
 * 06: lin_norm__mean_abs
 * 07: lin_norm__mean_abs_diff
 * 08: gyro_norm__max
 * 09: gyro_norm__peak_to_peak
 * 10: gyro_norm__mean_abs_diff
 * 11: acc_norm_centered__mean
 * 12: acc_norm_centered__std
 * 13: acc_norm_centered__rms
 * 14: acc_norm_centered__min
 * 15: acc_norm_centered__max
 * 16: acc_norm_centered__peak_to_peak
 * 17: acc_norm_centered__mean_abs
 * 18: acc_norm_centered__mean_abs_diff
 * 19: lin_delta_norm__mean
 * 20: lin_delta_norm__std
 * 21: lin_delta_norm__rms
 * 22: lin_delta_norm__min
 * 23: lin_delta_norm__max
 * 24: lin_delta_norm__peak_to_peak
 * 25: lin_delta_norm__mean_abs
 * 26: lin_delta_norm__mean_abs_diff
 * 27: lin_delta_norm__zero_crossing_rate
 * 28: gyro_delta_norm__mean
 * 29: gyro_delta_norm__std
 * 30: gyro_delta_norm__rms
 * 31: gyro_delta_norm__min
 * 32: gyro_delta_norm__max
 * 33: gyro_delta_norm__peak_to_peak
 * 34: gyro_delta_norm__mean_abs
 * 35: gyro_delta_norm__mean_abs_diff
 * 36: lin_covariance_eigenvalue_0
 * 37: lin_covariance_eigenvalue_1
 * 38: gyro_covariance_eigenvalue_1
 * 39: gyro_covariance_eigenvalue_2
 */

#define DAY16_TIME_ONLY_SAMPLE_RATE_HZ       (40.0f)
#define DAY16_TIME_ONLY_SAMPLE_PERIOD_MS     (25U)
#define DAY16_TIME_ONLY_WINDOW_SAMPLES       (64U)
#define DAY16_TIME_ONLY_HOP_SAMPLES          (16U)
#define DAY16_TIME_ONLY_FEATURE_COUNT        (40U)
#define DAY16_TIME_ONLY_CLASS_COUNT          (3U)
#define DAY16_TIME_ONLY_INPUT_SCALE          (4.235143587e-02f)
#define DAY16_TIME_ONLY_INPUT_ZERO_POINT     (-3)
#define DAY16_TIME_ONLY_OUTPUT_SCALE         (3.906250000e-03f)
#define DAY16_TIME_ONLY_OUTPUT_ZERO_POINT    (-128)

static const char *const day16_time_only_labels[3] = {
  "idle", "walk", "stairs"
};

static const float day16_time_only_clip_low[40] = {
  2.695522960e-03f, 1.098801241e-03f, 3.017575890e-03f, 0.000000000e+00f, 5.271455999e-03f, 4.328295141e-03f,
  2.695522960e-03f, 3.831183753e-04f, 4.259503286e-02f, 1.109894904e-02f, 9.506437101e-04f, -7.475260645e-03f,
  1.046940295e-04f, 1.653640730e-03f, -3.737036884e-02f, -3.000000026e-03f, 7.261384733e-04f, 1.591612007e-03f,
  2.589938995e-05f, 6.521140365e-04f, 4.013141495e-04f, 8.082014229e-04f, 0.000000000e+00f, 1.663730713e-03f,
  1.663730713e-03f, 6.521140365e-04f, 3.734025033e-04f, 1.269841343e-01f, 2.869182928e-03f, 1.180912426e-03f,
  3.093394157e-03f, 6.661733642e-05f, 5.821663113e-03f, 5.054274234e-03f, 2.869182928e-03f, 9.472985961e-04f,
  4.281354372e-06f, 6.498751713e-07f, 1.794519618e-05f, 4.471055195e-06f
};

static const float day16_time_only_clip_high[40] = {
  1.019162610e-01f, 4.925252870e-02f, 1.088132608e-01f, 3.648287430e-02f, 2.069981843e-01f, 1.988175511e-01f,
  1.019162610e-01f, 1.850807913e-02f, 1.894640565e+00f, 1.600155232e+00f, 6.124252994e-02f, -1.591612007e-03f,
  7.498329505e-03f, 1.082771271e-02f, -2.000000095e-03f, -1.000000047e-03f, 3.503703699e-02f, 7.475260645e-03f,
  1.540858299e-03f, 2.502680326e-02f, 1.938645355e-02f, 2.952194586e-02f, 5.875249947e-03f, 1.314553469e-01f,
  1.308524311e-01f, 2.502680326e-02f, 1.089911163e-02f, 5.714285970e-01f, 1.185029596e-01f, 5.099847913e-02f,
  1.284386367e-01f, 3.690989491e-02f, 3.015856147e-01f, 2.783333659e-01f, 1.185029596e-01f, 2.878416330e-02f,
  8.921160316e-03f, 3.763953017e-03f, 7.546876952e-02f, 2.983076312e-02f
};

static const float day16_time_only_mean[40] = {
  5.513226136e-02f, 2.596279826e-02f, 6.105754524e-02f, 9.225854325e-03f, 1.144573835e-01f, 1.052190574e-01f,
  5.513226136e-02f, 9.689249286e-03f, 5.754684434e-01f, 4.757806986e-01f, 2.560712953e-02f, -3.793730279e-03f,
  1.779576627e-03f, 4.229147069e-03f, -8.721551431e-03f, -1.563263484e-03f, 7.159096973e-03f, 3.793730279e-03f,
  5.075991381e-04f, 1.408569534e-02f, 8.358305170e-03f, 1.640538084e-02f, 1.641142377e-03f, 3.816054837e-02f,
  3.651435170e-02f, 1.408569534e-02f, 4.996616672e-03f, 2.721709288e-01f, 5.216133565e-02f, 2.353924826e-02f,
  5.735871094e-02f, 1.158084835e-02f, 1.146094291e-01f, 1.030102063e-01f, 5.216133565e-02f, 1.246188156e-02f,
  3.011583596e-03f, 1.300389895e-03f, 1.812222044e-02f, 6.558958297e-03f
};

static const float day16_time_only_std[40] = {
  2.890917268e-02f, 1.399088865e-02f, 3.187160811e-02f, 6.904975562e-03f, 6.151427301e-02f, 5.752124805e-02f,
  2.890917268e-02f, 5.618494243e-03f, 4.611812440e-01f, 3.826309329e-01f, 1.550127320e-02f, 1.511920656e-03f,
  1.144116192e-03f, 1.816496598e-03f, 5.398646113e-03f, 6.123075052e-04f, 5.075222306e-03f, 1.511920656e-03f,
  2.829700856e-04f, 7.917543509e-03f, 4.782515086e-03f, 9.193537565e-03f, 1.360931706e-03f, 2.344887025e-02f,
  2.265817858e-02f, 7.917543509e-03f, 2.808508666e-03f, 9.334702474e-02f, 3.022643014e-02f, 1.367315706e-02f,
  3.298188654e-02f, 8.654399280e-03f, 6.596059573e-02f, 5.992155009e-02f, 3.022643014e-02f, 7.220979492e-03f,
  2.038959124e-03f, 9.235270457e-04f, 1.514744653e-02f, 6.042392428e-03f
};

static inline int8_t day16_time_only_quantize_input(float value)
{
  float qf = value / DAY16_TIME_ONLY_INPUT_SCALE
             + (float)DAY16_TIME_ONLY_INPUT_ZERO_POINT;
  int32_t quantized = (int32_t)(qf + (qf >= 0.0f ? 0.5f : -0.5f));
  if (quantized > 127) quantized = 127;
  if (quantized < -128) quantized = -128;
  return (int8_t)quantized;
}

static inline float day16_time_only_dequantize_output(int8_t value)
{
  return ((float)value - (float)DAY16_TIME_ONLY_OUTPUT_ZERO_POINT)
         * DAY16_TIME_ONLY_OUTPUT_SCALE;
}

#endif
