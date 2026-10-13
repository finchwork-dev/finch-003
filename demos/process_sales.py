#!/usr/bin/env python3
"""process_sales.py - limpa CSV de vendas e gera resumo.

## Como rodar
    python process_sales.py --input sales.csv --output-dir ./out

## Dependências
Nenhuma além do Python 3.8+ (apenas biblioteca padrão).

## Exemplo
    printf 'date,product,quantity,unit_price,customer_email\n2026-01-02,Caneta,3,2.5,a@x.com\n' > sales.csv
    python process_sales.py --input sales.csv --output-dir ./out
Gera out/cleaned_sales.csv e out/summary.json.
"""
import argparse, csv, json, os, sys
from collections import Counter
from datetime import datetime

REQUIRED = ["date", "product", "quantity", "unit_price", "customer_email"]
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")


def parse_date(s):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def clean_row(row):
    """Retorna a linha limpa (dict) ou None se inválida."""
    vals = {k: (row.get(k) or "").strip() for k in REQUIRED}
    if any(v == "" for v in vals.values()):
        return None
    try:
        qty = float(vals["quantity"])
        price = float(vals["unit_price"])
    except ValueError:
        return None  # quantity/unit_price não numérico
    if qty <= 0 or price < 0:
        return None  # valores negativos/zero
    d = parse_date(vals["date"])
    if d is None:
        return None
    qty_out = int(qty) if qty.is_integer() else qty
    return {"date": d.isoformat(), "product": vals["product"], "quantity": qty_out,
            "unit_price": round(price, 2), "customer_email": vals["customer_email"].lower(),
            "total": round(qty * price, 2)}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Limpa CSV de vendas e gera resumo.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", required=True)
    a = ap.parse_args(argv)
    if not os.path.isfile(a.input):
        print(f"Erro: arquivo '{a.input}' não encontrado.")
        return 1
    with open(a.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = [h.strip() for h in (reader.fieldnames or [])]
        if not all(c in header for c in REQUIRED):
            print("Erro: o CSV precisa conter as colunas date, product, quantity, unit_price, customer_email.")
            return 1
        reader.fieldnames = header
        rows, dropped = [], 0
        for r in reader:
            c = clean_row(r)
            if c is None:
                dropped += 1
            else:
                rows.append(c)
    os.makedirs(a.output_dir, exist_ok=True)
    with open(os.path.join(a.output_dir, "cleaned_sales.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REQUIRED + ["total"])
        w.writeheader(); w.writerows(rows)
    total = round(sum(r["total"] for r in rows), 2)
    qty_by_product = Counter()
    for r in rows:
        qty_by_product[r["product"]] += r["quantity"]
    summary = {
        "total_vendas": total,
        "produto_mais_vendido": qty_by_product.most_common(1)[0][0] if rows else None,
        "ticket_medio": round(total / len(rows), 2) if rows else 0,
        "clientes_unicos": len({r["customer_email"] for r in rows}),
    }
    with open(os.path.join(a.output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"{len(rows) + dropped} linhas processadas, {len(rows)} válidas, {dropped} descartadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
