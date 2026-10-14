# Informações consolidadas Sobre a Rota

**Analista Isaac · Região Duque de Caxias**

App web em que o motorista digita o próprio ID e vê:

- **Rota:** rota, tag, ajudante, quantidade de lojas (códigos), quantidade de agências a serem fechadas, KM da rota, pedágio, horário de início e horário de finalização da rota. Vem da aba *Informações Consolidadas da Rota*.
- **Agências:** PUP ID, horário de fechamento, sequência, horário de chegada, horário de saída, nome do ponto e endereço. Vem da aba *Fechamento de Agencia*.

## Privacidade
O `data.json` não guarda nenhum ID nem dado em texto aberto. Os dados de cada motorista ficam criptografados com AES-256-GCM, e a chave vem do próprio ID (PBKDF2-SHA256, 200.000 iterações). A página só abre os dados de quem digitar o ID correto.

## Como atualizar os dados
1. Exporte a planilha "Horários" em `.xlsx`.
2. `pip install openpyxl cryptography`
3. `python tools/build_data.py Horarios.xlsx data.json`
4. Faça commit do novo `data.json`. O GitHub Pages publica sozinho.
