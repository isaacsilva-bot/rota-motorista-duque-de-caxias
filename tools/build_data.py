"""Gera data.json (criptografado por ID) a partir da planilha exportada em .xlsx.

Uso:  python tools/build_data.py Horarios.xlsx
Requer: pip install openpyxl cryptography
Cada motorista só consegue abrir os próprios dados digitando o ID:
o ID é derivado com PBKDF2-SHA256 (200.000 iterações) em uma etiqueta de busca
e em uma chave AES-256-GCM. Nenhum ID ou dado aparece em texto aberto no arquivo.
"""
import sys, json, os, base64, datetime, hashlib, re
import openpyxl
from zoneinfo import ZoneInfo
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ITER = 200_000

def norm_id(v):
    if v is None: return ""
    if isinstance(v, (datetime.datetime, datetime.date)): return f"{v.day}/{v.month}"
    if isinstance(v, float) and v.is_integer(): v = int(v)
    s = str(v).strip()
    if re.fullmatch(r"\d+\.0", s): s = s[:-2]
    return s

def fmt(v, kind=None):
    if v is None: return ""
    if isinstance(v, datetime.time): return v.strftime("%H:%M")
    if isinstance(v, datetime.datetime): return v.strftime("%H:%M")
    if isinstance(v, float):
        if v.is_integer(): return str(int(v))
        return f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return str(v).strip()

def sheet(wb, prefix):
    for ws in wb.worksheets:
        if ws.title.lower().startswith(prefix.lower()): return ws
    raise SystemExit(f"Aba não encontrada: {prefix}")

def rows(ws):
    it = ws.iter_rows(values_only=True)
    head = [str(h).strip() if h is not None else "" for h in next(it)]
    for r in it:
        d = {head[i]: r[i] for i in range(min(len(head), len(r))) if head[i]}
        if norm_id(d.get("ID do Motorista")): yield d

def derive(id_, salt):
    raw = hashlib.pbkdf2_hmac("sha256", id_.encode(), salt, ITER, dklen=64)
    return raw[:32].hex(), raw[32:]

def main(path, out):
    wb = openpyxl.load_workbook(path, data_only=True)
    drivers = {}
    for d in rows(sheet(wb, "Informações Consolidadas")):
        i = norm_id(d["ID do Motorista"])
        drivers.setdefault(i, {"rota": None, "pontos": []})["rota"] = {
            "ROTA": fmt(d.get("ROTA")), "TAG": fmt(d.get("TAG")),
            "AJUDANTE": fmt(d.get("AJUDANTE")),
            "LOJAS": fmt(d.get("Quantidade de lojas (códigos)")),
            "AGENCIAS": fmt(d.get("Quantidade de Agencias a Serem fechadas")),
            "KM": fmt(d.get("KM DA ROTA")), "PEDAGIO": fmt(d.get("PEDÁGIO")),
            "INICIO": fmt(d.get("Horário de Início")),
            "FIM": fmt(d.get("Horário de Finalização da rota")),
        }
    for d in rows(sheet(wb, "Fechamento de Agencia")):
        i = norm_id(d["ID do Motorista"])
        drivers.setdefault(i, {"rota": None, "pontos": []})["pontos"].append({
            "PUP": fmt(d.get("PUP ID")), "FECH": fmt(d.get("Horário de fechamento")),
            "SEQ": fmt(d.get("Sequencia")), "CHEG": fmt(d.get("Horário de chegada")),
            "SAIDA": fmt(d.get("Horário de saída")), "NOME": fmt(d.get("NOME DO PONTO")),
            "END": fmt(d.get("Endereço")),
        })
    for v in drivers.values():
        v["pontos"].sort(key=lambda p: (p["CHEG"] or "99:99", p["SEQ"]))
    salt = os.urandom(16)
    recs = {}
    for i, v in drivers.items():
        tag, key = derive(i, salt)
        iv = os.urandom(12)
        ct = AESGCM(key).encrypt(iv, json.dumps(v, ensure_ascii=False).encode(), None)
        recs[tag] = base64.b64encode(iv + ct).decode()
    recs = dict(sorted(recs.items()))
    data = {"v": 1, "iter": ITER, "salt": base64.b64encode(salt).decode(),
            "atualizado": datetime.datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M"), "r": recs}
    json.dump(data, open(out, "w"), ensure_ascii=False)
    print(f"{len(recs)} motoristas -> {out}")
    return drivers

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data.json")
