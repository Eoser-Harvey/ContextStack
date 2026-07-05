"""
Extract key SNPs from Han Wei's WeGene TXT data for deep analysis.
"""
import re
from pathlib import Path

TXT_PATH = r"E:\Personal Files\0.家庭健康\伟 基因检测\韩伟.txt"
OUT_DIR = Path(r"e:\ProjectGroup\AI\ContextStack\01-Projects\family-hub\family-health")

# Key SNPs to extract - organized by category
KEY_SNPS = {
    # 叶酸/同型半胱氨酸通路
    "MTHFR_C677T": "rs1801133",
    "MTHFR_A1298C": "rs1801131",
    "MTRR": "rs1801394",
    "MTR": "rs1805087",
    "MTHFD1_R653Q": "rs1950902",
    "MTHFD1_R134K": "rs2236225",
    "TCN2": "rs1801198",
    "CBS": "rs234706",
    "BHMT": "rs651852",
    
    # 凝血/血栓
    "PAI1_SERPINE1": "rs1799889",
    "F5_Leiden": "rs6025",
    "F2_Prothrombin": "rs1799963",
    
    # 药物代谢
    "CYP2C19": "rs4244285",
    "CYP2D6": "rs1065852",
    "CYP2C9_2": "rs1799853",
    "CYP2C9_3": "rs1057910",
    "CYP3A5": "rs776746",
    "CYP4F2": "rs2108622",
    "NAT2": "rs1801280",
    "UGT1A1": "rs4148323",
    "SLCO1B1": "rs4149056",
    "TPMT": "rs1142345",
    "NUDT15": "rs116855232",
    "DPYD": "rs3918290",
    "G6PD": "rs1050829",
    "VKORC1": "rs9923231",
    
    # 心血管/代谢
    "APOE_e2": "rs429358",
    "APOE_e4": "rs7412",
    "LPA": "rs3798220",
    "FTO": "rs9939609",
    "APOA2": "rs5082",
    
    # 酒精代谢
    "ALDH2": "rs671",
    "ADH1B": "rs1229984",
    "ADH1B_2": "rs2066702",
    
    # 乳糖代谢
    "MCM6_1": "rs182549",
    "MCM6_2": "rs4988235",
    
    # 铁代谢
    "HFE_H63D": "rs1799945",
    "HFE_C282Y": "rs1800562",
    
    # 炎症/免疫
    "TNF": "rs1800629",
    "IL6": "rs1800795",
    "PEMT": "rs7946",
    "VDR_FokI": "rs2228576",
    "GSTP1": "rs1695",
    "PON1": "rs662",
    "COMT": "rs4680",
    "BDNF": "rs6265",
    
    # 男性特有
    "AR": "rs6152",  # 雄激素受体
    "SRD5A2": "rs523349",  # 5α-还原酶
}

# Build index
print("Building SNP index from TXT...")
snp_index = {}
with open(TXT_PATH, "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("#"):
            continue
        parts = line.strip().split("\t")
        if len(parts) >= 4:
            snp_index[parts[0]] = parts[3]

# Look up
print("\nKey SNP Results:")
results = []
for name, rsid in KEY_SNPS.items():
    gt = snp_index.get(rsid, "NOT_FOUND")
    results.append(f"{name:20s} {rsid:15s} {gt}")
    print(f"  {name:20s} {rsid:15s} {gt}")

# Save results
out_file = OUT_DIR / "_hanwei_snp_key.txt"
with open(out_file, "w", encoding="utf-8") as f:
    f.write("# 韩伟 关键SNP位点基因型\n")
    f.write(f"# 总计查找: {len(KEY_SNPS)} 个位点\n\n")
    for line in results:
        f.write(line + "\n")

print(f"\nSaved to: {out_file}")

# Also look for specific male-related and fertility-related SNPs
print("\n\n=== Additional Male Health SNPs ===")
MALE_SNPS = {
    "SHBG": "rs6259",
    "SHBG_2": "rs727428",
    "FSHR": "rs6166",
    "LHCGR": "rs2293275",
    "ESR1": "rs2234693",
    "ESR1_2": "rs9340799",
    "CYP19A1": "rs2414096",
    "NR5A1": "rs11100614",
    "DAZL": "rs2303428",
    "PRM1": "rs35576928",
    "CATSPER1": "rs2845570",
    "DNAH1": "rs121918506",
}

for name, rsid in MALE_SNPS.items():
    gt = snp_index.get(rsid, "NOT_FOUND")
    print(f"  {name:20s} {rsid:15s} {gt}")

# Kidney-related SNPs
print("\n\n=== Kidney/Gout SNPs ===")
KIDNEY_SNPS = {
    "SLC2A9": "rs16890979",
    "ABCG2": "rs2231142",
    "SLC22A12": "rs11231825",
    "UMOD": "rs4293393",
    "SHROOM3": "rs17319721",
}
for name, rsid in KIDNEY_SNPS.items():
    gt = snp_index.get(rsid, "NOT_FOUND")
    print(f"  {name:20s} {rsid:15s} {gt}")

# Autoimmune SNPs
print("\n\n=== Autoimmune SNPs ===")
AUTO_SNPS = {
    "NOD2_R702W": "rs2066844",
    "NOD2_G908R": "rs2066845",
    "NOD2_1007fs": "rs2066847",
    "ATG16L1": "rs2241880",
    "IRGM": "rs13361189",
    "IL23R": "rs11209026",
    "STAT4": "rs7574865",
    "PTPN22": "rs2476601",
    "CTLA4": "rs231775",
    "HLA_DQA1": "rs2187668",
}
for name, rsid in AUTO_SNPS.items():
    gt = snp_index.get(rsid, "NOT_FOUND")
    print(f"  {name:20s} {rsid:15s} {gt}")

print(f"\nTotal SNPs indexed: {len(snp_index)}")