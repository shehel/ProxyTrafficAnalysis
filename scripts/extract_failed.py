import re

log_text = """
VAL MISSING:
- Source file not found: ../ProxyData/local_pcaps/mixed_02_01_2025_06_08_10_low

- Source file not found: ../ProxyData/local_pcaps/mixed_03_01_2025_13_59_38_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_01_01_2025_04_30_20_low

- Source file not found: ../ProxyData/local_pcaps/mixed_27_12_2024_17_48_05_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_29_12_2024_03_36_31_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_31_12_2024_09_16_08_low

- Source file not found: ../ProxyData/local_pcaps/mixed_05_01_2025_05_06_52_medium
 
TRAIN MISSING:
Source file not found: ../ProxyData/local_pcaps/mixed_31_12_2024_04_59_41_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_05_01_2025_08_58_05_low

- Source file not found: ../ProxyData/local_pcaps/mixed_03_01_2025_15_45_57_high

- Source file not found: ../ProxyData/local_pcaps/mixed_25_12_2024_19_43_12_high

- Source file not found: ../ProxyData/local_pcaps/mixed_05_01_2025_02_54_54_low

- Source file not found: ../ProxyData/local_pcaps/mixed_27_12_2024_19_34_41_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_29_12_2024_13_32_22_low

- Source file not found: ../ProxyData/local_pcaps/mixed_27_12_2024_01_45_20_high

- Source file not found: ../ProxyData/local_pcaps/mixed_05_01_2025_01_04_28_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_02_01_2025_06_09_38_low

- Source file not found: ../ProxyData/local_pcaps/mixed_01_01_2025_10_54_44_low

- Source file not found: ../ProxyData/local_pcaps/mixed_31_12_2024_06_12_23_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_04_01_2025_02_50_14_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_31_12_2024_13_53_34_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_26_12_2024_09_50_07_medium
 
TEST MISSING:
- Source file not found: ../ProxyData/local_pcaps/mixed_03_01_2025_17_53_58_low

- Source file not found: ../ProxyData/local_pcaps/mixed_01_01_2025_17_44_52_low

- Source file not found: ../ProxyData/local_pcaps/mixed_02_01_2025_04_49_19_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_29_12_2024_22_05_16_medium

- Source file not found: ../ProxyData/local_pcaps/mixed_29_12_2024_11_24_11_high

- Source file not found: ../ProxyData/local_pcaps/mixed_29_12_2024_09_16_06_medium
"""

folder_list = re.findall(r"mixed_\d{2}_\d{2}_\d{4}_\d{2}_\d{2}_\d{2}_(?:low|medium|high)", log_text)

print(folder_list)

