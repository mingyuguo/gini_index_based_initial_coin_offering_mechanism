import csv

# -9 budget_ether -8 budget_usd  -2 market_cup ther -1 marketcap_usd_million
# -4 token_price_ether -3 token_price_usd
# may not be all consistent with this format
def import_csv(csvfilename="Merged_data/_raiden_Merged.csv"):
    vs = []
    bs = []
    with open(csvfilename, "r", encoding="utf-8", errors="ignore") as scraped:
        reader = csv.reader(scraped, delimiter=",")
        row_index = 0
        for row in reader:
            if row:  # avoid blank lines
                row_index += 1
                if row_index != 1:
                    vs.append(float(row[-4]))
                    if "Gnosis" in csvfilename:
                        bs.append(float(row[-7]))
                    else:
                        bs.append(float(row[-9]))
    return vs, bs
