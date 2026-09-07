#ifndef DAY16_TIME_FREQUENCY_PARAMS_H
#define DAY16_TIME_FREQUENCY_PARAMS_H

#include <stdint.h>

/*
 * Generated deployment parameters for time_frequency.
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
 * 40: lin_norm__dominant_frequency_hz
 * 41: lin_norm__spectral_centroid_hz
 * 42: lin_norm__spectral_entropy
 * 43: lin_norm__band_energy_0p3_1p5
 * 44: lin_norm__band_energy_1p5_3p0
 * 45: lin_norm__band_energy_3p0_8p0
 * 46: lin_norm__low_high_energy_ratio
 * 47: gyro_norm__band_energy_0p3_1p5
 * 48: lin_delta_norm__dominant_frequency_hz
 * 49: lin_delta_norm__spectral_centroid_hz
 * 50: lin_delta_norm__spectral_entropy
 * 51: lin_delta_norm__band_energy_0p3_1p5
 * 52: lin_delta_norm__band_energy_1p5_3p0
 * 53: gyro_delta_norm__spectral_centroid_hz
 * 54: gyro_delta_norm__spectral_entropy
 * 55: gyro_delta_norm__band_energy_0p3_1p5
 */

#define DAY16_TIME_FREQUENCY_SAMPLE_RATE_HZ       (40.0f)
#define DAY16_TIME_FREQUENCY_SAMPLE_PERIOD_MS     (25U)
#define DAY16_TIME_FREQUENCY_WINDOW_SAMPLES       (64U)
#define DAY16_TIME_FREQUENCY_HOP_SAMPLES          (16U)
#define DAY16_TIME_FREQUENCY_FEATURE_COUNT        (56U)
#define DAY16_TIME_FREQUENCY_CLASS_COUNT          (3U)
#define DAY16_TIME_FREQUENCY_INPUT_SCALE          (4.631513730e-02f)
#define DAY16_TIME_FREQUENCY_INPUT_ZERO_POINT     (-13)
#define DAY16_TIME_FREQUENCY_OUTPUT_SCALE         (3.906250000e-03f)
#define DAY16_TIME_FREQUENCY_OUTPUT_ZERO_POINT    (-128)

static const char *const day16_time_frequency_labels[3] = {
  "idle", "walk", "stairs"
};

static const float day16_time_frequency_clip_low[56] = {
  2.695522960e-03f, 1.098801241e-03f, 3.017575890e-03f, 0.000000000e+00f, 5.271455999e-03f, 4.328295141e-03f,
  2.695522960e-03f, 3.831183753e-04f, 4.259503286e-02f, 1.109894904e-02f, 9.506437101e-04f, -7.475260645e-03f,
  1.046940295e-04f, 1.653640730e-03f, -3.737036884e-02f, -3.000000026e-03f, 7.261384733e-04f, 1.591612007e-03f,
  2.589938995e-05f, 6.521140365e-04f, 4.013141495e-04f, 8.082014229e-04f, 0.000000000e+00f, 1.663730713e-03f,
  1.663730713e-03f, 6.521140365e-04f, 3.734025033e-04f, 1.269841343e-01f, 2.869182928e-03f, 1.180912426e-03f,
  3.093394157e-03f, 6.661733642e-05f, 5.821663113e-03f, 5.054274234e-03f, 2.869182928e-03f, 9.472985961e-04f,
  4.281354372e-06f, 6.498751713e-07f, 1.794519618e-05f, 4.471055195e-06f, 6.250000000e-01f, 8.848504889e-01f,
  1.967499858e-01f, 1.684661482e-02f, 5.192723267e-03f, 1.196584318e-02f, 1.311638835e-01f, 4.246834189e-02f,
  6.250000000e-01f, 2.710651612e+00f, 5.761263746e-01f, 9.382725414e-03f, 7.482232321e-03f, 1.863947990e+00f,
  4.586402097e-01f, 1.256027159e-02f
};

static const float day16_time_frequency_clip_high[56] = {
  1.019162610e-01f, 4.925252870e-02f, 1.088132608e-01f, 3.648287430e-02f, 2.069981843e-01f, 1.988175511e-01f,
  1.019162610e-01f, 1.850807913e-02f, 1.894640565e+00f, 1.600155232e+00f, 6.124252994e-02f, -1.591612007e-03f,
  7.498329505e-03f, 1.082771271e-02f, -2.000000095e-03f, -1.000000047e-03f, 3.503703699e-02f, 7.475260645e-03f,
  1.540858299e-03f, 2.502680326e-02f, 1.938645355e-02f, 2.952194586e-02f, 5.875249947e-03f, 1.314553469e-01f,
  1.308524311e-01f, 2.502680326e-02f, 1.089911163e-02f, 5.714285970e-01f, 1.185029596e-01f, 5.099847913e-02f,
  1.284386367e-01f, 3.690989491e-02f, 3.015856147e-01f, 2.783333659e-01f, 1.185029596e-01f, 2.878416330e-02f,
  8.921160316e-03f, 3.763953017e-03f, 7.546876952e-02f, 2.983076312e-02f, 4.018750000e+00f, 4.335589094e+00f,
  7.220413834e-01f, 9.675739980e-01f, 6.985351443e-01f, 8.653911722e-01f, 8.212573990e+01f, 9.886415023e-01f,
  1.776875000e+01f, 1.163573072e+01f, 9.232739568e-01f, 5.698264527e-01f, 5.214673078e-01f, 8.656709566e+00f,
  8.820399308e-01f, 7.099806619e-01f
};

static const float day16_time_frequency_mean[56] = {
  5.513226136e-02f, 2.596279826e-02f, 6.105754524e-02f, 9.225854325e-03f, 1.144573835e-01f, 1.052190574e-01f,
  5.513226136e-02f, 9.689249286e-03f, 5.754684434e-01f, 4.757806986e-01f, 2.560712953e-02f, -3.793730279e-03f,
  1.779576627e-03f, 4.229147069e-03f, -8.721551431e-03f, -1.563263484e-03f, 7.159096973e-03f, 3.793730279e-03f,
  5.075991381e-04f, 1.408569534e-02f, 8.358305170e-03f, 1.640538084e-02f, 1.641142377e-03f, 3.816054837e-02f,
  3.651435170e-02f, 1.408569534e-02f, 4.996616672e-03f, 2.721709288e-01f, 5.216133565e-02f, 2.353924826e-02f,
  5.735871094e-02f, 1.158084835e-02f, 1.146094291e-01f, 1.030102063e-01f, 5.216133565e-02f, 1.246188156e-02f,
  3.011583596e-03f, 1.300389895e-03f, 1.812222044e-02f, 6.558958297e-03f, 1.919206274e+00f, 2.529658030e+00f,
  5.279381134e-01f, 3.968512210e-01f, 2.150491456e-01f, 3.704262446e-01f, 5.799950908e+00f, 5.975234272e-01f,
  3.075099810e+00f, 5.396619659e+00f, 7.553858202e-01f, 1.758598757e-01f, 2.065588202e-01f, 4.276828469e+00f,
  6.975601077e-01f, 2.334302426e-01f
};

static const float day16_time_frequency_std[56] = {
  2.890917268e-02f, 1.399088865e-02f, 3.187160811e-02f, 6.904975562e-03f, 6.151427301e-02f, 5.752124805e-02f,
  2.890917268e-02f, 5.618494243e-03f, 4.611812440e-01f, 3.826309329e-01f, 1.550127320e-02f, 1.511920656e-03f,
  1.144116192e-03f, 1.816496598e-03f, 5.398646113e-03f, 6.123075052e-04f, 5.075222306e-03f, 1.511920656e-03f,
  2.829700856e-04f, 7.917543509e-03f, 4.782515086e-03f, 9.193537565e-03f, 1.360931706e-03f, 2.344887025e-02f,
  2.265817858e-02f, 7.917543509e-03f, 2.808508666e-03f, 9.334702474e-02f, 3.022643014e-02f, 1.367315706e-02f,
  3.298188654e-02f, 8.654399280e-03f, 6.596059573e-02f, 5.992155009e-02f, 3.022643014e-02f, 7.220979492e-03f,
  2.038959124e-03f, 9.235270457e-04f, 1.514744653e-02f, 6.042392428e-03f, 1.214169906e+00f, 7.965569023e-01f,
  1.050535416e-01f, 2.643267284e-01f, 1.520656404e-01f, 2.308585082e-01f, 1.173576176e+01f, 2.701792945e-01f,
  2.943612778e+00f, 1.946297087e+00f, 8.041557720e-02f, 1.161477395e-01f, 1.173368365e-01f, 1.223915298e+00f,
  8.046015964e-02f, 1.568160648e-01f
};

static inline int8_t day16_time_frequency_quantize_input(float value)
{
  float qf = value / DAY16_TIME_FREQUENCY_INPUT_SCALE
             + (float)DAY16_TIME_FREQUENCY_INPUT_ZERO_POINT;
  int32_t quantized = (int32_t)(qf + (qf >= 0.0f ? 0.5f : -0.5f));
  if (quantized > 127) quantized = 127;
  if (quantized < -128) quantized = -128;
  return (int8_t)quantized;
}

static inline float day16_time_frequency_dequantize_output(int8_t value)
{
  return ((float)value - (float)DAY16_TIME_FREQUENCY_OUTPUT_ZERO_POINT)
         * DAY16_TIME_FREQUENCY_OUTPUT_SCALE;
}

#endif
